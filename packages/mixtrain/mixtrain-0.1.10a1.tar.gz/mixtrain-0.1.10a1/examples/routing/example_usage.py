#!/usr/bin/env python3
"""
Example usage of the Mixtrain routing engine.

This script demonstrates various routing engine features including:
- Configuration creation using builder pattern
- Different routing strategies
- Condition evaluation
- Testing and validation
"""

from mixtrain.routing import (
    RoutingEngine,
    RoutingEngineFactory,
    ConfigBuilder,
    RoutingValidator,
    RoutingConfigValidationError,
)
from mixtrain.routing.builder import create_ab_test_config, create_premium_routing_config
import json


def example_simple_routing():
    """Example 1: Simple premium user routing."""
    print("=== Example 1: Simple Premium User Routing ===")

    # Create configuration using builder pattern
    config = (ConfigBuilder("premium_routing", "Route premium users to better models")
              .add_rule("premium_users", priority=100, description="Premium tier users")
              .when("user.tier").equals("premium")
              .add_target("modal", "gpt4-turbo", "https://gpt4-turbo.modal.run")
              .and_rule("standard_users", priority=50, description="Standard tier users")
              .add_target("modal", "gpt3.5-turbo", "https://gpt35-turbo.modal.run")
              .build())

    # Create engine
    engine = RoutingEngine(config)

    # Test premium user
    premium_request = {"user": {"tier": "premium"}, "request": {"prompt": "Hello world"}}
    result = engine.route_request(premium_request)

    print(f"Premium user routed to: {result.selected_targets[0].model_name}")
    print(f"Explanation: {result.explanation}")

    # Test standard user
    standard_request = {"user": {"tier": "standard"}, "request": {"prompt": "Hello world"}}
    result = engine.route_request(standard_request)

    print(f"Standard user routed to: {result.selected_targets[0].model_name}")
    print(f"Explanation: {result.explanation}")
    print()


def example_ab_testing():
    """Example 2: A/B testing with split strategy."""
    print("=== Example 2: A/B Testing ===")

    config = (ConfigBuilder("ab_test", "A/B test for image models")
              .add_rule("image_ab_test", priority=100, description="Split traffic for image generation")
              .when("request.type").equals("image")
              .use_split_strategy()
              .add_target("modal", "flux-v1", "https://flux-v1.modal.run", weight=0.8)
              .with_label("control")
              .add_target("modal", "flux-v2", "https://flux-v2.modal.run", weight=0.2)
              .with_label("variant")
              .and_rule("fallback", priority=10, description="Fallback for non-image requests")
              .add_target("fal", "llama-3", "https://fal.run/llama-3")
              .build())

    engine = RoutingEngine(config)

    # Test multiple image requests to see split distribution
    print("Testing 10 image requests to see split distribution:")
    control_count = 0
    variant_count = 0

    for i in range(10):
        request = {"request": {"type": "image", "prompt": f"Image {i}"}}
        result = engine.route_request(request)
        selected_target = result.selected_targets[0]

        if selected_target.model_name == "flux-v1":
            control_count += 1
        elif selected_target.model_name == "flux-v2":
            variant_count += 1

    print(f"Control (flux-v1): {control_count}/10 requests")
    print(f"Variant (flux-v2): {variant_count}/10 requests")

    # Test non-image request
    text_request = {"request": {"type": "text", "prompt": "Hello"}}
    result = engine.route_request(text_request)
    print(f"Text request routed to: {result.selected_targets[0].model_name}")
    print()


def example_complex_conditions():
    """Example 3: Complex conditional routing."""
    print("=== Example 3: Complex Conditional Routing ===")

    config = (ConfigBuilder("complex_routing", "Complex business logic routing")
              .add_rule("vip_image_generation", priority=100,
                       description="VIP users with credits for image generation")
              .when("user.tier").equals("vip")
              .with_condition("user.credits", "greater_than", 10)
              .with_condition("request.type", "equals", "image")
              .add_target("modal", "premium-flux", "https://premium-flux.modal.run")

              .and_rule("enterprise_fallback", priority=90,
                       description="Enterprise users with fallback strategy")
              .when("user.tier").equals("enterprise")
              .use_fallback_strategy()
              .add_target("modal", "enterprise-primary", "https://enterprise-primary.modal.run")
              .add_target("fal", "enterprise-backup", "https://fal.run/enterprise-backup")

              .and_rule("geographic_routing", priority=80,
                       description="Route based on geographic region")
              .when("user.region").is_in(["us-east", "us-west"])
              .with_condition("request.priority", "equals", "high")
              .add_target("modal", "us-optimized", "https://us-optimized.modal.run")

              .and_rule("catch_all", priority=1, description="Default routing")
              .add_target("fal", "default-model", "https://fal.run/default")
              .build())

    engine = RoutingEngine(config)

    # Test various scenarios
    test_cases = [
        {
            "name": "VIP Image Generation",
            "data": {
                "user": {"tier": "vip", "credits": 15},
                "request": {"type": "image", "prompt": "Generate an image"}
            }
        },
        {
            "name": "Enterprise with Fallback",
            "data": {
                "user": {"tier": "enterprise"},
                "request": {"type": "text", "prompt": "Business query"}
            }
        },
        {
            "name": "Geographic High Priority",
            "data": {
                "user": {"region": "us-east"},
                "request": {"priority": "high", "prompt": "Urgent request"}
            }
        },
        {
            "name": "Default Fallback",
            "data": {
                "user": {"tier": "standard"},
                "request": {"type": "general", "prompt": "Regular request"}
            }
        }
    ]

    for test_case in test_cases:
        result = engine.route_request(test_case["data"])
        print(f"{test_case['name']}: {result.matched_rule.name if result.matched_rule else 'No match'}")
        if result.selected_targets:
            print(f"  -> {result.selected_targets[0].model_name}")
        print(f"  -> {result.explanation}")
    print()


def example_shadow_routing():
    """Example 4: Shadow routing for testing."""
    print("=== Example 4: Shadow Routing ===")

    config = (ConfigBuilder("shadow_test", "Shadow routing for model testing")
              .add_rule("production_shadow", priority=100,
                       description="Shadow test new model against production")
              .when("user.tier").is_in(["premium", "enterprise"])
              .use_shadow_strategy()
              .add_target("modal", "production-model", "https://production.modal.run")
              .add_target("modal", "experimental-model", "https://experimental.modal.run")
              .build())

    engine = RoutingEngine(config)

    request = {
        "user": {"tier": "premium"},
        "request": {"prompt": "Test shadow routing"}
    }

    result = engine.route_request(request)

    print(f"Matched rule: {result.matched_rule.name}")
    print(f"Number of targets: {len(result.selected_targets)}")

    for i, target in enumerate(result.selected_targets):
        target_type = "Shadow" if target.is_shadow else "Primary"
        print(f"  {target_type}: {target.model_name}")
    print()


def example_validation_and_testing():
    """Example 5: Configuration validation and testing."""
    print("=== Example 5: Validation and Testing ===")

    # Create configuration with intentional errors
    try:
        invalid_config = (ConfigBuilder("invalid", "Config with errors")
                         .add_rule("bad_split", priority=100)
                         .use_split_strategy()
                         .add_target("modal", "model1", "https://model1.com", weight=0.6)
                         .add_target("modal", "model2", "https://model2.com", weight=0.3)
                         .build())

        RoutingValidator.validate_and_raise(invalid_config)

    except RoutingConfigValidationError as e:
        print("Caught validation error (expected):")
        for error in e.errors:
            print(f"  - {error}")

    # Create valid configuration
    valid_config = create_premium_routing_config(
        "test_premium",
        "https://premium.modal.run",
        "https://standard.modal.run"
    )

    # Validate
    errors = RoutingValidator.validate_config(valid_config)
    print(f"Valid configuration errors: {len(errors)}")

    # Test with expectations
    engine = RoutingEngine(valid_config)

    test_result = engine.test_request(
        {"user": {"tier": "premium"}},
        expected_rule="premium_users"
    )

    print(f"Test result - matched expected: {test_result.metadata['matched_expected']}")

    # Coverage analysis
    test_requests = [
        {"user": {"tier": "premium"}},
        {"user": {"tier": "standard"}},
        {"user": {"tier": "premium"}},
        {"user": {"tier": "standard"}},
        {"user": {"tier": "enterprise"}},  # This won't match any rule
    ]

    coverage = engine.get_rule_coverage(test_requests)
    print(f"Rule coverage: {coverage['coverage_percentage']:.1f}%")
    print(f"Unmatched requests: {coverage['unmatched_requests']}")
    print()


def example_json_configuration():
    """Example 6: Working with JSON configurations."""
    print("=== Example 6: JSON Configuration ===")

    # Create configuration
    config = create_ab_test_config(
        "json_test",
        "https://control.modal.run",
        "https://variant.modal.run",
        variant_percentage=0.3
    )

    # Convert to JSON
    config_json = config.to_json()

    print("Configuration as JSON:")
    print(json.dumps(config_json, indent=2)[:500] + "...")
    
    config_json = json.loads(config_json)
    # Create engine from JSON
    engine = RoutingEngineFactory.from_json(config_json)

    # Test the engine
    result = engine.route_request({"test": "data"})
    print(f"Routing result: {result.selected_targets[0].model_name}")
    print()


def main():
    """Run all examples."""
    print("Mixtrain Routing Engine Examples")
    print("================================\n")

    import mixtrain.client as mix
    config = mix.get_active_routing_config()
    engine = RoutingEngineFactory.from_json(config['config_data'])
    result = engine.route_request({"user": {"tier": "premium"}})
    try:
        example_simple_routing()
        example_ab_testing()
        example_complex_conditions()
        example_shadow_routing()
        example_validation_and_testing()
        example_json_configuration()

        print("All examples completed successfully! ✅")

    except Exception as e:
        print(f"Error running examples: {e}")
        raise


if __name__ == "__main__":
    main()