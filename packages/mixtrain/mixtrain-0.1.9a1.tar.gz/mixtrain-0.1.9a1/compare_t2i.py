import subprocess
import sys
import os
from typing import Any, Optional


import tempfile
from mixtrain import MixClient, MixFlow

import time


def mix_param(default_value: Any):
    pass


# def install_package(packages):
#     """Installs a given Python package using pip."""
#     try:
#         subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])
#         print(f"Successfully installed {packages}")
#     except subprocess.CalledProcessError as e:
#         print(f"Error installing {packages}: {e}")


# Example usage:
# install_package(["fal_client"])

# import fal_client
import pandas as pd

mix = MixClient()


class MixModel:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def run(self, args: dict):
        pass

    def submit(self, args: dict):
        raise NotImplementedError("Submitting is not supported for this model")


class ModalModel(MixModel):
    def __init__(self, model_name: str):
        super().__init__(model_name)


class FalModel(MixModel):
    def __init__(self, model_name: str):
        import fal_client

        super().__init__(model_name)
        self.fal_key_updated = False
        self.setup()

    def setup(self):
        import fal_client

        if "FAL_KEY" not in os.environ and not self.fal_key_updated:
            self.fal_key_updated = True
            os.environ["FAL_KEY"] = mix.get_secret("FAL_KEY")

    def cleanup(self):
        if "FAL_KEY" in os.environ and self.fal_key_updated:
            os.environ.pop("FAL_KEY")

    def __del__(self):
        self.cleanup()

    def run(self, args: dict):
        import fal_client

        request_id = self.submit(args)
        return self.wait_for_completion(request_id)

    def wait_for_completion(self, request_id: str):
        import fal_client

        while True:
            status = fal_client.status(self.model_name, request_id)
            if isinstance(status, fal_client.Completed):
                result = fal_client.result(self.model_name, (request_id))
                return result
            else:
                time.sleep(1)

    def get_status(self, request_id: str):
        import fal_client

        return fal_client.status(self.model_name, request_id)

    def submit(self, args: dict):
        import fal_client

        handler = fal_client.submit(
            self.model_name,
            arguments=args,
        )

        request_id = handler.request_id
        return request_id


def run_batch(model_name_to_args_list: dict[str, list[dict]]) -> dict[str, list[Any]]:
    """Submit all requests, then poll only pending ones until completion.

    Preserves per-model ordering of results.
    """
    # Submit all requests and keep stable ordering per model
    import fal_client

    model_to_request_ids: dict[str, list[str]] = {}
    for model_name, args_list in model_name_to_args_list.items():
        model: MixModel = get_model(model_name)
        request_ids: list[str] = []
        for args in args_list:
            request_ids.append(model.submit(args))
        model_to_request_ids[model_name] = request_ids

    # Pre-allocate result slots and pending indices per model
    model_to_results: dict[str, list[Optional[Any]]] = {
        model_name: [None] * len(request_ids)
        for model_name, request_ids in model_to_request_ids.items()
    }
    model_to_pending_indices: dict[str, set[int]] = {
        model_name: set(range(len(request_ids)))
        for model_name, request_ids in model_to_request_ids.items()
    }
    # Per-request scheduling to avoid re-polling too frequently
    min_backoff: float = 0.2
    max_backoff: float = 2.0
    model_to_next_check: dict[str, dict[int, float]] = {
        model_name: {idx: 0.0 for idx in pending}
        for model_name, pending in model_to_pending_indices.items()
    }
    model_to_backoff: dict[str, dict[int, float]] = {
        model_name: {idx: min_backoff for idx in pending}
        for model_name, pending in model_to_pending_indices.items()
    }

    # Poll until all pending are completed
    while any(len(pending) > 0 for pending in model_to_pending_indices.values()):
        now = time.monotonic()
        any_completed_this_cycle = False
        any_checked_this_cycle = False

        for model_name, request_ids in model_to_request_ids.items():
            pending_indices = model_to_pending_indices[model_name]
            if not pending_indices:
                continue

            model: MixModel = get_model(model_name)
            next_check_map = model_to_next_check[model_name]
            backoff_map = model_to_backoff[model_name]

            # Iterate over a snapshot since we'll mutate the set
            for idx in list(pending_indices):
                if next_check_map.get(idx, 0.0) > now:
                    continue  # not due yet

                any_checked_this_cycle = True
                request_id = request_ids[idx]

                # Efficient path when model exposes get_status
                if hasattr(model, "get_status"):
                    status = getattr(model, "get_status")(request_id)
                    if isinstance(status, fal_client.Completed):
                        result = fal_client.result(model_name, request_id)
                        model_to_results[model_name][idx] = result
                        pending_indices.remove(idx)
                        next_check_map.pop(idx, None)
                        backoff_map.pop(idx, None)
                        any_completed_this_cycle = True
                        continue
                else:
                    # Fallback: blockingly wait for each remaining request
                    result = model.wait_for_completion(request_id)
                    model_to_results[model_name][idx] = result
                    pending_indices.remove(idx)
                    next_check_map.pop(idx, None)
                    backoff_map.pop(idx, None)
                    any_completed_this_cycle = True
                    continue

                # Not completed yet: schedule next check with per-request backoff
                new_backoff = min(backoff_map.get(idx, min_backoff) * 1.5, max_backoff)
                backoff_map[idx] = new_backoff
                next_check_map[idx] = now + new_backoff

        if not any_completed_this_cycle and not any_checked_this_cycle:
            # Sleep until the earliest next check across all requests
            next_times: list[float] = []
            for per_model in model_to_next_check.values():
                next_times.extend(per_model.values())
            if next_times:
                sleep_for = max(0.05, min(t - now for t in next_times if t > now))
                time.sleep(sleep_for)
            else:
                # Fallback minimal sleep to avoid busy loop
                time.sleep(0.1)

    # Cast away Optional for the return type
    finalized: dict[str, list[Any]] = {
        model_name: [r for r in results if r is not None]
        for model_name, results in model_to_results.items()
    }
    return finalized


def get_model(model_name: str) -> MixModel:
    if model_name.startswith("fal-ai/"):  # TODO: handle private models
        return FalModel(model_name)
    elif model_name.startswith("modal/"):
        return ModalModel(model_name)
    else:
        raise ValueError(f"Model {model_name} not supported")


class T2IEvaluation(MixFlow):
    """T2I (Text to Image) evaluation workflow

    Args:
        limit: Number of prompts to evaluate
        model_names: List of model names to evaluate
        input_dataset_name: Name of the input dataset
        output_dataset_name: Name of the output dataset
        evaluation_name: Name of the evaluation to create
    """

    limit = mixflow_param(default=10)
    model_names = mixflow_param(
        default=["fal-ai/hunyuan-image/v3/text-to-image", "fal-ai/qwen-image"]
    )

    input_dataset_name = mixflow_param(default="t2i_100")
    output_dataset_name = mixflow_param()
    evaluation_name = mixflow_param()

    def __init__(self):
        super().__init__()

    def setup(self):
        import fal_client

    def evaluate_prompt(self, prompt, model_name: str):
        results = get_model(model_name).run({"prompt": prompt})
        return results["images"][0]["url"]

    def run(self):
        input_dataset = mix.get_dataset(self.input_dataset_name)
        prompts = input_dataset.scan().to_pandas()["prompt"][: self.limit].tolist()
        df = pd.DataFrame({"prompt": prompts})
        santized_model_names = [
            m.replace("fal-ai/", "").replace("/", "_").replace("-", "_")
            for m in self.model_names
        ]

        # Submit all requests for all models and prompts, then wait
        model_name_to_args_list = {
            model_name: [{"prompt": p} for p in prompts]
            for model_name in self.model_names
        }
        batch_results = run_batch(model_name_to_args_list)

        # Map results to first image URL per result, preserving prompt order
        model_to_urls: dict[str, list[str]] = {}
        for model_name, results in batch_results.items():
            urls: list[str] = []
            for result in results:
                urls.append(result["images"][0]["url"])  # type: ignore[index]
            model_to_urls[model_name] = urls

        # Fill DataFrame columns with sanitized model names
        for model_name, sanitized in zip(self.model_names, santized_model_names):
            df[sanitized] = model_to_urls[model_name]

        # Create output dataset from results
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            df.to_csv(f.name, index=False)
            # mix.delete_dataset(output_dataset_name)
            mix.create_dataset_from_file(self.output_dataset_name, f.name)

        viz_config = {
            "datasets": [
                {
                    "columnName": "prompt",
                    "tableName": self.output_dataset_name,
                    "dataType": "text",
                },
            ]
        }
        # Add model columns to viz_config
        for model_name in santized_model_names:
            viz_config["datasets"].append(
                {
                    "columnName": model_name,
                    "tableName": self.output_dataset_name,
                    "dataType": "link-image",
                }
            )
        mix.create_evaluation(self.evaluation_name, viz_config)


# T2IEvaluation(input_dataset_name, evaluation_name, model_names).run()
