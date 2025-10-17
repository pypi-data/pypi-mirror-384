from enum import Enum

import modal
import typer
from rich import print as rprint
from rich.table import Table

from .client import call_api, list_model_providers, list_models

app = typer.Typer(help="Manage training jobs.", invoke_without_command=True)

@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def start():
    """
    Start a training job.
    """
    call_api("POST", "/training/start")


@app.command()
def status():
    """
    Get training status.
    """
    call_api("GET", "/training/status")

class Framework(str, Enum):
    oxen = "oxen"
    pytorch = "pytorch"
    tensorflow = "tensorflow"
    axolotl = "axolotl"

@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run(ctx: typer.Context,
        path: str = typer.Option(".", help="The path to the training data."),
        gpu: str = typer.Option("T4", help="The GPU to use."),
        framework: Framework = typer.Option(None, help="The framework to use."),
        extra_libs: list[str] = typer.Option([], help="Extra libraries to install."),
        ):
    """
    Run a training job.
    """
    print(f"Using GPU: {gpu}")
    for arg in ctx.args:
        typer.echo(f"- {arg}")


    app = modal.App.lookup("train-app",create_if_missing=True)
    if framework == Framework.axolotl:

        image = modal.Image.from_registry("axolotlai/axolotl-cloud:main-20250701-py3.11-cu124-2.6.0").pip_install(extra_libs).env({
            "JUPYTER_DISABLE": "1",
        })

    with modal.enable_output():
        sandbox = modal.Sandbox.create(image=image, gpu=gpu, app=app, timeout=600, verbose=True) # you can pass cmd here as well
        print(sandbox.object_id)
        p = sandbox.exec("python", "-c", "import torch; print(torch.cuda.get_device_name())")
        for line in p.stdout:
            print(line, end="")
        # print(p.stdout.read())
        # print(p.stderr.read())

        p = sandbox.exec("python", "-c", "import duckdb; print(duckdb.__version__)")
        # for line in p.stdout:
        #     print(line, end="")
        print(p.stdout.read())
        print(p.stderr.read())

        sandbox.terminate()


@app.command(name="models")
def list_training_models():
    """List available models for training from configured model providers."""
    try:
        # Check if any model providers are configured
        model_data = list_model_providers()
        model_onboarded = model_data.get("onboarded_providers", [])
        
        if not model_onboarded:
            rprint("[yellow]No model providers configured.[/yellow]")
            rprint("Configure a model provider first using 'mixtrain provider add <type>'.")
            rprint("Available model providers:")
            model_available = model_data.get("available_providers", [])
            for provider in model_available:
                rprint(f"  - {provider.get('provider_type')}: {provider.get('display_name')}")
            return

        # List available models
        models = list_models()
        
        if not models:
            rprint("[yellow]No models available for training.[/yellow]")
            rprint("Deploy models to your configured model providers first.")
            return

        rprint("[bold]Available Models for Training:[/bold]")
        table = Table("Name", "Provider", "URL")
        for model in models:
            table.add_row(
                model.get("name", ""),
                model.get("provider_name", ""),
                model.get("url", ""),
            )
        rprint(table)

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)
