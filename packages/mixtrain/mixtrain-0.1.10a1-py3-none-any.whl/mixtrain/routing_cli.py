"""CLI commands for routing engine."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from .client import MixClient
from .routing import (
    ConfigBuilder,
    ConfigurationLinter,
    RoutingConfig,
    RoutingEngineFactory,
    RoutingStrategy,
    RoutingValidator,
    RoutingConfigValidationError,
)

app = typer.Typer(
    help="Routing engine commands",
    invoke_without_command=True,
)
console = Console()


@app.callback()
def routing_main(ctx: typer.Context):
    """Routing engine commands for configuration management and testing.

    Commands work with configuration IDs by default (from mixtrain platform) or local files with --config-file.
    Use 'mixtrain routing list-configs' to see available configurations and their IDs.
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command(name="list-configs")
def list_configs():
    """List all routing configurations in the workspace."""
    try:
        client = MixClient()
        configs = client.list_routing_configs()

        if not configs:
            rprint("[yellow]No routing configurations found.[/yellow]")
            rprint("Use 'mixtrain routing create-config <name>' to create one.")
            return

        # Show configurations
        table = Table(
            "ID", "Name", "Status", "Description", "Version", "Created", "Updated"
        )
        for config in configs:
            # Check if this config is active based on status field
            config_status = config.get("status", "").lower()
            is_active = config_status == "active"
            status = (
                "[green]Active[/green]"
                if is_active
                else f"[dim]{config_status.title() or 'Inactive'}[/dim]"
            )
            table.add_row(
                str(config.get("id", "")),
                config.get("name", ""),
                status,
                (config.get("description", "") or "")[:40]
                + ("..." if len(config.get("description", "") or "") > 40 else ""),
                str(config.get("version", "")),
                format_date(config.get("created_at", "")),
                format_date(config.get("updated_at", "")),
            )
        console.print(table)

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


def format_date(date_str: str) -> str:
    dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    local_dt = dt.astimezone()  # converts to system local timezone
    return local_dt.strftime("%Y-%m-%d %H:%M:%S")


@app.command()
def create(
    name: str = typer.Argument(help="Configuration name"),
    output: Optional[str] = typer.Option(
        None, "-o", "--output", help="Output file path"
    ),
    interactive: bool = typer.Option(
        False, "-i", "--interactive", help="Interactive configuration builder"
    ),
    from_json: Optional[str] = typer.Option(
        None, "--from-json", help="Create configuration from JSON file"
    ),
):
    """Create a new routing configuration.

    Can create from JSON file (--from-json), interactively (-i), or with basic prompts.
    """
    try:
        if from_json:
            # Load configuration from JSON file
            try:
                with open(from_json) as f:
                    json_data = json.load(f)

                # Use the name and description from the JSON file, but allow name override from CLI
                config_name = (
                    name if name else json_data.get("name", "Imported Configuration")
                )
                config_description = json_data.get("description", "")
                rules = json_data.get("rules", [])

                if not rules:
                    rprint("[red]Error:[/red] JSON file must contain 'rules' array")
                    raise typer.Exit(1)

                # Create RoutingConfig object from JSON data
                config = RoutingConfig(
                    name=config_name, description=config_description, rules=rules
                )

            except FileNotFoundError:
                rprint(f"[red]Error:[/red] JSON file '{from_json}' not found")
                raise typer.Exit(1)
            except json.JSONDecodeError as e:
                rprint(f"[red]Error:[/red] Invalid JSON in file '{from_json}': {e}")
                raise typer.Exit(1)
        elif interactive:
            config = _interactive_config_builder(name)
        else:
            # Create a simple default configuration
            endpoint = typer.prompt("Default endpoint URL")
            config = (
                ConfigBuilder(name, "Default routing configuration")
                .add_rule(
                    "default", description="Route all requests to default endpoint"
                )
                .add_target("custom", "default", endpoint)
                .build()
            )

        config_json = config.to_json()

        if output:
            # Save to local file
            with open(output, "w") as f:
                json.dump(config_json, f, indent=2)
            rprint(f"[green]✓[/green] Configuration saved to {output}")
        else:
            # Create in backend via API
            client = MixClient()
            response = client.create_routing_config(
                config.name,
                config.description or "",
                [rule.dict() for rule in config.rules],
            )

            if response:
                config_id = response.get("id")
                rprint(
                    f"[green]✓[/green] Configuration '{config.name}' created successfully (ID: {config_id})"
                )
                rprint(f"Use 'mixtrain routing view {config_id}' to view details")
            else:
                rprint("[red]Error:[/red] Failed to create configuration in backend")
                raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command(name="add-rule")
def add_rule(
    config_id: Optional[int] = typer.Argument(
        None, help="Configuration ID to add rule to (defaults to active config)"
    ),
    config_file: Optional[str] = typer.Option(
        None, "--config-file", help="Local configuration file to add rule to"
    ),
    name: Optional[str] = typer.Option(None, "-n", "--name", help="Rule name"),
):
    """Add a new rule to a routing configuration.

    If no config is specified, adds to active config by creating a duplicate.
    Active configs can't be edited directly, so a new version is created.
    """
    try:
        # Determine which config to use
        use_active = not config_id and not config_file

        if config_file:
            # Load from local file
            with open(config_file) as f:
                config_data = json.load(f)
            target_config_id = None
            is_active_config = False
        else:
            # Load from backend (either specific ID or active)
            if use_active:
                client = MixClient()
                config_data = client.get_active_routing_config()
                if not config_data:
                    rprint(
                        "[red]Error:[/red] No active routing configuration found in workspace"
                    )
                    rprint(
                        "Use 'mixtrain routing list-configs' to see available configurations"
                    )
                    raise typer.Exit(1)
                target_config_id = config_data.get("id") if config_data else None
                is_active_config = True
                rprint(
                    f"Using active config: {config_data.get('name', 'Unnamed')} (ID: {target_config_id})"
                )
            else:
                client = MixClient()
                config_data = client.get_routing_config(config_id)
                target_config_id = config_id
                # Check if this is the active config
                active_config_data = client.get_active_routing_config()
                is_active_config = (
                    active_config_data and active_config_data.get("id") == config_id
                )

        # Build new rule interactively
        rprint(
            f"[bold]Adding new rule to configuration: {config_data.get('name', 'Unnamed')}[/bold]"
        )
        if not name:
            name = typer.prompt("Rule name")

        priority = typer.prompt("Rule priority", default=0, type=int)
        description = typer.prompt("Rule description", default="")

        # Create rule data
        rule_data = {
            "name": name,
            "priority": priority,
            "description": description,
            "is_enabled": True,
            "conditions": [],
            "targets": [],
            "strategy": "single",
        }

        # Add conditions
        rprint(
            "\n[bold]Add conditions (press Enter with empty field to finish):[/bold]"
        )
        while True:
            field = typer.prompt("Condition field", default="")
            if not field.strip():
                break
            operator = typer.prompt(
                "Operator (equals, in, greater_than, etc.)", default="equals"
            )
            value = typer.prompt("Value (or JSON for arrays)")
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                parsed_value = value

            rule_data["conditions"].append(
                {"field": field, "operator": operator, "value": parsed_value}
            )

        # Add targets
        rprint("\n[bold]Add targets (at least one required):[/bold]")
        while True:
            target_data = _interactive_target_builder()
            rule_data["targets"].append(target_data)

            if not typer.confirm("Add another target?"):
                break

        # Set strategy based on number of targets
        if len(rule_data["targets"]) > 1:
            strategy = typer.prompt("Strategy", default="split")
            rule_data["strategy"] = strategy

        # Add rule to config
        rules = config_data.get("rules", [])
        rules.append(rule_data)
        config_data["rules"] = rules

        # Save the configuration
        if config_file:
            # Save back to local file
            with open(config_file, "w") as f:
                json.dump(config_data, f, indent=2)
            rprint(f"Rule '{name}' added to {config_file}")
        else:
            # Update backend config
            if is_active_config:
                # Create new config as duplicate of active
                client = MixClient()
                new_name = f"{config_data.get('name', 'Config')} (Modified)"
                response = client.create_routing_config(
                    new_name,
                    config_data.get("description", "") + " - Modified with new rule",
                    rules,
                )
                new_config_id = response.get("id") if response else None
                rprint(
                    f"Rule '{name}' added to new configuration '{new_name}' (ID: {new_config_id})"
                )
                rprint(
                    "Note: Active config can't be modified directly, so a new config was created"
                )
            else:
                # Update existing config
                client = MixClient()
                client.update_routing_config(target_config_id, rules=rules)
                rprint(f"Rule '{name}' added to configuration ID {target_config_id}")

    except FileNotFoundError:
        rprint(f"[red]Error:[/red] Configuration file not found")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        rprint(f"[red]Error:[/red] Invalid JSON in configuration file: {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def validate(
    config_id: Optional[int] = typer.Argument(
        None, help="Configuration ID to validate"
    ),
    config_file: Optional[str] = typer.Option(
        None, "--config-file", help="Local configuration file to validate"
    ),
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Show detailed validation results"
    ),
):
    """Validate a routing configuration by ID or from a local file."""
    _validate_config_args(config_id, config_file)

    try:
        config_data = _load_config_data(config_id, config_file)

        # Validate configuration
        errors = RoutingValidator.validate_config_dict(config_data)

        if verbose:
            # Run linter for comprehensive analysis
            try:
                from .routing.models import RoutingConfig

                config = RoutingConfig.from_json(config_data)
                lint_results = ConfigurationLinter.lint_config(config)
                _display_lint_results(lint_results)
            except Exception as e:
                rprint(f"[yellow]Warning:[/yellow] Could not run linter: {e}")

        if errors:
            rprint(f"[red]✗ Validation failed with {len(errors)} errors:[/red]")
            for i, error in enumerate(errors, 1):
                rprint(f"  {i}. {error}")
            raise typer.Exit(1)
        else:
            rprint("[green]✓ Configuration is valid![/green]")

    except Exception as e:
        _handle_config_error(e, config_file or f"config ID {config_id}")
        raise typer.Exit(1)


@app.command()
def test(
    config_id: Optional[int] = typer.Argument(None, help="Configuration ID to test"),
    config_file: Optional[str] = typer.Option(
        None, "--config-file", help="Local configuration file to test"
    ),
    request_file: Optional[str] = typer.Option(
        None, "-r", "--request", help="JSON file containing request data"
    ),
    request_data: Optional[str] = typer.Option(
        None, "-d", "--data", help="JSON string with request data"
    ),
    expected_rule: Optional[str] = typer.Option(
        None, "-e", "--expected", help="Expected rule name"
    ),
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Show detailed results"
    ),
):
    """Test routing against sample request data by ID or from a local file."""
    _validate_config_args(config_id, config_file)

    try:
        config_data = _load_config_data(config_id, config_file)
        engine = RoutingEngineFactory.from_json(config_data)

        # Get request data
        if request_file:
            with open(request_file) as f:
                request_data_dict = json.load(f)
        elif request_data:
            request_data_dict = json.loads(request_data)
        else:
            # Interactive input
            request_data_dict = _interactive_request_builder()

        # Route the request
        result = engine.test_request(request_data_dict, expected_rule)

        # Display results
        _display_routing_result(result, verbose)

        # Exit with error code if test failed expectation
        if expected_rule and result.metadata.get("matched_expected") is False:
            raise typer.Exit(1)

    except json.JSONDecodeError as e:
        rprint(f"[red]Error:[/red] Invalid JSON: {e}")
        raise typer.Exit(1)
    except Exception as e:
        _handle_config_error(e, config_file or f"config ID {config_id}")
        raise typer.Exit(1)


@app.command()
def coverage(
    test_requests: str = typer.Argument(
        help="JSON file containing array of test requests"
    ),
    config_id: Optional[int] = typer.Option(
        None, "--config-id", help="Configuration ID to analyze"
    ),
    config_file: Optional[str] = typer.Option(
        None, "--config-file", help="Local configuration file to analyze"
    ),
):
    """Analyze rule coverage for a set of test requests."""
    _validate_config_args(config_id, config_file)

    try:
        config_data = _load_config_data(config_id, config_file)
        engine = RoutingEngineFactory.from_json(config_data)

        with open(test_requests) as f:
            requests_data = json.load(f)

        if not isinstance(requests_data, list):
            rprint(
                "[red]Error:[/red] Test requests file must contain an array of request objects"
            )
            raise typer.Exit(1)

        # Analyze coverage
        coverage_results = engine.get_rule_coverage(requests_data)

        # Display results
        _display_coverage_results(coverage_results)

        # Exit with error if coverage is poor
        if coverage_results["coverage_percentage"] < 80:
            rprint(
                f"\n[yellow]Warning:[/yellow] Rule coverage is below 80% ({coverage_results['coverage_percentage']:.1f}%)"
            )
            raise typer.Exit(1)

    except Exception as e:
        _handle_config_error(e, config_file or f"config ID {config_id}")
        raise typer.Exit(1)


@app.command()
def view(
    config_id: Optional[int] = typer.Argument(
        None, help="Configuration ID to view (defaults to active config)"
    ),
    config_file: Optional[str] = typer.Option(
        None, "--config-file", help="Local configuration file to view"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output json format"),
):
    """View detailed routing configuration information by ID, from a local file, or the currently active config."""
    _validate_config_args(config_id, config_file, allow_active=True)

    try:
        # Use active config if no specific ID or file provided
        use_active = not config_id and not config_file
        config_data = _load_config_data(config_id, config_file, use_active=use_active)

        config = RoutingConfig.from_json(config_data)

        if json_output:
            rprint(json.dumps(config.to_json(), indent=2))
        else:
            _display_detailed_config_view(config)

    except Exception as e:
        _handle_config_error(e, config_file or f"config ID {config_id}")
        raise typer.Exit(1)


def _interactive_config_builder(name: str) -> "RoutingConfig":
    """Interactive configuration builder."""
    description = typer.prompt("Configuration description", default="")
    builder = ConfigBuilder(name, description)

    while True:
        rule_name = typer.prompt("\nRule name")
        rule_priority = typer.prompt("Rule priority", default=0, type=int)
        rule_description = typer.prompt("Rule description", default="")

        rule_builder = builder.add_rule(rule_name, rule_priority, rule_description)

        # Add conditions
        rprint(
            "\n[bold]Add conditions (press Enter with empty field to finish):[/bold]"
        )
        while True:
            field = typer.prompt("Condition field", default="")
            if not field.strip():
                break

            operator = typer.prompt(
                "Operator (equals, in, greater_than, etc.)", default="equals"
            )
            value = typer.prompt("Value (or JSON for arrays)")

            try:
                # Try to parse as JSON first
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                # Use as string if not valid JSON
                parsed_value = value

            rule_builder = rule_builder.with_condition(field, operator, parsed_value)

        # Set strategy
        strategy = typer.prompt(
            "Strategy", default=RoutingStrategy.SINGLE, type=RoutingStrategy
        )

        if strategy == RoutingStrategy.SPLIT:
            rule_builder = rule_builder.use_split_strategy()
        elif strategy == RoutingStrategy.SHADOW:
            rule_builder = rule_builder.use_shadow_strategy()
        elif strategy == RoutingStrategy.FALLBACK:
            rule_builder = rule_builder.use_fallback_strategy()

        # Add targets
        rprint("\n[bold]Add targets:[/bold]")
        while True:
            provider = typer.prompt("Target provider", default="")
            if not provider.strip():
                break

            target_data = _interactive_target_builder_from_provider(provider)

            # Use the builder pattern with the target data
            rule_builder = rule_builder.add_target(
                target_data["provider"],
                target_data["model_name"],
                target_data["endpoint"],
                target_data["weight"],
                function_name=target_data.get("function_name"),
                request_class=target_data.get("request_class"),
            )

        # Ask if user wants to add another rule
        add_another = typer.confirm("\nAdd another rule?")
        if add_another:
            rule_builder = rule_builder.and_rule("", 0, "")
        else:
            break

    return rule_builder.build()


def _interactive_target_builder() -> Dict[str, Any]:
    """Interactive target builder that handles provider-specific fields."""
    provider = typer.prompt("Target provider")
    model_name = typer.prompt("Model name")
    weight = typer.prompt("Weight", default=1.0, type=float)

    target_data = {"provider": provider, "model_name": model_name, "weight": weight}

    if provider.lower() == "modal":
        # Modal provider uses function_name and request_class, endpoint is auto-generated
        function_name = typer.prompt("Function name", default="main")
        request_class = typer.prompt("Request class", default="")
        # Generate placeholder Modal endpoint from model name
        endpoint = f"https://{model_name}--modal.modal.run"
        target_data.update(
            {
                "endpoint": endpoint,
                "function_name": function_name,
                "request_class": request_class or None,
            }
        )
    else:
        # Other providers use endpoint
        endpoint = typer.prompt("Endpoint URL")
        target_data.update(
            {"endpoint": endpoint, "function_name": None, "request_class": None}
        )

    return target_data


def _interactive_target_builder_from_provider(provider: str) -> Dict[str, Any]:
    """Interactive target builder when provider is already known."""
    model_name = typer.prompt("Model name")
    weight = typer.prompt("Weight", default=1.0, type=float)

    target_data = {"provider": provider, "model_name": model_name, "weight": weight}

    if provider.lower() == "modal":
        # Modal provider uses function_name and request_class, endpoint is auto-generated
        function_name = typer.prompt("Function name", default="main")
        request_class = typer.prompt("Request class", default="")
        # Generate placeholder Modal endpoint from model name
        endpoint = f"https://{model_name}--modal.modal.run"
        target_data.update(
            {
                "endpoint": endpoint,
                "function_name": function_name,
                "request_class": request_class or None,
            }
        )
    else:
        # Other providers use endpoint
        endpoint = typer.prompt("Endpoint URL")
        target_data.update(
            {"endpoint": endpoint, "function_name": None, "request_class": None}
        )

    return target_data


def _interactive_request_builder() -> Dict[str, Any]:
    """Interactive request data builder."""
    rprint("[bold]Enter request data (JSON format):[/bold]")
    rprint('Example: {"user": {"tier": "premium"}, "request": {"type": "image"}}')

    while True:
        request_input = typer.prompt("Request data")
        try:
            return json.loads(request_input)
        except json.JSONDecodeError as e:
            rprint(f"[red]Invalid JSON:[/red] {e}")
            rprint("Please enter valid JSON data.")


def _display_routing_result(result, verbose: bool = False):
    """Display routing test results."""
    if result.matched_rule:
        rprint(f"[green]✓ Matched Rule:[/green] {result.matched_rule.name}")
        rprint(f"[blue]Strategy:[/blue] {result.matched_rule.strategy}")
        rprint(f"[blue]Selected Targets:[/blue] {len(result.selected_targets)}")

        if verbose:
            # Show matched rule details
            table = Table(title="Matched Rule Details")
            table.add_column("Property", style="cyan")
            table.add_column("Value")

            table.add_row("Name", result.matched_rule.name)
            table.add_row("Description", result.matched_rule.description or "")
            table.add_row("Priority", str(result.matched_rule.priority))
            table.add_row("Strategy", result.matched_rule.strategy)
            table.add_row("Conditions", str(len(result.matched_rule.conditions)))

            console.print(table)

            # Show selected targets
            if result.selected_targets:
                targets_table = Table(title="Selected Targets")
                targets_table.add_column("Provider")
                targets_table.add_column("Model")
                targets_table.add_column("Endpoint")
                targets_table.add_column("Weight")
                targets_table.add_column("Shadow")

                for target in result.selected_targets:
                    targets_table.add_row(
                        target.provider,
                        target.model_name,
                        target.endpoint,
                        str(target.weight),
                        "Yes" if target.is_shadow else "No",
                    )

                console.print(targets_table)

    else:
        rprint("[red]✗ No rules matched[/red]")

    rprint(f"\n[dim]Explanation:[/dim] {result.explanation}")

    if result.execution_time_ms:
        rprint(f"[dim]Execution time:[/dim] {result.execution_time_ms:.2f}ms")


def _display_coverage_results(results: Dict[str, Any]):
    """Display coverage analysis results."""
    table = Table(title="Rule Coverage Analysis")
    table.add_column("Metric", style="cyan")
    table.add_column("Value")

    table.add_row("Total Requests", str(results["total_requests"]))
    table.add_row("Total Rules", str(results["total_rules"]))
    table.add_row("Covered Rules", str(results["covered_rules"]))
    table.add_row("Coverage Percentage", f"{results['coverage_percentage']:.1f}%")
    table.add_row("Unmatched Requests", str(results["unmatched_requests"]))

    console.print(table)

    # Show rule hits
    if results["rule_hits"]:
        hits_table = Table(title="Rule Hit Counts")
        hits_table.add_column("Rule Name")
        hits_table.add_column("Hits", justify="right")

        for rule_name, hits in results["rule_hits"].items():
            style = "green" if hits > 0 else "red"
            hits_table.add_row(rule_name, str(hits), style=style)

        console.print(hits_table)

    # Show uncovered rules
    if results["uncovered_rules"]:
        rprint(
            f"\n[yellow]Uncovered Rules ({len(results['uncovered_rules'])}):[/yellow]"
        )
        for rule in results["uncovered_rules"]:
            rprint(f"  • {rule}")


def _display_lint_results(lint_results: Dict[str, List[str]]):
    """Display linting results."""
    errors = lint_results.get("errors", [])
    warnings = lint_results.get("warnings", [])
    suggestions = lint_results.get("suggestions", [])

    if errors:
        rprint(f"\n[red]Errors ({len(errors)}):[/red]")
        for error in errors:
            rprint(f"  ✗ {error}")

    if warnings:
        rprint(f"\n[yellow]Warnings ({len(warnings)}):[/yellow]")
        for warning in warnings:
            rprint(f"  ⚠ {warning}")

    if suggestions:
        rprint(f"\n[blue]Suggestions ({len(suggestions)}):[/blue]")
        for suggestion in suggestions:
            rprint(f"  💡 {suggestion}")


def _validate_config_args(
    config_id: Optional[int], config_file: Optional[str], allow_active: bool = False
) -> None:
    """Validate configuration arguments and exit with error if invalid."""
    if config_id and config_file:
        rprint("[red]Error:[/red] Cannot specify both config_id and --config-file")
        raise typer.Exit(1)

    if not allow_active and not config_id and not config_file:
        rprint("[red]Error:[/red] Either config_id or --config-file must be provided")
        raise typer.Exit(1)


def _load_config_data(
    config_id: Optional[int] = None,
    config_file: Optional[str] = None,
    use_active: bool = False,
) -> dict:
    """Load configuration data from various sources.

    Args:
        config_id: Specific configuration ID to load from mixtrain platform
        config_file: Local configuration file path
        use_active: Load active configuration from mixtrain platform if no config_id or config_file

    Returns:
        Normalized configuration data dictionary

    Raises:
        typer.Exit: On any loading error
    """
    if config_file:
        # Load from local file
        try:
            with open(config_file) as f:
                config_data = json.load(f)
            return config_data
        except FileNotFoundError:
            rprint(f"[red]Error:[/red] Configuration file '{config_file}' not found")
            raise typer.Exit(1)
        except json.JSONDecodeError as e:
            rprint(f"[red]Error:[/red] Invalid JSON in configuration file: {e}")
            raise typer.Exit(1)

    elif config_id:
        # Load from mixtrain platform by specific ID
        try:
            client = MixClient()
            config_data = client.get_routing_config(config_id)
            return config_data
        except Exception as e:
            rprint(f"[red]Error:[/red] Failed to load config {config_id}: {e}")
            raise typer.Exit(1)

    elif use_active:
        # Load active config from mixtrain platform
        try:
            client = MixClient()
            response = client.get_active_routing_config()
            if not response:
                rprint(
                    "[red]Error:[/red] No active routing configuration found in workspace"
                )
                rprint(
                    "Use 'mixtrain routing list' to see available configurations and activate one"
                )
                raise typer.Exit(1)
            return response
        except Exception as e:
            if "No active routing configuration" in str(e):
                raise
            rprint(f"[red]Error:[/red] Failed to load active config: {e}")
            raise typer.Exit(1)
    else:
        rprint("[red]Error:[/red] No configuration source specified")
        raise typer.Exit(1)


def _handle_config_error(error: Exception, config_file: str = None):
    """Handle and display user-friendly configuration errors."""

    # Handle Pydantic validation errors specifically
    if isinstance(error, RoutingConfigValidationError):
        rprint("[red]Configuration Validation Error:[/red]")
        rprint("Your configuration file has the following issues:\n")

        for error_detail in error.errors():
            field_name = ".".join(str(loc) for loc in error_detail.get("loc", []))
            error_type = error_detail.get("type", "")
            error_msg = error_detail.get("msg", "")

            if error_type == "missing":
                if field_name == "name":
                    rprint(
                        "  • [red]Missing required field:[/red] [yellow]'name'[/yellow]"
                    )
                    rprint("    Your configuration needs a name at the top level.")
                    rprint('    [dim]Add: "name": "My Configuration"[/dim]')
                elif field_name == "rules":
                    rprint(
                        "  • [red]Missing required field:[/red] [yellow]'rules'[/yellow]"
                    )
                    rprint("    Your configuration needs an array of routing rules.")
                    rprint('    [dim]Add: "rules": [...][/dim]')
                else:
                    rprint(
                        f"  • [red]Missing required field:[/red] [yellow]'{field_name}'[/yellow]"
                    )
            elif error_type == "value_error":
                if "at least one target must be specified" in error_msg:
                    rprint(
                        f"  • [red]Rule validation error:[/red] Rule at {field_name} has no targets"
                    )
                    rprint("    Each routing rule must have at least one target model.")
                elif "at least one routing rule must be specified" in error_msg:
                    rprint("  • [red]Configuration error:[/red] Rules array is empty")
                    rprint("    Your configuration needs at least one routing rule.")
                else:
                    rprint(
                        f"  • [red]Validation error in {field_name}:[/red] {error_msg}"
                    )
            else:
                rprint(f"  • [red]Error in {field_name}:[/red] {error_msg}")

        rprint("\n[blue]Supported file formats:[/blue]")

        rprint("\n[dim]1. Direct configuration:[/dim]")
        rprint("[cyan]{[/cyan]")
        rprint('[cyan]  "name": "Configuration Name",[/cyan]')
        rprint('[cyan]  "description": "Optional description",[/cyan]')
        rprint('[cyan]  "rules": [[/cyan]')
        rprint(
            '[cyan]    {"name": "rule_name", "conditions": [...], "targets": [...]}[/cyan]'
        )
        rprint("[cyan]  ][/cyan]")
        rprint("[cyan]}[/cyan]")

        rprint("\n[dim]2. Rules array:[/dim]")
        rprint("[cyan][[/cyan]")
        rprint(
            '[cyan]  {"name": "rule_name", "conditions": [...], "targets": [...]}[/cyan]'
        )
        rprint("[cyan]][/cyan]")

        if config_file:
            rprint(f"\n[blue]💡 Helpful commands:[/blue]")
            rprint(
                f'  • [yellow]mixtrain routing create "My Config"[/yellow] - Create a new configuration'
            )
            rprint(
                f"  • [yellow]mixtrain routing validate {config_file}[/yellow] - Get detailed validation info"
            )

    else:
        # Handle other types of errors
        error_str = str(error).lower()

        # Try to detect common issues from string patterns
        if "validation error" in error_str or "field required" in error_str:
            rprint("[red]Configuration Validation Error:[/red]")

            if "name" in error_str and (
                "field required" in error_str or "missing" in error_str
            ):
                rprint("  • [red]Missing required field:[/red] [yellow]'name'[/yellow]")
                rprint("    The configuration must have a name at the top level.")

            if "rules" in error_str and (
                "field required" in error_str or "missing" in error_str
            ):
                rprint(
                    "  • [red]Missing required field:[/red] [yellow]'rules'[/yellow]"
                )
                rprint("    The configuration must have an array of routing rules.")

            rprint(f"\n[dim]Original error: {str(error)}[/dim]")
        else:
            rprint(f"[red]Error:[/red] {str(error)}")


def _display_detailed_config_view(config):
    """Display configuration details in a compact, table-based format."""
    # Header with basic info
    if config.description:
        rprint(f"[dim]{config.description}[/dim]")

    rprint(
        f"Rules: {sum(1 for r in config.rules if r.is_enabled)}/{len(config.rules)} active"
    )

    if not config.rules:
        rprint("\n[yellow]No routing rules found in this configuration.[/yellow]")
        return

    # Main rules table
    table = Table(show_header=True, header_style="bold cyan", title=config.name)
    table.add_column("Rule Name", style="bold")
    table.add_column("Priority", style="dim")
    table.add_column("Conditions")
    table.add_column("Strategy")
    table.add_column("Targets")

    # Sort rules by priority (highest first)
    sorted_rules = sorted(config.rules, key=lambda r: r.priority, reverse=True)

    for rule in sorted_rules:
        # Conditions summary
        if rule.conditions:
            conditions_summary = []
            for condition in rule.conditions:
                operator_symbol = {
                    "equals": "==",
                    "not_equals": "!=",
                    "in": "∈",
                    "not_in": "∉",
                    "contains": "⊃",
                    "greater_than": ">",
                    "less_than": "<",
                    "greater_than_or_equal": "≥",
                    "less_than_or_equal": "≤",
                    "regex": "~",
                    "exists": "∃",
                    "not_exists": "∄",
                }.get(condition.operator, condition.operator)

                value_str = str(condition.value)
                # if len(value_str) > 10:
                #     value_str = value_str[:8] + ".."

                conditions_summary.append(
                    f"{condition.field}{operator_symbol}{value_str}"
                )

            conditions_text = "\n".join(conditions_summary)
            # if len(rule.conditions) > 2:
            #     conditions_text += f"\n+{len(rule.conditions)-2} more"
        else:
            conditions_text = "[dim]none[/dim]"

        # Targets summary
        if rule.targets:
            targets_summary = []
            for target in rule.targets[:2]:  # Show first 2 targets
                target_text = f"{target.provider}/{target.model_name}"
                if target.weight != 1.0:
                    target_text += f" ({target.weight})"
                if target.is_shadow:
                    target_text += " [dim](shadow)[/dim]"
                targets_summary.append(target_text)

            targets_text = "\n".join(targets_summary)
            if len(rule.targets) > 2:
                targets_text += f"\n+{len(rule.targets) - 2} more"
        else:
            targets_text = "[red]none![/red]"

        if rule.is_enabled:
            table.add_row(
                rule.name,
                str(rule.priority),
                conditions_text,
                rule.strategy,
                targets_text,
            )
        else:
            table.add_row(
                f"[dim]{rule.name}[/dim]",
                f"[dim]{str(rule.priority)}[/dim]",
                f"[dim]{conditions_text}[/dim]",
                f"[dim]{rule.strategy}[/dim]",
                f"[dim]{targets_text}[/dim]",
            )
        table.add_section()

    console.print(table)
