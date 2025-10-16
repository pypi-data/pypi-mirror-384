
import typer
from rich import print as rprint
from rich.table import Table

from .client import call_api, list_model_providers, list_models

app = typer.Typer(help="Manage evaluation jobs.", invoke_without_command=True)

@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def run(dataset_name: str, eval_func: str, dataset_version: str | None = None, limit: int | None = -1):
    """
    Start an evaluation job.
    """
    # call_api("POST", "/eval/start")
    print("Starting evaluation...")


@app.command()
def status():
    """
    Get evaluation status.
    """
    call_api("GET", "/eval/status")


@app.command(name="models")
def list_evaluation_models():
    """List available models for evaluation from configured model providers."""
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
            rprint("[yellow]No models available for evaluation.[/yellow]")
            rprint("Deploy models to your configured model providers first.")
            return

        rprint("[bold]Available Models for Evaluation:[/bold]")
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
