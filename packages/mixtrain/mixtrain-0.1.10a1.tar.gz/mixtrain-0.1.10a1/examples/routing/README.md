# Mixtrain Routing Engine

The Mixtrain routing engine provides intelligent request routing and load balancing for AI model inference. It supports multiple routing strategies, conditional logic, and provider-agnostic configuration.

## Quick Start

### Installation

The routing engine is included in the Mixtrain SDK:

```bash
cd mixtrain && uv pip install -e .
```

### Basic Usage

#### 1. Programmatic Usage

```python
from mixtrain.routing import RoutingEngine, ConfigBuilder

# Create a simple configuration
config = (ConfigBuilder("production", "Production routing")
          .add_rule("premium_users", priority=100)
          .when("user.tier").equals("premium")
          .add_target("modal", "premium-model", "https://premium.modal.run")
          .and_rule("default", priority=10)
          .add_target("modal", "default-model", "https://default.modal.run")
          .build())

# Create engine
engine = RoutingEngine(config)

# Route a request
request_data = {"user": {"tier": "premium"}, "request": {"type": "chat"}}
result = engine.route_request(request_data)

print(f"Matched rule: {result.matched_rule.name}")
print(f"Selected target: {result.selected_targets[0].endpoint}")
```

#### 2. CLI Usage

```bash
# Validate a configuration
mixtrain routing validate simple_routing.json

# Test routing against sample data
mixtrain routing test simple_routing.json --data '{"user":{"tier":"premium"}}'

# Analyze rule coverage
mixtrain routing coverage ab_test_routing.json test_requests.json

# Explain configuration
mixtrain routing explain simple_routing.json
```

#### 3. JSON Configuration

```json
{
  "name": "My Routing Config",
  "description": "Production routing configuration",
  "rules": [
    {
      "name": "premium_users",
      "description": "Route premium users to premium models",
      "priority": 100,
      "conditions": [
        {
          "field": "user.tier",
          "operator": "equals",
          "value": "premium"
        }
      ],
      "strategy": "single",
      "targets": [
        {
          "provider": "modal",
          "model_name": "premium-gpt4",
          "endpoint": "https://premium-gpt4.modal.run",
          "weight": 1.0
        }
      ]
    }
  ]
}
```

## Features

### Routing Strategies

1. **Single**: Route to one target
2. **Split**: A/B testing with weighted distribution
3. **Shadow**: Primary + shadow routing for testing
4. **Fallback**: Try targets in order until success

### Condition Operators

- `equals`, `not_equals`: Exact matching
- `in`, `not_in`: List membership
- `contains`, `not_contains`: Substring matching
- `exists`, `not_exists`: Field existence
- `greater_than`, `less_than`: Numeric comparison
- `regex`: Regular expression matching

### Supported Providers

- **Modal**: Serverless ML inference
- **Fal**: Fast AI model hosting
- **Custom**: Any HTTP endpoint

## Examples

### 1. User Tiering

Route premium users to better models:

```python
config = (ConfigBuilder("user_tiering", "Route by user tier")
          .add_rule("premium", priority=100)
          .when("user.tier").equals("premium")
          .add_target("modal", "gpt4", "https://gpt4.modal.run")
          .and_rule("standard", priority=50)
          .add_target("modal", "gpt35", "https://gpt35.modal.run")
          .build())
```

### 2. A/B Testing

Split traffic between model versions:

```python
config = (ConfigBuilder("ab_test", "Test new model")
          .add_rule("model_test", priority=100)
          .when("request.type").equals("image")
          .use_split_strategy()
          .add_target("modal", "flux-v1", "https://flux-v1.modal.run", weight=0.8)
          .with_label("control")
          .add_target("modal", "flux-v2", "https://flux-v2.modal.run", weight=0.2)
          .with_label("variant")
          .build())
```

### 3. Regional Routing

Route based on user location:

```python
config = (ConfigBuilder("regional", "Route by region")
          .add_rule("us_east", priority=100)
          .when("user.region").equals("us-east")
          .add_target("modal", "model-us-east", "https://us-east.modal.run")
          .and_rule("us_west", priority=100)
          .when("user.region").equals("us-west")
          .add_target("modal", "model-us-west", "https://us-west.modal.run")
          .build())
```

### 4. Shadow Testing

Test new models with shadow traffic:

```python
config = (ConfigBuilder("shadow_test", "Shadow testing setup")
          .add_rule("production_shadow", priority=100)
          .when("user.tier").equals("premium")
          .use_shadow_strategy()
          .add_target("modal", "prod-model", "https://prod.modal.run")
          .add_target("modal", "experimental", "https://experimental.modal.run")
          .build())
```

### 5. Fallback Routing

Ensure reliability with fallbacks:

```python
config = (ConfigBuilder("reliable", "High availability routing")
          .add_rule("ha_routing", priority=100)
          .use_fallback_strategy()
          .add_target("modal", "primary", "https://primary.modal.run")
          .add_target("fal", "backup", "https://fal.run/backup")
          .add_target("custom", "emergency", "https://emergency.example.com")
          .build())
```

## Advanced Usage

### Custom Conditions

Complex routing logic using multiple conditions:

```python
rule_builder = (builder.add_rule("complex_routing", priority=100)
                .when("user.tier").equals("premium")
                .with_condition("request.type", "in", ["image", "video"])
                .with_condition("user.credits", "greater_than", 100)
                .with_condition("user.region", "not_in", ["restricted_region"]))
```

### Conditional Builder Pattern

Fluent API for building conditions:

```python
from mixtrain.routing.conditions import condition

# Create reusable conditions
premium_user = condition("user.tier").equals("premium")
image_request = condition("request.type").contains("image")
has_credits = condition("user.credits").greater_than(0)

# Use in configuration
config = (ConfigBuilder("conditional", "Conditional routing")
          .add_rule("premium_images", priority=100)
          .with_condition(premium_user.field, premium_user.operator, premium_user.value)
          .with_condition(image_request.field, image_request.operator, image_request.value)
          .add_target("modal", "premium-flux", "https://premium-flux.modal.run")
          .build())
```

### Testing and Validation

```python
from mixtrain.routing import RoutingValidator

# Validate configuration
errors = RoutingValidator.validate_config(config)
if errors:
    print("Validation errors:", errors)

# Test with expectations
result = engine.test_request(
    request_data={"user": {"tier": "premium"}},
    expected_rule="premium_users"
)

print(f"Test passed: {result.metadata['matched_expected']}")

# Coverage analysis
test_requests = [
    {"user": {"tier": "premium"}},
    {"user": {"tier": "standard"}},
    {"user": {"tier": "enterprise"}},
]

coverage = engine.get_rule_coverage(test_requests)
print(f"Coverage: {coverage['coverage_percentage']:.1f}%")
```

## Integration with Mixtrain Platform

The routing engine integrates seamlessly with the Mixtrain platform:

```python
from mixtrain import client

# Create routing configuration on platform
config_json = config.to_json()
client.create_routing_config(workspace="my-workspace", config=config_json)

# Use in inference requests
response = client.inference(
    workspace="my-workspace",
    request_data={"user": {"tier": "premium"}, "prompt": "Hello world"}
)
```

## CLI Commands

### Create Configuration

```bash
# Interactive creation
mixtrain routing create "My Config" --interactive

# Simple creation
mixtrain routing create "Simple Config" --output config.json
```

### Validate Configuration

```bash
# Basic validation
mixtrain routing validate config.json

# Detailed validation with linting
mixtrain routing validate config.json --verbose
```

### Test Routing

```bash
# Test with inline data
mixtrain routing test config.json --data '{"user":{"tier":"premium"}}'

# Test with request file
mixtrain routing test config.json --request test_request.json

# Test with expectation
mixtrain routing test config.json --data '{"user":{"tier":"premium"}}' --expected premium_users
```

### Coverage Analysis

```bash
# Analyze rule coverage
mixtrain routing coverage config.json test_requests.json
```

### Explain Configuration

```bash
# Table format (default)
mixtrain routing explain config.json

# JSON format
mixtrain routing explain config.json --format json

# Markdown format
mixtrain routing explain config.json --format markdown
```

## Configuration Schema

### RoutingConfig

- `name`: Configuration name (required)
- `description`: Human-readable description
- `rules`: Array of routing rules
- `metadata`: Additional metadata

### RoutingRule

- `name`: Rule name (required)
- `description`: Rule description
- `priority`: Priority (higher = evaluated first)
- `is_enabled`: Whether rule is active
- `conditions`: Array of conditions (AND logic)
- `strategy`: Routing strategy
- `targets`: Array of target endpoints

### RoutingCondition

- `field`: Field path (dot notation supported)
- `operator`: Comparison operator
- `value`: Expected value (type depends on operator)
- `description`: Condition description

### RoutingTarget

- `provider`: Provider name (modal, fal, custom)
- `model_name`: Model identifier
- `endpoint`: HTTP endpoint URL
- `weight`: Routing weight (0.0-1.0)
- `label`: Optional label
- `timeout_ms`: Request timeout
- `retry_count`: Number of retries
- `headers`: Custom HTTP headers

## Best Practices

1. **Use descriptive names**: Name rules and targets clearly
2. **Set appropriate priorities**: Higher priority for more specific rules
3. **Add fallback rules**: Always have a catch-all rule
4. **Validate configurations**: Use the validator before deployment
5. **Test thoroughly**: Use coverage analysis to ensure all rules are tested
6. **Monitor performance**: Track routing decisions and performance
7. **Document conditions**: Add descriptions to complex conditions
8. **Version configurations**: Keep track of configuration changes

## Performance

The routing engine is designed for low-latency operation:

- **Condition evaluation**: O(1) for most operators
- **Rule matching**: O(n) where n is number of enabled rules
- **Target selection**: O(1) for single/shadow, O(n) for split/fallback
- **Memory usage**: Minimal, configurations are lightweight

Typical routing decisions complete in < 1ms for configurations with dozens of rules.

## Troubleshooting

### Common Issues

1. **Rules not matching**: Check condition fields and values
2. **Weight validation errors**: Ensure split strategy weights sum to 1.0
3. **Import errors**: Verify routing package installation
4. **Performance issues**: Reduce number of rules or simplify conditions

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
from loguru import logger

logger.add("routing.log", level="DEBUG")
```

### Validation Errors

Use the validator to catch configuration issues:

```python
from mixtrain.routing import RoutingValidator, ConfigurationLinter

errors = RoutingValidator.validate_config(config)
lint_results = ConfigurationLinter.lint_config(config)

print("Errors:", errors)
print("Warnings:", lint_results["warnings"])
print("Suggestions:", lint_results["suggestions"])
```