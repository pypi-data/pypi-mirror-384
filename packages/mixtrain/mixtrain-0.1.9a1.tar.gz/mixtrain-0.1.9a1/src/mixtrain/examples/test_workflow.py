"""Test workflow file with MixFlow subclasses using mixflow_param()."""

from mixtrain import MixFlow, mixflow_param


class SimpleWorkflow(MixFlow):
    """A simple workflow with basic parameters."""

    # Parameters using mixflow_param()
    prompt = mixflow_param()
    limit: int = mixflow_param(default=10)
    model_name = mixflow_param(default="gpt-3.5-turbo", description="The model name")
    temperature: float = mixflow_param(default=0.7)
    custom_config = mixflow_param(default={"mode": "fast"})
    non_zero_default = "0"

    # Regular class attribute (should not be extracted)
    _internal_counter = 0

    def run(self):
        """Run the workflow."""
        print(f"Running with prompt: {self.prompt}")
        print(f"Model: {self.model_name}, Limit: {self.limit}")


class ImageGenerationWorkflow(MixFlow):
    """Image generation workflow with more complex parameters."""

    input_dataset: str = mixflow_param()
    output_dataset: str = mixflow_param()
    models: list[str] = mixflow_param(default=["flux-v1", "flux-v2"])
    batch_size: int = mixflow_param(default=32)
    evaluation_name: str = mixflow_param()
    max_retries: int = mixflow_param(default=3)
    timeout: float = mixflow_param(default=60.0)

    def setup(self):
        """Setup the workflow."""
        pass

    def run(self):
        """Run image generation."""
        pass


class DataProcessingWorkflow(MixFlow):
    """Data processing with optional parameters."""

    # Required parameters
    source_path: str = mixflow_param()
    destination_path: str = mixflow_param()

    # Optional parameters with defaults
    chunk_size: int = mixflow_param(default=1000)
    parallel_workers: int = mixflow_param(default=4)
    compression: bool = mixflow_param(default=False)

    # Parameters without type hints
    custom_config = mixflow_param(default={"mode": "fast"})

    def run(self):
        """Process data."""
        pass
