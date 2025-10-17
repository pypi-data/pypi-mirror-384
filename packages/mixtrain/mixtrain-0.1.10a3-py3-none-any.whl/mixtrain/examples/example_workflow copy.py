"""Example workflow demonstrating mixflow_param usage."""

from mixtrain import MixFlow, mixflow_param


class ExampleWorkflow(MixFlow):
    """Example workflow with configurable parameters."""

    # Parameter with type, default, and description
    learning_rate: float = mixflow_param(
        default=0.001, description="Learning rate for training"
    )

    # Parameter with just type and description
    model_name: str = mixflow_param(description="Name of the model to use for training")

    # Parameter with just default value
    batch_size: int = mixflow_param(default=32)

    # Parameter with integer type
    epochs: int = mixflow_param(default=10, description="Number of training epochs")

    # Boolean parameter
    use_gpu: bool = mixflow_param(
        default=True, description="Whether to use GPU acceleration"
    )

    def setup(self):
        """Initialize the workflow."""
        print("Setting up workflow...")

    def run(self):
        """Execute the workflow."""
        print("\nRunning workflow...")
        print(f"Training {self.model_name} for {self.epochs} epochs")
        print(f"Using batch size: {self.batch_size}")
        print(f"Learning rate: {self.learning_rate}")
        print(f"GPU acceleration: {'enabled' if self.use_gpu else 'disabled'}")

        # Your actual workflow logic here
        # For example: train model, process data, etc.

        print("\nWorkflow execution completed!")

    def cleanup(self):
        """Clean up resources."""
        print("Cleaning up workflow resources...")
