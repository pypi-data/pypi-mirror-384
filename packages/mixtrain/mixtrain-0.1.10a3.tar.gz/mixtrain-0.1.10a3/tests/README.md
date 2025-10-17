# Mixtrain Tests

This directory contains comprehensive tests for the mixtrain SDK and CLI.

## Test Structure

- `conftest.py` - Pytest configuration and shared fixtures
- `test_client.py` - Tests for the SDK client module
- `test_cli.py` - Tests for CLI commands and main application
- `test_config.py` - Tests for configuration utilities
- `test_dataset.py` - Tests for dataset module and commands
- `test_provider.py` - Tests for provider module and commands
- `test_secret.py` - Tests for secret module and commands
- `test_integration.py` - Integration tests for end-to-end workflows

## Running Tests

### Prerequisites

Install test dependencies:

```bash
cd mixtrain
uv pip install -e ".[test]"
```

### Run All Tests

```bash
cd mixtrain
uv run pytest
```

### Run Specific Test Categories

```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run only CLI tests
uv run pytest -m cli

# Run only SDK tests
uv run pytest -m sdk
```

### Run Specific Test Files

```bash
# Test client module
uv run pytest tests/test_client.py

# Test CLI commands
uv run pytest tests/test_cli.py

# Test configuration
uv run pytest tests/test_config.py
```

### Run Specific Test Functions

```bash
# Test specific function
uv run pytest tests/test_client.py::TestClientAPI::test_call_api_with_auth_token

# Test specific class
uv run pytest tests/test_cli.py::TestWorkspaceCommands
```

### Test Coverage

Run tests with coverage reporting:

```bash
uv run pytest --cov=mixtrain --cov-report=html --cov-report=term
```

## Test Configuration

Tests use the following configuration:

- **Temporary Config**: Each test uses a temporary configuration directory to avoid interfering with real config
- **Mock Authentication**: Tests use mock auth tokens and API keys
- **Mock API Calls**: All API calls are mocked to avoid hitting real endpoints
- **Sample Data**: Tests use generated sample CSV and Parquet files

## Key Fixtures

- `temp_config_dir`: Provides a temporary directory for config files
- `mock_config`: Sets up a mock configuration with test workspace and auth token
- `sample_csv_file`: Creates a temporary CSV file for testing
- `sample_parquet_file`: Creates a temporary Parquet file for testing
- `mock_platform_url`: Mocks the platform URL environment variable
- `mock_api_key`: Mocks the API key environment variable
- `cli_runner`: Provides a Typer CLI runner for testing commands

## Test Coverage Areas

### SDK Client Tests (`test_client.py`)
- API call functionality with different authentication methods
- Workspace operations (create, list, delete, switch)
- Dataset operations (create, list, delete, query, metadata)
- Provider operations (list, create, update, delete)
- Authentication methods (browser, token, GitHub, Google)
- Catalog and Iceberg table operations
- Error handling scenarios

### CLI Tests (`test_cli.py`)
- Main CLI functionality and help
- Login command
- Configuration management
- Workspace commands (create, list, delete)
- Dataset commands (create, list, delete, query, metadata)
- Provider commands (status, add, update, remove, info, models)
- Secret commands (list, get, set, delete, copy)
- Error handling and user interaction

### Configuration Tests (`test_config.py`)
- WorkspaceConfig model functionality
- Config singleton pattern
- Configuration file loading and saving
- Workspace management
- Platform URL configuration
- Authentication token management
- Error handling for corrupted config files

### Dataset Tests (`test_dataset.py`)
- File validation (CSV, Parquet, unsupported formats)
- DatasetBrowser TUI application
- Dataset CLI commands
- Interactive features (search, key events)
- Error handling

### Provider Tests (`test_provider.py`)
- Provider helper functions
- Provider CLI commands (status, add, update, remove, info, models)
- Dataset and model provider workflows
- Secret collection and validation
- Error handling

### Secret Tests (`test_secret.py`)
- Secret CLI commands (list, get, set, delete, copy)
- Interactive prompts and confirmations
- Hidden vs. shown secret values
- Update vs. create workflows
- Error handling

### Integration Tests (`test_integration.py`)
- Complete workspace lifecycle workflows
- Dataset management workflows
- Provider setup and configuration workflows
- Secret management workflows
- SDK client integration scenarios
- End-to-end data pipeline setup
- Configuration and data management integration
- Error propagation through different layers

## Best Practices

1. **No Real API Calls**: All tests mock API calls to avoid dependencies on external services
2. **Isolated Configuration**: Each test uses temporary configuration to avoid side effects
3. **Comprehensive Coverage**: Tests cover both success and error scenarios
4. **User-Facing Focus**: Tests prioritize user-facing functionality over internal implementation details
5. **Realistic Data**: Tests use realistic sample data and scenarios
6. **Clear Assertions**: Tests have clear, specific assertions about expected behavior
7. **Proper Cleanup**: Tests clean up temporary files and reset state appropriately

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you've installed the package in development mode: `uv pip install -e .`
2. **Missing Dependencies**: Install test dependencies: `uv pip install -e ".[test]"`
3. **Config Conflicts**: Tests should use temporary config directories, but if you see conflicts, check that `reset_config_singleton` fixture is working
4. **Mock Issues**: If mocks aren't working as expected, check that patches are applied in the correct order and scope

### Debug Mode

Run tests with more verbose output:

```bash
uv run pytest -v -s --tb=long
```

### Specific Test Debugging

Run a single test with full output:

```bash
uv run pytest tests/test_client.py::TestClientAPI::test_call_api_with_auth_token -v -s --tb=long
```
