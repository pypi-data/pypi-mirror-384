"""Generate embeddings for a mixtrain dataset and append as a column."""

import subprocess
import sys
from typing import Any

from mixtrain import MixClient, MixFlow, mixflow_param


def install_package(packages):
    """Installs a given Python package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])
        print(f"Successfully installed {packages}")
    except subprocess.CalledProcessError as e:
        print(f"Error installing {packages}: {e}")


mix = MixClient()


class GenerateEmbeddings(MixFlow):
    """Generate embeddings for text data in a dataset and append as columns.

    This workflow reads text data from a dataset, generates embeddings
    using a specified model, creates 2D projections for visualization,
    and overwrites the dataset with the new columns added.

    Args:
        dataset_name: Name of the dataset to add embeddings to (Apache Iceberg)
        text_column: Name of the column containing text to embed
        embedding_column: Name of the column to store embeddings (default: "embedding")
        embedding_model: Model to use for embeddings (default: "openai")
        model_name: Specific model name (e.g., "text-embedding-3-small" for OpenAI)
        batch_size: Number of texts to process at once (default: 100)
        limit: Maximum number of rows to process (None for all)
        generate_2d_projection: Generate x,y coordinates for visualization (default: True)
        projection_method: Projection method: 'tsne' or 'umap' (default: "tsne")
    """

    dataset_name: str = mixflow_param(description="Dataset to add embeddings to")
    text_column: str = mixflow_param(
        default="text", description="Column name containing text to embed"
    )
    embedding_column: str = mixflow_param(
        default="embedding", description="Column name to store embeddings"
    )
    embedding_model: str = mixflow_param(
        default="openai",
        description="Embedding model provider (openai, sentence-transformers)",
    )
    model_name: str = mixflow_param(
        default="text-embedding-3-small", description="Specific model name to use"
    )
    batch_size: int = mixflow_param(
        default=100, description="Batch size for processing"
    )
    limit: int = mixflow_param(
        default=None, description="Maximum number of rows to process (None for all)"
    )
    generate_2d_projection: bool = mixflow_param(
        default=True, description="Generate 2D projection for visualization"
    )
    projection_method: str = mixflow_param(
        default="tsne", description="Projection method: 'tsne' or 'umap'"
    )

    def __init__(self):
        super().__init__()
        self.embedding_client = None

    def setup(self, run_config: dict[str, Any]):
        """Initialize the workflow with configuration."""
        print(f"Setting up embedding generation workflow...")
        print(f"Run config: {run_config}")

        for key, value in run_config.items():
            setattr(self, key, value)

        # Base packages
        packages_to_install = ["pyarrow"]  # noqa: RUF012

        # Install required packages based on embedding model
        if self.embedding_model == "openai":
            packages_to_install.append("openai")

        elif self.embedding_model == "sentence-transformers":
            packages_to_install.extend(["sentence-transformers", "torch"])
        else:
            raise ValueError(f"Unsupported embedding model: {self.embedding_model}")

        # Add dimensionality reduction dependencies if needed
        if self.generate_2d_projection:
            if self.projection_method == "tsne":
                packages_to_install.append("scikit-learn")
            elif self.projection_method == "umap":
                packages_to_install.append("umap-learn")
            else:
                raise ValueError(
                    f"Unsupported projection method: {self.projection_method}"
                )

        install_package(packages_to_install)

        # Initialize embedding client after installation
        if self.embedding_model == "openai":
            import openai  # type: ignore

            # Get API key from mixtrain secrets
            api_key = mix.get_secret("OPENAI_API_KEY")
            self.embedding_client = openai.OpenAI(api_key=api_key)
        elif self.embedding_model == "sentence-transformers":
            from sentence_transformers import SentenceTransformer  # type: ignore

            self.embedding_client = SentenceTransformer(self.model_name)

        print(f"Using {self.embedding_model} with model: {self.model_name}")

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        if self.embedding_model == "openai":
            response = self.embedding_client.embeddings.create(
                input=texts, model=self.model_name
            )
            return [item.embedding for item in response.data]

        elif self.embedding_model == "sentence-transformers":
            embeddings = self.embedding_client.encode(texts, show_progress_bar=False)
            return embeddings.tolist()

        else:
            raise ValueError(f"Unsupported embedding model: {self.embedding_model}")

    def run(self):
        """Execute the embedding generation workflow."""
        print(f"\n{'=' * 60}")
        print(f"Generating embeddings for dataset: {self.dataset_name}")
        print(f"Text column: {self.text_column}")
        print(f"Embedding column: {self.embedding_column}")
        print(f"{'=' * 60}\n")

        # Load input dataset
        print(f"Loading dataset: {self.dataset_name}")
        input_dataset = mix.get_dataset(self.dataset_name)
        df = input_dataset.scan().to_pandas()

        # Apply limit if specified
        if self.limit is not None:
            df = df.head(self.limit)

        print(f"Loaded {len(df)} rows")

        # Validate text column exists
        if self.text_column not in df.columns:
            raise ValueError(
                f"Text column '{self.text_column}' not found in dataset. "
                f"Available columns: {df.columns.tolist()}"
            )

        # Get texts to embed
        texts = df[self.text_column].astype(str).tolist()

        # Generate embeddings in batches
        all_embeddings = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size

        print(f"\nGenerating embeddings in {total_batches} batches...")
        for i in range(0, len(texts), self.batch_size):
            batch_num = i // self.batch_size + 1
            batch_texts = texts[i : i + self.batch_size]

            print(
                f"Processing batch {batch_num}/{total_batches} ({len(batch_texts)} texts)..."
            )
            batch_embeddings = self.generate_embeddings_batch(batch_texts)
            all_embeddings.extend(batch_embeddings)

        # Add embeddings to dataframe
        df[self.embedding_column] = all_embeddings

        print(f"\nGenerated {len(all_embeddings)} embeddings")
        print(f"Embedding dimension: {len(all_embeddings[0])}")

        # Generate 2D projection for visualization
        if self.generate_2d_projection:
            print(f"\nGenerating 2D projection using {self.projection_method}...")

            # Convert embeddings list to numpy array for dimensionality reduction
            import numpy as np  # type: ignore

            embeddings_array = np.array(all_embeddings)

            if self.projection_method == "tsne":
                from sklearn.manifold import TSNE  # type: ignore

                perplexity = (
                    min(30, len(all_embeddings) - 1) if len(all_embeddings) > 1 else 1
                )
                tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity)
                projections = tsne.fit_transform(embeddings_array)
            elif self.projection_method == "umap":
                import umap  # type: ignore

                reducer = umap.UMAP(n_components=2, random_state=42)
                projections = reducer.fit_transform(embeddings_array)
            else:
                raise ValueError(
                    f"Unsupported projection method: {self.projection_method}"
                )

            df[f"{self.embedding_column}_x"] = projections[:, 0]
            df[f"{self.embedding_column}_y"] = projections[:, 1]

            # Also create standard column names for frontend compatibility
            df["embedding_x"] = projections[:, 0]
            df["embedding_y"] = projections[:, 1]

            print(f"✓ Added x and y columns for visualization")
            print(f"  - {self.embedding_column}_x and {self.embedding_column}_y")
            print(f"  - embedding_x and embedding_y (standard names)")

        # Convert to PyArrow table and update the dataset
        import pyarrow as pa  # type: ignore

        arrow_table = pa.Table.from_pandas(df)

        print(f"\nUpdating dataset: {self.dataset_name}")
        input_table = mix.get_dataset(self.dataset_name)

        # Get the new schema that includes our added columns
        new_schema = arrow_table.schema

        # Evolve the Iceberg schema to add new columns
        # Use union_by_name to merge schemas
        print("Evolving table schema to add new columns...")
        try:
            # Update schema using PyIceberg's schema evolution
            from pyiceberg.types import (  # type: ignore
                DoubleType,
                ListType,
                NestedField,
            )

            with input_table.update_schema() as update:
                # Add embedding column (list of doubles)
                if self.embedding_column not in [
                    field.name for field in input_table.schema().fields
                ]:
                    update.add_column(
                        self.embedding_column,
                        ListType(
                            element_id=1,
                            element_type=DoubleType(),
                            element_required=False,
                        ),
                        doc="Generated embeddings",
                    )

                # Add x and y columns if projection was generated
                if self.generate_2d_projection:
                    # Add custom-named columns
                    x_col = f"{self.embedding_column}_x"
                    y_col = f"{self.embedding_column}_y"

                    if x_col not in [
                        field.name for field in input_table.schema().fields
                    ]:
                        update.add_column(
                            x_col, DoubleType(), doc="X coordinate for visualization"
                        )

                    if y_col not in [
                        field.name for field in input_table.schema().fields
                    ]:
                        update.add_column(
                            y_col, DoubleType(), doc="Y coordinate for visualization"
                        )

                    # Add standard column names for frontend compatibility
                    if "embedding_x" not in [
                        field.name for field in input_table.schema().fields
                    ]:
                        update.add_column(
                            "embedding_x",
                            DoubleType(),
                            doc="X coordinate (standard name)",
                        )

                    if "embedding_y" not in [
                        field.name for field in input_table.schema().fields
                    ]:
                        update.add_column(
                            "embedding_y",
                            DoubleType(),
                            doc="Y coordinate (standard name)",
                        )

            print("✓ Schema updated successfully")

            # Now overwrite with the new data
            input_table.overwrite(arrow_table)

        except Exception as e:
            print(f"Warning: Could not use schema evolution: {e}")
            print("Attempting alternative approach: appending to table...")
            # Alternative: use append which is more lenient with new columns
            input_table.append(arrow_table)

        print(f"\n{'=' * 60}")
        print(f"✓ Successfully added embeddings to {self.dataset_name}!")
        print(f"✓ New columns:")
        print(f"  - {self.embedding_column} (embeddings)")
        if self.generate_2d_projection:
            print(
                f"  - {self.embedding_column}_x, {self.embedding_column}_y (custom names)"
            )
            print(f"  - embedding_x, embedding_y (standard names for visualization)")
        print(f"✓ Total rows: {len(df)}")
        print(f"{'=' * 60}\n")

    def cleanup(self):
        """Clean up resources."""
        print("Cleaning up workflow resources...")
        self.embedding_client = None


# Example usage:
# To run this workflow:
# 1. Ensure you have a dataset with text data
# 2. Set OPENAI_API_KEY secret in mixtrain (for OpenAI embeddings)
# 3. Run the workflow with appropriate parameters
#
# Example:
# workflow = GenerateEmbeddings()
# workflow.setup({
#     "dataset_name": "my_text_dataset",
#     "text_column": "text",
#     "embedding_model": "openai",
#     "model_name": "text-embedding-3-small",
#     "generate_2d_projection": True,
#     "projection_method": "tsne",
#     "limit": 100
# })
# workflow.run()
# workflow.cleanup()
