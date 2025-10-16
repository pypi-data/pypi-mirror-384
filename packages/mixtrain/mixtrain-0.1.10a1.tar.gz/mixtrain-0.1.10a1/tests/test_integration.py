"""Integration tests for mixtrain SDK and CLI workflows."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from mixtrain.cli import app
from mixtrain import client


class TestWorkspaceWorkflow:
    """Test end-to-end workspace management workflows."""

    def test_workspace_lifecycle(self, mock_config, mock_platform_url):
        """Test complete workspace lifecycle: create, list, switch, delete."""
        runner = CliRunner()
        
        # Mock API responses for workspace operations
        create_response = {"data": {"name": "integration-test-workspace", "description": "Test workspace"}}
        list_response = {
            "data": [
                {
                    "name": "integration-test-workspace",
                    "description": "Test workspace",
                    "role": "owner",
                    "totalMembers": 1,
                    "created_at": "2023-01-01T00:00:00Z"
                }
            ]
        }
        
        with patch("mixtrain.client.create_workspace") as mock_create:
            mock_create.return_value = create_response
            
            with patch("mixtrain.client.set_workspace") as mock_set:
                with patch("mixtrain.client.list_workspaces") as mock_list:
                    mock_list.return_value = list_response
                    
                    with patch("mixtrain.client.delete_workspace") as mock_delete:
                        # 1. Create workspace
                        result = runner.invoke(app, [
                            "workspace", "create", "integration-test-workspace",
                            "--description", "Test workspace"
                        ])
                        assert result.exit_code == 0
                        assert "Successfully created workspace" in result.stdout
                        
                        # 2. List workspaces
                        result = runner.invoke(app, ["workspace", "list"])
                        assert result.exit_code == 0
                        assert "integration-test-workspace" in result.stdout
                        
                        # 3. Switch workspace (via config)
                        result = runner.invoke(app, ["config", "--workspace", "integration-test-workspace"])
                        assert result.exit_code == 0
                        assert "Switched to workspace" in result.stdout
                        
                        # 4. Delete workspace
                        result = runner.invoke(app, [
                            "workspace", "delete", "integration-test-workspace", "--yes"
                        ])
                        assert result.exit_code == 0
                        assert "Successfully deleted workspace" in result.stdout

    def test_workspace_error_handling(self, mock_config, mock_platform_url):
        """Test workspace operations error handling."""
        runner = CliRunner()
        
        # Test creating workspace with duplicate name
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.side_effect = Exception("Workspace already exists")
            
            result = runner.invoke(app, ["workspace", "create", "existing-workspace"])
            assert result.exit_code == 1
            assert "Workspace already exists" in result.stdout
        
        # Test deleting non-existent workspace
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.side_effect = Exception("Workspace not found")
            
            result = runner.invoke(app, ["workspace", "delete", "nonexistent", "--yes"])
            assert result.exit_code == 1
            assert "Workspace not found" in result.stdout


class TestDatasetWorkflow:
    """Test end-to-end dataset management workflows."""

    def test_dataset_lifecycle(self, mock_config, mock_platform_url, sample_csv_file):
        """Test complete dataset lifecycle: create, list, query, metadata, delete."""
        runner = CliRunner()
        
        # Mock API responses
        list_response = {
            "tables": [
                {
                    "name": "integration-test-dataset",
                    "namespace": "test-workspace",
                    "description": "Test dataset"
                }
            ]
        }
        
        metadata_response = {
            "table_name": "integration-test-dataset",
            "format_version": 2,
            "table_uuid": "test-uuid",
            "location": "s3://bucket/path",
            "schema": [
                {"name": "id", "type": "bigint"},
                {"name": "name", "type": "string"},
                {"name": "value", "type": "bigint"}
            ]
        }
        
        # Mock dataset table for query
        mock_table = Mock()
        mock_scan = Mock()
        mock_duckdb = Mock()
        mock_arrow_table = Mock()
        
        mock_table.scan.return_value = mock_scan
        mock_scan.to_duckdb.return_value = mock_duckdb
        mock_duckdb.execute.return_value = mock_duckdb
        mock_duckdb.fetch_arrow_table.return_value = mock_arrow_table
        mock_arrow_table.to_pylist.return_value = [{"id": 1, "name": "test", "value": 100}]
        mock_arrow_table.schema.names = ["id", "name", "value"]
        
        with patch("mixtrain.client.create_dataset_from_file") as mock_create:
            with patch("mixtrain.client.list_datasets") as mock_list:
                mock_list.return_value = list_response
                
                with patch("mixtrain.client.get_dataset") as mock_get:
                    mock_get.return_value = mock_table
                    
                    with patch("mixtrain.client.get_dataset_metadata") as mock_metadata:
                        mock_metadata.return_value = metadata_response
                        
                        with patch("mixtrain.client.delete_dataset") as mock_delete:
                            with patch("mixtrain.dataset.DatasetBrowser") as mock_browser:
                                mock_app = Mock()
                                mock_browser.return_value = mock_app
                                
                                # 1. Create dataset
                                result = runner.invoke(app, [
                                    "dataset", "create", "integration-test-dataset", sample_csv_file,
                                    "--description", "Test dataset"
                                ])
                                assert result.exit_code == 0
                                assert "Dataset 'integration-test-dataset' created successfully" in result.stdout
                                
                                # 2. List datasets
                                result = runner.invoke(app, ["dataset", "list"])
                                assert result.exit_code == 0
                                assert "integration-test-dataset" in result.stdout
                                
                                # 3. Query dataset
                                result = runner.invoke(app, [
                                    "dataset", "query", "integration-test-dataset",
                                    "SELECT * FROM integration-test-dataset LIMIT 10"
                                ])
                                assert result.exit_code == 0
                                mock_browser.assert_called_once()
                                
                                # 4. Get metadata
                                result = runner.invoke(app, ["dataset", "metadata", "integration-test-dataset"])
                                assert result.exit_code == 0
                                assert "Dataset: integration-test-dataset" in result.stdout
                                assert "Schema:" in result.stdout
                                
                                # 5. Delete dataset
                                result = runner.invoke(app, ["dataset", "delete", "integration-test-dataset"])
                                assert result.exit_code == 0
                                assert "Table integration-test-dataset deleted successfully" in result.stdout

    def test_dataset_file_validation_workflow(self, mock_config):
        """Test dataset creation with various file types and validation."""
        runner = CliRunner()
        
        # Test unsupported file format
        result = runner.invoke(app, ["dataset", "create", "test-dataset", "test.txt"])
        assert result.exit_code == 1
        assert "Only parquet and CSV files are supported" in result.stdout
        
        # Test non-existent file
        result = runner.invoke(app, ["dataset", "create", "test-dataset", "/nonexistent/file.csv"])
        assert result.exit_code == 1
        assert "File /nonexistent/file.csv not found" in result.stdout


class TestProviderWorkflow:
    """Test end-to-end provider management workflows."""

    def test_provider_lifecycle(self, mock_config, mock_platform_url):
        """Test complete provider lifecycle: list, add, update, remove."""
        runner = CliRunner()
        
        # Mock provider data
        initial_data = {
            "available_providers": [
                {
                    "provider_type": "apache_iceberg",
                    "display_name": "Apache Iceberg",
                    "description": "Apache Iceberg data lake format",
                    "status": "available",
                    "secret_requirements": [
                        {
                            "name": "CATALOG_URI",
                            "display_name": "Catalog URI",
                            "description": "PostgreSQL connection string",
                            "is_required": True
                        }
                    ]
                }
            ],
            "onboarded_providers": []
        }
        
        onboarded_data = {
            "available_providers": initial_data["available_providers"],
            "onboarded_providers": [
                {
                    "id": 1,
                    "provider_type": "apache_iceberg",
                    "display_name": "Apache Iceberg",
                    "created_at": "2023-01-01T00:00:00Z"
                }
            ]
        }
        
        with patch("mixtrain.client.list_dataset_providers") as mock_list_dataset:
            with patch("mixtrain.client.list_model_providers") as mock_list_model:
                mock_list_model.return_value = {"available_providers": [], "onboarded_providers": []}
                
                with patch("mixtrain.client.create_dataset_provider") as mock_create:
                    mock_create.return_value = {"id": 1, "display_name": "Apache Iceberg"}
                    
                    with patch("mixtrain.client.update_dataset_provider") as mock_update:
                        mock_update.return_value = {"display_name": "Apache Iceberg"}
                        
                        with patch("mixtrain.client.delete_dataset_provider") as mock_delete:
                            with patch("typer.prompt") as mock_prompt:
                                mock_prompt.return_value = "postgresql://localhost:5432/catalog"
                                
                                with patch("typer.confirm") as mock_confirm:
                                    mock_confirm.return_value = True
                                    
                                    # 1. Initial status (no providers)
                                    mock_list_dataset.return_value = initial_data
                                    result = runner.invoke(app, ["provider", "status"])
                                    assert result.exit_code == 0
                                    assert "No providers configured yet" in result.stdout
                                    
                                    # 2. Add provider
                                    result = runner.invoke(app, ["provider", "add", "apache_iceberg"])
                                    assert result.exit_code == 0
                                    assert "Successfully added Apache Iceberg!" in result.stdout
                                    
                                    # 3. Status with onboarded provider
                                    mock_list_dataset.return_value = onboarded_data
                                    result = runner.invoke(app, ["provider", "status"])
                                    assert result.exit_code == 0
                                    assert "Configured Dataset Providers:" in result.stdout
                                    
                                    # 4. Update provider
                                    result = runner.invoke(app, ["provider", "update", "1"])
                                    assert result.exit_code == 0
                                    assert "Successfully updated Apache Iceberg!" in result.stdout
                                    
                                    # 5. Remove provider
                                    result = runner.invoke(app, ["provider", "remove", "1"])
                                    assert result.exit_code == 0
                                    assert "Successfully removed Apache Iceberg!" in result.stdout

    def test_provider_info_workflow(self, mock_config, mock_platform_url):
        """Test provider information retrieval workflow."""
        runner = CliRunner()
        
        provider_data = {
            "available_providers": [
                {
                    "provider_type": "apache_iceberg",
                    "display_name": "Apache Iceberg",
                    "description": "Apache Iceberg data lake format",
                    "status": "available",
                    "website_url": "https://iceberg.apache.org",
                    "onboarding_instructions": "Configure your catalog connection",
                    "secret_requirements": [
                        {
                            "display_name": "Catalog URI",
                            "description": "PostgreSQL connection string",
                            "is_required": True
                        }
                    ]
                }
            ],
            "onboarded_providers": []
        }
        
        with patch("mixtrain.client.list_dataset_providers") as mock_list_dataset:
            mock_list_dataset.return_value = provider_data
            
            with patch("mixtrain.client.list_model_providers") as mock_list_model:
                mock_list_model.return_value = {"available_providers": [], "onboarded_providers": []}
                
                result = runner.invoke(app, ["provider", "info", "apache_iceberg"])
                
                assert result.exit_code == 0
                assert "Apache Iceberg (dataset provider)" in result.stdout
                assert "Website: https://iceberg.apache.org" in result.stdout
                assert "Required Configuration:" in result.stdout
                assert "Setup Instructions:" in result.stdout


class TestSecretWorkflow:
    """Test end-to-end secret management workflows."""

    def test_secret_lifecycle(self, mock_config, mock_platform_url):
        """Test complete secret lifecycle: create, list, get, update, copy, delete."""
        runner = CliRunner()
        
        # Mock secret data
        secret_data = {
            "name": "TEST_SECRET",
            "description": "Test secret",
            "value": "secret_value",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "created_by": "user@example.com"
        }
        
        secrets_list = [secret_data]
        
        with patch("mixtrain.client.call_api") as mock_call:
            # Setup different responses for different API calls
            def api_side_effect(method, path, **kwargs):
                mock_response = Mock()
                
                if method == "GET" and path.endswith("/secrets/"):
                    mock_response.json.return_value = secrets_list
                elif method == "GET" and "TEST_SECRET" in path:
                    mock_response.json.return_value = secret_data
                elif method == "GET" and "COPIED_SECRET" in path:
                    mock_response.json.return_value = {**secret_data, "name": "COPIED_SECRET"}
                elif method == "POST":
                    mock_response.json.return_value = {"success": True}
                elif method == "PUT":
                    mock_response.json.return_value = {"success": True}
                elif method == "DELETE":
                    mock_response.json.return_value = {"success": True}
                else:
                    # For checking if secret exists during creation
                    raise Exception("404")
                
                return mock_response
            
            mock_call.side_effect = api_side_effect
            
            with patch("rich.prompt.Prompt.ask") as mock_prompt:
                mock_prompt.side_effect = ["secret_value", "Test secret description"]
                
                with patch("rich.prompt.Confirm.ask") as mock_confirm:
                    mock_confirm.return_value = True
                    
                    # 1. Create secret
                    result = runner.invoke(app, ["secret", "set", "TEST_SECRET"])
                    assert result.exit_code == 0
                    assert "Secret 'TEST_SECRET' created successfully!" in result.stdout
                    
                    # 2. List secrets
                    result = runner.invoke(app, ["secret", "list"])
                    assert result.exit_code == 0
                    assert "TEST_SECRET" in result.stdout
                    
                    # 3. Get secret (hidden)
                    result = runner.invoke(app, ["secret", "get", "TEST_SECRET"])
                    assert result.exit_code == 0
                    assert "Secret 'TEST_SECRET':" in result.stdout
                    assert "Hidden" in result.stdout
                    
                    # 4. Get secret (shown)
                    result = runner.invoke(app, ["secret", "get", "TEST_SECRET", "--show"])
                    assert result.exit_code == 0
                    assert "secret_value" in result.stdout
                    
                    # 5. Update secret
                    result = runner.invoke(app, [
                        "secret", "set", "TEST_SECRET", "new_value",
                        "--description", "Updated description", "--update"
                    ])
                    assert result.exit_code == 0
                    assert "Secret 'TEST_SECRET' updated successfully!" in result.stdout
                    
                    # 6. Copy secret
                    result = runner.invoke(app, [
                        "secret", "copy", "TEST_SECRET", "COPIED_SECRET",
                        "--description", "Copied secret"
                    ])
                    assert result.exit_code == 0
                    assert "Secret 'TEST_SECRET' copied to 'COPIED_SECRET' successfully!" in result.stdout
                    
                    # 7. Delete secret
                    result = runner.invoke(app, ["secret", "delete", "TEST_SECRET"])
                    assert result.exit_code == 0
                    assert "Secret 'TEST_SECRET' deleted successfully!" in result.stdout


class TestSDKClientIntegration:
    """Test SDK client integration scenarios."""

    def test_authentication_flow(self, mock_config, mock_platform_url):
        """Test authentication flow with different methods."""
        # Test API key authentication
        with patch.dict(os.environ, {"MIXTRAIN_API_KEY": "mix-test-key"}):
            with patch("mixtrain.client._call_api") as mock_call:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"data": "test"}
                mock_call.return_value = mock_response
                
                response = client.call_api("GET", "/test")
                assert response.json() == {"data": "test"}
        
        # Test JWT token authentication
        with patch("mixtrain.client._call_api") as mock_call:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": "test"}
            mock_call.return_value = mock_response
            
            response = client.call_api("GET", "/test")
            assert response.json() == {"data": "test"}

    def test_workspace_dataset_integration(self, mock_config, mock_platform_url, sample_csv_file):
        """Test integration between workspace and dataset operations."""
        # Create workspace
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {
                "data": {"name": "integration-workspace", "description": "Integration test"}
            }
            
            result = client.create_workspace("integration-workspace", "Integration test")
            assert result["data"]["name"] == "integration-workspace"
        
        # Switch to workspace
        client.set_workspace("integration-workspace")
        
        # Create dataset in workspace
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {"data": {"name": "test-dataset"}}
            
            result = client.create_dataset_from_file("test-dataset", sample_csv_file, "Test dataset")
            assert result["data"]["name"] == "test-dataset"
        
        # List datasets in workspace
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {
                "tables": [{"name": "test-dataset", "namespace": "integration-workspace"}]
            }
            
            result = client.list_datasets()
            assert len(result["tables"]) == 1
            assert result["tables"][0]["name"] == "test-dataset"

    def test_provider_dataset_integration(self, mock_config, mock_platform_url):
        """Test integration between provider setup and dataset operations."""
        # Setup dataset provider
        secrets = {"CATALOG_URI": "postgresql://localhost:5432/catalog"}
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {
                "id": 1,
                "provider_type": "apache_iceberg",
                "display_name": "Apache Iceberg"
            }
            
            result = client.create_dataset_provider("apache_iceberg", secrets)
            assert result["id"] == 1
        
        # Mock catalog operations
        with patch("mixtrain.client.get_catalog") as mock_get_catalog:
            mock_catalog = Mock()
            mock_get_catalog.return_value = mock_catalog
            
            with patch("mixtrain.client.get_dataset") as mock_get_dataset:
                mock_table = Mock()
                mock_get_dataset.return_value = mock_table
                
                # Get dataset using configured provider
                table = client.get_dataset("test-dataset")
                assert table == mock_table
                mock_get_catalog.assert_called_once_with("test-workspace")

    def test_error_propagation(self, mock_config, mock_platform_url):
        """Test error propagation through different layers."""
        # Test API error propagation
        with patch("mixtrain.client._call_api") as mock_call:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"detail": "Bad request"}
            mock_response.text = "Bad request"
            mock_call.return_value = mock_response
            
            with pytest.raises(Exception, match="Bad request"):
                client.call_api("GET", "/test")
        
        # Test network error propagation
        with patch("mixtrain.client._call_api") as mock_call:
            import httpx
            mock_call.side_effect = httpx.RequestError("Network error")
            
            with pytest.raises(httpx.RequestError):
                client.call_api("GET", "/test")


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows combining multiple components."""

    def test_complete_data_pipeline_setup(self, mock_config, mock_platform_url, sample_csv_file):
        """Test setting up a complete data pipeline from scratch."""
        runner = CliRunner()
        
        # Mock all required API responses
        workspace_response = {"data": {"name": "data-pipeline-workspace"}}
        provider_response = {"id": 1, "display_name": "Apache Iceberg"}
        dataset_response = {"data": {"name": "pipeline-dataset"}}
        
        with patch("mixtrain.client.create_workspace") as mock_create_workspace:
            mock_create_workspace.return_value = workspace_response
            
            with patch("mixtrain.client.set_workspace") as mock_set_workspace:
                with patch("mixtrain.client.create_dataset_provider") as mock_create_provider:
                    mock_create_provider.return_value = provider_response
                    
                    with patch("mixtrain.client.create_dataset_from_file") as mock_create_dataset:
                        mock_create_dataset.return_value = dataset_response
                        
                        with patch("typer.prompt") as mock_prompt:
                            mock_prompt.return_value = "postgresql://localhost:5432/catalog"
                            
                            # 1. Create workspace
                            result = runner.invoke(app, [
                                "workspace", "create", "data-pipeline-workspace",
                                "--description", "Data pipeline workspace"
                            ])
                            assert result.exit_code == 0
                            
                            # 2. Add dataset provider
                            result = runner.invoke(app, ["provider", "add", "apache_iceberg"])
                            assert result.exit_code == 0
                            
                            # 3. Create dataset
                            result = runner.invoke(app, [
                                "dataset", "create", "pipeline-dataset", sample_csv_file,
                                "--description", "Pipeline dataset"
                            ])
                            assert result.exit_code == 0
                            
                            # Verify all operations were called
                            mock_create_workspace.assert_called_once()
                            mock_set_workspace.assert_called_once()
                            mock_create_provider.assert_called_once()
                            mock_create_dataset.assert_called_once()

    def test_configuration_and_data_management(self, mock_config, mock_platform_url):
        """Test configuration management combined with data operations."""
        runner = CliRunner()
        
        # Test switching workspaces and performing operations
        with patch("mixtrain.client.set_workspace") as mock_set:
            with patch("mixtrain.client.list_datasets") as mock_list:
                mock_list.return_value = {
                    "tables": [{"name": "workspace1-dataset", "namespace": "workspace1"}]
                }
                
                # Switch to workspace1
                result = runner.invoke(app, ["config", "--workspace", "workspace1"])
                assert result.exit_code == 0
                
                # List datasets in workspace1
                result = runner.invoke(app, ["dataset", "list"])
                assert result.exit_code == 0
                assert "workspace1-dataset" in result.stdout
                
                # Switch to different workspace
                mock_list.return_value = {
                    "tables": [{"name": "workspace2-dataset", "namespace": "workspace2"}]
                }
                
                result = runner.invoke(app, ["config", "--workspace", "workspace2"])
                assert result.exit_code == 0
                
                # List datasets in workspace2
                result = runner.invoke(app, ["dataset", "list"])
                assert result.exit_code == 0
                assert "workspace2-dataset" in result.stdout
