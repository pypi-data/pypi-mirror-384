"""Tests for mixtrain client module."""

import pytest
import httpx
from unittest.mock import AsyncMock, Mock, patch
from mixtrain import client
from mixtrain.utils.config import Config


class TestClientAPI:
    """Test client API functions."""

    @pytest.mark.asyncio
    async def test_call_api_with_auth_token(self, mock_config, mock_platform_url):
        """Test API call with auth token."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)
            
            response = await client._call_api("GET", "/test")
            
            assert response.status_code == 200
            assert response.json() == {"data": "test"}

    @pytest.mark.asyncio
    async def test_call_api_with_api_key(self, mock_config, mock_platform_url, mock_api_key):
        """Test API call with API key."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)
            
            response = await client._call_api("GET", "/test")
            
            # Verify API key was used in headers
            call_args = mock_client.return_value.__aenter__.return_value.request.call_args
            headers = call_args[1]["headers"]
            assert headers["X-API-Key"] == mock_api_key

    @pytest.mark.asyncio
    async def test_call_api_error_response(self, mock_config, mock_platform_url):
        """Test API call with error response."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Bad request"}
        mock_response.text = "Bad request"
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception, match="Bad request"):
                await client._call_api("GET", "/test")

    def test_call_api_sync_wrapper(self, mock_config, mock_platform_url):
        """Test synchronous wrapper around async API calls."""
        with patch("mixtrain.client._call_api") as mock_async_call:
            mock_response = Mock()
            mock_response.json.return_value = {"data": "test"}
            mock_async_call.return_value = mock_response
            
            response = client.call_api("GET", "/test")
            
            assert response.json() == {"data": "test"}
            mock_async_call.assert_called_once_with("GET", "/test", json=None, files=None, params=None, headers=None)


class TestWorkspaceOperations:
    """Test workspace-related operations."""

    def test_create_workspace(self, mock_config, mock_platform_url):
        """Test workspace creation."""
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {
                "data": {"name": "new-workspace", "description": "Test workspace"}
            }
            
            result = client.create_workspace("new-workspace", "Test workspace")
            
            mock_call.assert_called_once_with(
                "POST",
                "/workspaces/",
                json={"name": "new-workspace", "description": "Test workspace"}
            )
            assert result["data"]["name"] == "new-workspace"

    def test_list_workspaces(self, mock_config, mock_platform_url):
        """Test listing workspaces."""
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {
                "data": [
                    {"name": "workspace1", "description": "First workspace"},
                    {"name": "workspace2", "description": "Second workspace"}
                ]
            }
            
            result = client.list_workspaces()
            
            mock_call.assert_called_once_with("GET", "/workspaces/list")
            assert len(result["data"]) == 2

    def test_delete_workspace(self, mock_config, mock_platform_url):
        """Test workspace deletion."""
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value = Mock()
            
            client.delete_workspace("test-workspace")
            
            mock_call.assert_called_once_with("DELETE", "/workspaces/test-workspace")

    def test_set_workspace(self, mock_config):
        """Test setting active workspace."""
        client.set_workspace("new-workspace")
        
        config = Config()
        # Should raise exception since workspace doesn't exist in config
        with pytest.raises(Exception, match="Workspace 'new-workspace' not found"):
            config.workspace_name

    def test_get_workspace(self, mock_config):
        """Test getting current workspace."""
        workspace = client.get_workspace()
        assert workspace == "test-workspace"


class TestDatasetOperations:
    """Test dataset-related operations."""

    def test_create_dataset_from_file(self, mock_config, mock_platform_url, sample_csv_file):
        """Test creating dataset from file."""
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {"data": {"name": "test-dataset"}}
            
            result = client.create_dataset_from_file("test-dataset", sample_csv_file, "Test dataset")
            
            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0] == ("POST", "/lakehouse/workspaces/test-workspace/tables/test-dataset")
            assert "files" in call_args[1]
            assert call_args[1]["headers"]["X-Description"] == "Test dataset"

    def test_list_datasets(self, mock_config, mock_platform_url):
        """Test listing datasets."""
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {
                "tables": [
                    {"name": "dataset1", "namespace": "test-workspace", "description": "First dataset"},
                    {"name": "dataset2", "namespace": "test-workspace", "description": "Second dataset"}
                ]
            }
            
            result = client.list_datasets()
            
            mock_call.assert_called_once_with("GET", "/lakehouse/workspaces/test-workspace/tables")
            assert len(result["tables"]) == 2

    def test_delete_dataset(self, mock_config, mock_platform_url):
        """Test dataset deletion."""
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value = Mock()
            
            client.delete_dataset("test-dataset")
            
            mock_call.assert_called_once_with("DELETE", "/lakehouse/workspaces/test-workspace/tables/test-dataset")

    def test_get_dataset_metadata(self, mock_config, mock_platform_url):
        """Test getting dataset metadata."""
        mock_table = Mock()
        mock_metadata = {
            "table_name": "test-dataset",
            "format_version": 2,
            "table_uuid": "test-uuid",
            "location": "s3://bucket/path"
        }
        mock_table.metadata = mock_metadata
        
        with patch("mixtrain.client.get_dataset", return_value=mock_table):
            result = client.get_dataset_metadata("test-dataset")
            
            assert result == mock_metadata


class TestProviderOperations:
    """Test provider-related operations."""

    def test_list_dataset_providers(self, mock_config, mock_platform_url):
        """Test listing dataset providers."""
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {
                "available_providers": [
                    {"provider_type": "apache_iceberg", "display_name": "Apache Iceberg"}
                ],
                "onboarded_providers": []
            }
            
            result = client.list_dataset_providers()
            
            mock_call.assert_called_once_with("GET", "/workspaces/test-workspace/dataset-providers/")
            assert len(result["available_providers"]) == 1

    def test_create_dataset_provider(self, mock_config, mock_platform_url):
        """Test creating dataset provider."""
        secrets = {"CATALOG_URI": "postgresql://localhost:5432/catalog"}
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {
                "id": 1,
                "provider_type": "apache_iceberg",
                "display_name": "Apache Iceberg"
            }
            
            result = client.create_dataset_provider("apache_iceberg", secrets)
            
            mock_call.assert_called_once_with(
                "POST",
                "/workspaces/test-workspace/dataset-providers/",
                json={"provider_type": "apache_iceberg", "secrets": secrets}
            )
            assert result["id"] == 1

    def test_update_dataset_provider(self, mock_config, mock_platform_url):
        """Test updating dataset provider."""
        secrets = {"CATALOG_URI": "postgresql://localhost:5432/new_catalog"}
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {"id": 1, "updated": True}
            
            result = client.update_dataset_provider(1, secrets)
            
            mock_call.assert_called_once_with(
                "PUT",
                "/workspaces/test-workspace/dataset-providers/1",
                json={"secrets": secrets}
            )
            assert result["updated"] is True

    def test_delete_dataset_provider(self, mock_config, mock_platform_url):
        """Test deleting dataset provider."""
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {"deleted": True}
            
            result = client.delete_dataset_provider(1)
            
            mock_call.assert_called_once_with("DELETE", "/workspaces/test-workspace/dataset-providers/1")
            assert result["deleted"] is True

    def test_list_model_providers(self, mock_config, mock_platform_url):
        """Test listing model providers."""
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {
                "available_providers": [
                    {"provider_type": "openai", "display_name": "OpenAI"}
                ],
                "onboarded_providers": []
            }
            
            result = client.list_model_providers()
            
            mock_call.assert_called_once_with("GET", "/workspaces/test-workspace/models/providers")
            assert len(result["available_providers"]) == 1

    def test_create_model_provider(self, mock_config, mock_platform_url):
        """Test creating model provider."""
        secrets = {"API_KEY": "sk-test-key"}
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {
                "id": 1,
                "provider_type": "openai",
                "display_name": "OpenAI"
            }
            
            result = client.create_model_provider("openai", secrets)
            
            mock_call.assert_called_once_with(
                "POST",
                "/workspaces/test-workspace/models/providers",
                json={"provider_type": "openai", "secrets": secrets}
            )
            assert result["id"] == 1

    def test_list_models(self, mock_config, mock_platform_url):
        """Test listing models."""
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = [
                {"name": "gpt-4", "provider_name": "OpenAI", "url": "https://api.openai.com"}
            ]
            
            result = client.list_models()
            
            mock_call.assert_called_once_with("GET", "/workspaces/test-workspace/models/")
            assert len(result) == 1
            assert result[0]["name"] == "gpt-4"


class TestAuthenticationMethods:
    """Test authentication methods."""

    def test_authenticate_browser(self, mock_config):
        """Test browser authentication."""
        with patch("mixtrain.utils.auth.authenticate_browser") as mock_auth:
            mock_auth.return_value = "test_token"
            
            result = client.authenticate_browser()
            
            assert result == "test_token"
            mock_auth.assert_called_once()

    def test_authenticate_with_token(self, mock_config):
        """Test token authentication."""
        with patch("mixtrain.utils.auth.authenticate_with_token") as mock_auth:
            mock_auth.return_value = "test_token"
            
            result = client.authenticate_with_token("oauth_token", "github")
            
            assert result == "test_token"
            mock_auth.assert_called_once_with("oauth_token", "github", client.get_config, client._call_api)

    def test_authenticate_github(self, mock_config):
        """Test GitHub authentication."""
        with patch("mixtrain.utils.auth.authenticate_github") as mock_auth:
            mock_auth.return_value = "test_token"
            
            result = client.authenticate_github("github_token")
            
            assert result == "test_token"
            mock_auth.assert_called_once()

    def test_authenticate_google(self, mock_config):
        """Test Google authentication."""
        with patch("mixtrain.utils.auth.authenticate_google") as mock_auth:
            mock_auth.return_value = "test_token"
            
            result = client.authenticate_google("google_token")
            
            assert result == "test_token"
            mock_auth.assert_called_once()


class TestCatalogOperations:
    """Test catalog and dataset operations."""

    def test_get_catalog(self, mock_config, mock_platform_url):
        """Test getting catalog."""
        provider_secrets = {
            "provider_type": "apache_iceberg",
            "secrets": {
                "CATALOG_TYPE": "sql",
                "CATALOG_URI": "postgresql://localhost:5432/catalog",
                "CATALOG_WAREHOUSE_URI": "s3://bucket/warehouse"
            }
        }
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = provider_secrets
            
            with patch("pyiceberg.catalog.load_catalog") as mock_load_catalog:
                mock_catalog = Mock()
                mock_load_catalog.return_value = mock_catalog
                
                result = client.get_catalog("test-workspace")
                
                assert result == mock_catalog
                mock_load_catalog.assert_called_once_with(
                    "default",
                    type="sql",
                    uri="postgresql://localhost:5432/catalog",
                    warehouse="s3://bucket/warehouse"
                )

    def test_get_dataset(self, mock_config, mock_platform_url):
        """Test getting dataset."""
        mock_catalog = Mock()
        mock_table = Mock()
        mock_catalog.load_table.return_value = mock_table
        
        with patch("mixtrain.client.get_catalog", return_value=mock_catalog):
            result = client.get_dataset("test-dataset")
            
            assert result == mock_table
            mock_catalog.load_table.assert_called_once_with("test-workspace.test-dataset")

    def test_get_catalog_with_gcs_credentials(self, mock_config, mock_platform_url):
        """Test getting catalog with GCS credentials."""
        provider_secrets = {
            "provider_type": "apache_iceberg",
            "secrets": {
                "CATALOG_TYPE": "sql",
                "CATALOG_URI": "postgresql://localhost:5432/catalog",
                "CATALOG_WAREHOUSE_URI": "gs://bucket/warehouse",
                "SERVICE_ACCOUNT_JSON": '{"type": "service_account"}'
            }
        }
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = provider_secrets
            
            with patch("pyiceberg.catalog.load_catalog") as mock_load_catalog:
                with patch("builtins.open", create=True) as mock_open:
                    with patch("os.makedirs"):
                        mock_catalog = Mock()
                        mock_load_catalog.return_value = mock_catalog
                        
                        result = client.get_catalog("test-workspace")
                        
                        assert result == mock_catalog
                        # Verify service account file was written
                        mock_open.assert_called()


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_no_auth_token_error(self, temp_config_dir):
        """Test error when no auth token is available."""
        config = Config()
        config.auth_token = None
        config._save_config()
        
        with pytest.raises(Exception, match="No auth token or API key found"):
            client.call_api("GET", "/test")

    def test_invalid_api_key_format(self, mock_config, mock_platform_url):
        """Test error with invalid API key format."""
        with patch.dict("os.environ", {"MIXTRAIN_API_KEY": "invalid-key"}):
            with pytest.raises(Exception, match="Invalid API key format"):
                client.call_api("GET", "/test")

    def test_no_active_workspace_error(self, temp_config_dir):
        """Test error when no active workspace is set."""
        config = Config()
        config.auth_token = "test_token"
        config.workspaces = []
        config._save_config()
        
        with pytest.raises(Exception, match="No active workspace"):
            client.get_workspace()

    def test_catalog_load_error(self, mock_config, mock_platform_url):
        """Test error when catalog fails to load."""
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value.json.return_value = {
                "provider_type": "unsupported_provider"
            }
            
            with pytest.raises(Exception, match="is not supported"):
                client.get_catalog("test-workspace")
