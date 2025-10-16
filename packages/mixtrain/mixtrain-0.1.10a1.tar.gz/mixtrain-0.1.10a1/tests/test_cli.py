"""Tests for mixtrain CLI commands."""

import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from mixtrain.cli import app


class TestMainCLI:
    """Test main CLI functionality."""

    def test_cli_help(self, cli_runner):
        """Test CLI help command."""
        result = cli_runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout

    def test_login_command_success(self, cli_runner, mock_config):
        """Test successful login command."""
        with patch("mixtrain.client.authenticate_browser") as mock_auth:
            mock_auth.return_value = "test_token"
            
            with patch("mixtrain.cli.show_config") as mock_show:
                result = cli_runner.invoke(app, ["login"])
                
                assert result.exit_code == 0
                assert "✓" in result.stdout
                assert "Authenticated successfully!" in result.stdout
                mock_auth.assert_called_once()
                mock_show.assert_called_once()

    def test_login_command_failure(self, cli_runner, mock_config):
        """Test failed login command."""
        with patch("mixtrain.client.authenticate_browser") as mock_auth:
            mock_auth.side_effect = Exception("Authentication failed")
            
            result = cli_runner.invoke(app, ["login"])
            
            assert result.exit_code == 1
            assert "Login failed:" in result.stdout
            assert "Authentication failed" in result.stdout

    def test_config_show(self, cli_runner, mock_config):
        """Test config show command."""
        result = cli_runner.invoke(app, ["config", "--show"])
        
        assert result.exit_code == 0
        assert "test-workspace" in result.stdout

    def test_config_set_workspace(self, cli_runner, mock_config):
        """Test config set workspace command."""
        with patch("mixtrain.client.set_workspace") as mock_set:
            result = cli_runner.invoke(app, ["config", "--workspace", "other-workspace"])
            
            assert result.exit_code == 0
            assert "Switched to workspace: other-workspace" in result.stdout
            mock_set.assert_called_once_with("other-workspace")

    def test_config_set_workspace_error(self, cli_runner, mock_config):
        """Test config set workspace with error."""
        with patch("mixtrain.client.set_workspace") as mock_set:
            mock_set.side_effect = Exception("Workspace not found")
            
            result = cli_runner.invoke(app, ["config", "--workspace", "nonexistent"])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "Workspace not found" in result.stdout


class TestWorkspaceCommands:
    """Test workspace CLI commands."""

    def test_workspace_help(self, cli_runner):
        """Test workspace help command."""
        result = cli_runner.invoke(app, ["workspace"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout

    def test_workspace_list_success(self, cli_runner, mock_config):
        """Test successful workspace list command."""
        mock_workspaces = {
            "data": [
                {
                    "name": "workspace1",
                    "description": "First workspace",
                    "role": "owner",
                    "totalMembers": 1,
                    "created_at": "2023-01-01T00:00:00Z"
                },
                {
                    "name": "workspace2", 
                    "description": "Second workspace with a very long description that should be truncated",
                    "role": "member",
                    "totalMembers": 5,
                    "created_at": "2023-01-02T00:00:00Z"
                }
            ]
        }
        
        with patch("mixtrain.client.list_workspaces") as mock_list:
            mock_list.return_value = mock_workspaces
            
            result = cli_runner.invoke(app, ["workspace", "list"])
            
            assert result.exit_code == 0
            assert "Your Workspaces:" in result.stdout
            assert "workspace1" in result.stdout
            assert "workspace2" in result.stdout
            assert "owner" in result.stdout
            assert "member" in result.stdout

    def test_workspace_list_empty(self, cli_runner, mock_config):
        """Test workspace list with no workspaces."""
        with patch("mixtrain.client.list_workspaces") as mock_list:
            mock_list.return_value = {"data": []}
            
            result = cli_runner.invoke(app, ["workspace", "list"])
            
            assert result.exit_code == 0
            assert "No workspaces found" in result.stdout
            assert "mixtrain workspace create" in result.stdout

    def test_workspace_list_error(self, cli_runner, mock_config):
        """Test workspace list with error."""
        with patch("mixtrain.client.list_workspaces") as mock_list:
            mock_list.side_effect = Exception("API error")
            
            result = cli_runner.invoke(app, ["workspace", "list"])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "API error" in result.stdout

    def test_workspace_create_success(self, cli_runner, mock_config):
        """Test successful workspace creation."""
        mock_result = {
            "data": {
                "name": "new-workspace",
                "description": "New workspace"
            }
        }
        
        with patch("mixtrain.client.create_workspace") as mock_create:
            mock_create.return_value = mock_result
            
            with patch("mixtrain.client.set_workspace") as mock_set:
                result = cli_runner.invoke(app, [
                    "workspace", "create", "new-workspace",
                    "--description", "New workspace"
                ])
                
                assert result.exit_code == 0
                assert "✓" in result.stdout
                assert "Successfully created workspace 'new-workspace'" in result.stdout
                assert "Switched to workspace: new-workspace" in result.stdout
                mock_create.assert_called_once_with("new-workspace", "New workspace")
                mock_set.assert_called_once_with("new-workspace")

    def test_workspace_create_error(self, cli_runner, mock_config):
        """Test workspace creation with error."""
        with patch("mixtrain.client.create_workspace") as mock_create:
            mock_create.side_effect = Exception("Creation failed")
            
            result = cli_runner.invoke(app, ["workspace", "create", "new-workspace"])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "Creation failed" in result.stdout

    def test_workspace_delete_with_confirmation(self, cli_runner, mock_config):
        """Test workspace deletion with confirmation."""
        with patch("mixtrain.client.delete_workspace") as mock_delete:
            result = cli_runner.invoke(app, [
                "workspace", "delete", "test-workspace", "--yes"
            ])
            
            assert result.exit_code == 0
            assert "✓" in result.stdout
            assert "Successfully deleted workspace 'test-workspace'" in result.stdout
            mock_delete.assert_called_once_with("test-workspace")

    def test_workspace_delete_cancelled(self, cli_runner, mock_config):
        """Test workspace deletion cancelled by user."""
        with patch("typer.confirm") as mock_confirm:
            mock_confirm.return_value = False
            
            result = cli_runner.invoke(app, ["workspace", "delete", "test-workspace"])
            
            assert result.exit_code == 0
            assert "Deletion cancelled" in result.stdout

    def test_workspace_delete_error(self, cli_runner, mock_config):
        """Test workspace deletion with error."""
        with patch("mixtrain.client.delete_workspace") as mock_delete:
            mock_delete.side_effect = Exception("Deletion failed")
            
            result = cli_runner.invoke(app, [
                "workspace", "delete", "test-workspace", "--yes"
            ])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "Deletion failed" in result.stdout


class TestDatasetCommands:
    """Test dataset CLI commands."""

    def test_dataset_help(self, cli_runner):
        """Test dataset help command."""
        result = cli_runner.invoke(app, ["dataset"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout

    def test_dataset_create_success(self, cli_runner, mock_config, sample_csv_file):
        """Test successful dataset creation."""
        with patch("mixtrain.client.create_dataset_from_file") as mock_create:
            result = cli_runner.invoke(app, [
                "dataset", "create", "test-dataset", sample_csv_file,
                "--description", "Test dataset"
            ])
            
            assert result.exit_code == 0
            assert "Dataset 'test-dataset' created successfully" in result.stdout
            assert "Browse with: mixtrain dataset browse test-dataset" in result.stdout
            mock_create.assert_called_once_with("test-dataset", sample_csv_file, "Test dataset")

    def test_dataset_create_file_not_found(self, cli_runner, mock_config):
        """Test dataset creation with non-existent file."""
        result = cli_runner.invoke(app, [
            "dataset", "create", "test-dataset", "/nonexistent/file.csv"
        ])
        
        assert result.exit_code == 1
        assert "File /nonexistent/file.csv not found" in result.stdout

    def test_dataset_create_unsupported_format(self, cli_runner, mock_config):
        """Test dataset creation with unsupported file format."""
        with patch("os.path.exists", return_value=True):
            result = cli_runner.invoke(app, [
                "dataset", "create", "test-dataset", "test.txt"
            ])
            
            assert result.exit_code == 1
            assert "Only parquet and CSV files are supported" in result.stdout

    def test_dataset_create_error(self, cli_runner, mock_config, sample_csv_file):
        """Test dataset creation with API error."""
        with patch("mixtrain.client.create_dataset_from_file") as mock_create:
            mock_create.side_effect = Exception("API error")
            
            result = cli_runner.invoke(app, [
                "dataset", "create", "test-dataset", sample_csv_file
            ])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "API error" in result.stdout

    def test_dataset_list_success(self, cli_runner, mock_config):
        """Test successful dataset listing."""
        mock_data = {
            "tables": [
                {
                    "name": "dataset1",
                    "namespace": "test-workspace",
                    "description": "First dataset"
                },
                {
                    "name": "dataset2",
                    "namespace": "test-workspace", 
                    "description": "Second dataset"
                }
            ]
        }
        
        with patch("mixtrain.client.list_datasets") as mock_list:
            mock_list.return_value = mock_data
            
            result = cli_runner.invoke(app, ["dataset", "list"])
            
            assert result.exit_code == 0
            assert "dataset1" in result.stdout
            assert "dataset2" in result.stdout
            assert "First dataset" in result.stdout

    def test_dataset_list_empty(self, cli_runner, mock_config):
        """Test dataset listing with no datasets."""
        with patch("mixtrain.client.list_datasets") as mock_list:
            mock_list.return_value = {}
            
            result = cli_runner.invoke(app, ["dataset", "list"])
            
            assert result.exit_code == 0
            assert "No datasets found" in result.stdout

    def test_dataset_list_error(self, cli_runner, mock_config):
        """Test dataset listing with error."""
        with patch("mixtrain.client.list_datasets") as mock_list:
            mock_list.side_effect = Exception("API error")
            
            result = cli_runner.invoke(app, ["dataset", "list"])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "API error" in result.stdout

    def test_dataset_delete_success(self, cli_runner, mock_config):
        """Test successful dataset deletion."""
        with patch("mixtrain.client.delete_dataset") as mock_delete:
            result = cli_runner.invoke(app, ["dataset", "delete", "test-dataset"])
            
            assert result.exit_code == 0
            assert "Table test-dataset deleted successfully" in result.stdout
            mock_delete.assert_called_once_with("test-dataset")

    def test_dataset_delete_error(self, cli_runner, mock_config):
        """Test dataset deletion with error."""
        with patch("mixtrain.client.delete_dataset") as mock_delete:
            mock_delete.side_effect = Exception("Deletion failed")
            
            result = cli_runner.invoke(app, ["dataset", "delete", "test-dataset"])
            
            assert result.exit_code == 1
            assert "Deletion failed" in result.stdout

    def test_dataset_query_success(self, cli_runner, mock_config):
        """Test successful dataset query."""
        mock_table = Mock()
        mock_scan = Mock()
        mock_duckdb = Mock()
        mock_arrow_table = Mock()
        
        # Setup mock chain
        mock_table.scan.return_value = mock_scan
        mock_scan.to_duckdb.return_value = mock_duckdb
        mock_duckdb.execute.return_value = mock_duckdb
        mock_duckdb.fetch_arrow_table.return_value = mock_arrow_table
        mock_arrow_table.to_pylist.return_value = [{"id": 1, "name": "test"}]
        mock_arrow_table.schema.names = ["id", "name"]
        
        with patch("mixtrain.client.get_dataset") as mock_get:
            mock_get.return_value = mock_table
            
            with patch("mixtrain.dataset.DatasetBrowser") as mock_browser:
                mock_app = Mock()
                mock_browser.return_value = mock_app
                
                result = cli_runner.invoke(app, [
                    "dataset", "query", "test-dataset", "SELECT * FROM test-dataset LIMIT 10"
                ])
                
                assert result.exit_code == 0
                mock_get.assert_called_once_with("test-dataset")
                mock_browser.assert_called_once()
                mock_app.run.assert_called_once()

    def test_dataset_query_default_sql(self, cli_runner, mock_config):
        """Test dataset query with default SQL."""
        mock_table = Mock()
        mock_scan = Mock()
        mock_duckdb = Mock()
        mock_arrow_table = Mock()
        
        # Setup mock chain
        mock_table.scan.return_value = mock_scan
        mock_scan.to_duckdb.return_value = mock_duckdb
        mock_duckdb.execute.return_value = mock_duckdb
        mock_duckdb.fetch_arrow_table.return_value = mock_arrow_table
        mock_arrow_table.to_pylist.return_value = []
        mock_arrow_table.schema.names = []
        
        with patch("mixtrain.client.get_dataset") as mock_get:
            mock_get.return_value = mock_table
            
            with patch("mixtrain.dataset.DatasetBrowser") as mock_browser:
                mock_app = Mock()
                mock_browser.return_value = mock_app
                
                result = cli_runner.invoke(app, ["dataset", "query", "test-dataset"])
                
                assert result.exit_code == 0
                # Verify default SQL was used
                mock_duckdb.execute.assert_called_with("SELECT * FROM test-dataset LIMIT 100")

    def test_dataset_query_error(self, cli_runner, mock_config):
        """Test dataset query with error."""
        with patch("mixtrain.client.get_dataset") as mock_get:
            mock_get.side_effect = Exception("Query failed")
            
            result = cli_runner.invoke(app, ["dataset", "query", "test-dataset"])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "Query failed" in result.stdout

    def test_dataset_metadata_success(self, cli_runner, mock_config):
        """Test successful dataset metadata retrieval."""
        mock_metadata = {
            "table_name": "test-dataset",
            "format_version": 2,
            "table_uuid": "test-uuid-123",
            "location": "s3://bucket/path",
            "schema": [
                {"name": "id", "type": "bigint"},
                {"name": "name", "type": "string"}
            ]
        }
        
        with patch("mixtrain.client.get_dataset_metadata") as mock_get:
            mock_get.return_value = mock_metadata
            
            result = cli_runner.invoke(app, ["dataset", "metadata", "test-dataset"])
            
            assert result.exit_code == 0
            assert "Dataset: test-dataset" in result.stdout
            assert "Format Version: 2" in result.stdout
            assert "Dataset UUID: test-uuid-123" in result.stdout
            assert "Location: s3://bucket/path" in result.stdout
            assert "Schema:" in result.stdout
            assert "id" in result.stdout
            assert "bigint" in result.stdout

    def test_dataset_metadata_error(self, cli_runner, mock_config):
        """Test dataset metadata with error."""
        with patch("mixtrain.client.get_dataset_metadata") as mock_get:
            mock_get.side_effect = Exception("Metadata failed")
            
            result = cli_runner.invoke(app, ["dataset", "metadata", "test-dataset"])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "Metadata failed" in result.stdout


class TestProviderCommands:
    """Test provider CLI commands."""

    def test_provider_help(self, cli_runner):
        """Test provider help command."""
        result = cli_runner.invoke(app, ["provider"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout

    def test_provider_status_success(self, cli_runner, mock_config):
        """Test successful provider status command."""
        dataset_data = {
            "available_providers": [
                {
                    "provider_type": "apache_iceberg",
                    "display_name": "Apache Iceberg",
                    "description": "Apache Iceberg data lake format",
                    "status": "available"
                }
            ],
            "onboarded_providers": [
                {
                    "id": 1,
                    "provider_type": "apache_iceberg",
                    "display_name": "Apache Iceberg",
                    "created_at": "2023-01-01T00:00:00Z"
                }
            ]
        }
        
        model_data = {
            "available_providers": [
                {
                    "provider_type": "openai",
                    "display_name": "OpenAI",
                    "description": "OpenAI language models",
                    "status": "available"
                }
            ],
            "onboarded_providers": []
        }
        
        with patch("mixtrain.client.list_dataset_providers") as mock_dataset:
            mock_dataset.return_value = dataset_data
            
            with patch("mixtrain.client.list_model_providers") as mock_model:
                mock_model.return_value = model_data
                
                result = cli_runner.invoke(app, ["provider", "status"])
                
                assert result.exit_code == 0
                assert "Available Dataset Providers:" in result.stdout
                assert "Apache Iceberg" in result.stdout
                assert "Available Model Providers:" in result.stdout
                assert "OpenAI" in result.stdout
                assert "Configured Dataset Providers:" in result.stdout

    def test_provider_status_no_providers(self, cli_runner, mock_config):
        """Test provider status with no configured providers."""
        empty_data = {
            "available_providers": [],
            "onboarded_providers": []
        }
        
        with patch("mixtrain.client.list_dataset_providers") as mock_dataset:
            mock_dataset.return_value = empty_data
            
            with patch("mixtrain.client.list_model_providers") as mock_model:
                mock_model.return_value = empty_data
                
                result = cli_runner.invoke(app, ["provider", "status"])
                
                assert result.exit_code == 0
                assert "No providers configured yet" in result.stdout
                assert "mixtrain provider add" in result.stdout

    def test_provider_status_error(self, cli_runner, mock_config):
        """Test provider status with error."""
        with patch("mixtrain.client.list_dataset_providers") as mock_dataset:
            mock_dataset.side_effect = Exception("API error")
            
            result = cli_runner.invoke(app, ["provider", "status"])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "API error" in result.stdout


class TestSecretCommands:
    """Test secret CLI commands."""

    def test_secret_help(self, cli_runner):
        """Test secret help command."""
        result = cli_runner.invoke(app, ["secret"])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout

    def test_secret_list_success(self, cli_runner, mock_config):
        """Test successful secret list command."""
        mock_secrets = [
            {
                "name": "API_KEY",
                "description": "OpenAI API Key",
                "created_at": "2023-01-01T00:00:00Z",
                "created_by": "user@example.com"
            },
            {
                "name": "DATABASE_URL",
                "description": "Database connection string",
                "created_at": "2023-01-02T00:00:00Z",
                "created_by": "user@example.com"
            }
        ]
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_response = Mock()
            mock_response.json.return_value = mock_secrets
            mock_call.return_value = mock_response
            
            result = cli_runner.invoke(app, ["secret", "list"])
            
            assert result.exit_code == 0
            assert "API_KEY" in result.stdout
            assert "DATABASE_URL" in result.stdout
            assert "OpenAI API Key" in result.stdout

    def test_secret_list_empty(self, cli_runner, mock_config):
        """Test secret list with no secrets."""
        with patch("mixtrain.client.call_api") as mock_call:
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_call.return_value = mock_response
            
            result = cli_runner.invoke(app, ["secret", "list"])
            
            assert result.exit_code == 0
            assert "No secrets found" in result.stdout
            assert "mixtrain secret set" in result.stdout

    def test_secret_get_success(self, cli_runner, mock_config):
        """Test successful secret get command."""
        mock_secret = {
            "name": "API_KEY",
            "description": "OpenAI API Key",
            "value": "sk-test-key",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "created_by": "user@example.com"
        }
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_response = Mock()
            mock_response.json.return_value = mock_secret
            mock_call.return_value = mock_response
            
            result = cli_runner.invoke(app, ["secret", "get", "API_KEY", "--show"])
            
            assert result.exit_code == 0
            assert "Secret 'API_KEY':" in result.stdout
            assert "OpenAI API Key" in result.stdout
            assert "sk-test-key" in result.stdout

    def test_secret_get_hidden(self, cli_runner, mock_config):
        """Test secret get command without showing value."""
        mock_secret = {
            "name": "API_KEY",
            "description": "OpenAI API Key",
            "value": "sk-test-key",
            "created_at": "2023-01-01T00:00:00Z",
            "created_by": "user@example.com"
        }
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_response = Mock()
            mock_response.json.return_value = mock_secret
            mock_call.return_value = mock_response
            
            result = cli_runner.invoke(app, ["secret", "get", "API_KEY"])
            
            assert result.exit_code == 0
            assert "Secret 'API_KEY':" in result.stdout
            assert "Hidden (use --show to display)" in result.stdout
            assert "sk-test-key" not in result.stdout

    def test_secret_get_not_found(self, cli_runner, mock_config):
        """Test secret get command with non-existent secret."""
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.side_effect = Exception("404")
            
            result = cli_runner.invoke(app, ["secret", "get", "NONEXISTENT"])
            
            assert result.exit_code == 1
            assert "Secret 'NONEXISTENT' not found" in result.stdout
