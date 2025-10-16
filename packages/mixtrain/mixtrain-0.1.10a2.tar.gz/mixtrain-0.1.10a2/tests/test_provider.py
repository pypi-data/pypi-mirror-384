"""Tests for mixtrain provider module."""

import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from mixtrain.provider import app, get_provider_config, get_provider_config_by_id


class TestProviderHelpers:
    """Test provider helper functions."""

    def test_get_provider_config_dataset_provider(self, mock_config):
        """Test getting dataset provider config."""
        dataset_data = {
            "available_providers": [
                {
                    "provider_type": "apache_iceberg",
                    "display_name": "Apache Iceberg",
                    "description": "Apache Iceberg data lake format"
                }
            ]
        }
        
        with patch("mixtrain.client.list_dataset_providers") as mock_dataset:
            mock_dataset.return_value = dataset_data
            
            with patch("mixtrain.client.list_model_providers") as mock_model:
                mock_model.return_value = {"available_providers": []}
                
                result = get_provider_config("apache_iceberg")
                
                assert result["provider_type"] == "apache_iceberg"
                assert result["provider_category"] == "dataset"
                assert result["display_name"] == "Apache Iceberg"

    def test_get_provider_config_model_provider(self, mock_config):
        """Test getting model provider config."""
        model_data = {
            "available_providers": [
                {
                    "provider_type": "openai",
                    "display_name": "OpenAI",
                    "description": "OpenAI language models"
                }
            ]
        }
        
        with patch("mixtrain.client.list_dataset_providers") as mock_dataset:
            mock_dataset.return_value = {"available_providers": []}
            
            with patch("mixtrain.client.list_model_providers") as mock_model:
                mock_model.return_value = model_data
                
                result = get_provider_config("openai")
                
                assert result["provider_type"] == "openai"
                assert result["provider_category"] == "model"
                assert result["display_name"] == "OpenAI"

    def test_get_provider_config_not_found(self, mock_config):
        """Test getting non-existent provider config."""
        with patch("mixtrain.client.list_dataset_providers") as mock_dataset:
            mock_dataset.return_value = {"available_providers": []}
            
            with patch("mixtrain.client.list_model_providers") as mock_model:
                mock_model.return_value = {"available_providers": []}
                
                with pytest.raises(SystemExit):
                    get_provider_config("nonexistent")

    def test_get_provider_config_by_id_dataset_provider(self, mock_config):
        """Test getting dataset provider config by ID."""
        dataset_data = {
            "onboarded_providers": [
                {
                    "id": 1,
                    "provider_type": "apache_iceberg",
                    "display_name": "Apache Iceberg"
                }
            ]
        }
        
        with patch("mixtrain.client.list_dataset_providers") as mock_dataset:
            mock_dataset.return_value = dataset_data
            
            result = get_provider_config_by_id(1)
            
            assert result["id"] == 1
            assert result["provider_category"] == "dataset"
            assert result["provider_type"] == "apache_iceberg"

    def test_get_provider_config_by_id_model_provider(self, mock_config):
        """Test getting model provider config by ID."""
        dataset_data = {"onboarded_providers": []}
        model_data = {
            "onboarded_providers": [
                {
                    "id": 2,
                    "provider_type": "openai",
                    "display_name": "OpenAI"
                }
            ]
        }
        
        with patch("mixtrain.client.list_dataset_providers") as mock_dataset:
            mock_dataset.return_value = dataset_data
            
            with patch("mixtrain.client.list_model_providers") as mock_model:
                mock_model.return_value = model_data
                
                result = get_provider_config_by_id(2)
                
                assert result["id"] == 2
                assert result["provider_category"] == "model"
                assert result["provider_type"] == "openai"

    def test_get_provider_config_by_id_not_found(self, mock_config):
        """Test getting non-existent provider config by ID."""
        with patch("mixtrain.client.list_dataset_providers") as mock_dataset:
            mock_dataset.return_value = {"onboarded_providers": []}
            
            with patch("mixtrain.client.list_model_providers") as mock_model:
                mock_model.return_value = {"onboarded_providers": []}
                
                with pytest.raises(SystemExit):
                    get_provider_config_by_id(999)


class TestProviderCLICommands:
    """Test provider CLI commands."""

    def test_provider_help(self):
        """Test provider help command."""
        runner = CliRunner()
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout

    def test_provider_status_success(self, mock_config):
        """Test successful provider status command."""
        dataset_data = {
            "available_providers": [
                {
                    "provider_type": "apache_iceberg",
                    "display_name": "Apache Iceberg",
                    "description": "Apache Iceberg data lake format with very long description that should be truncated",
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
            "onboarded_providers": [
                {
                    "id": 2,
                    "provider_type": "openai",
                    "display_name": "OpenAI",
                    "created_at": "2023-01-02T00:00:00Z"
                }
            ]
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.client.list_dataset_providers") as mock_dataset:
            mock_dataset.return_value = dataset_data
            
            with patch("mixtrain.client.list_model_providers") as mock_model:
                mock_model.return_value = model_data
                
                result = runner.invoke(app, ["status"])
                
                assert result.exit_code == 0
                assert "Available Dataset Providers:" in result.stdout
                assert "Apache Iceberg" in result.stdout
                assert "Available Model Providers:" in result.stdout
                assert "OpenAI" in result.stdout
                assert "Configured Dataset Providers:" in result.stdout
                assert "Configured Model Providers:" in result.stdout

    def test_provider_status_no_providers(self, mock_config):
        """Test provider status with no configured providers."""
        empty_data = {
            "available_providers": [],
            "onboarded_providers": []
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.client.list_dataset_providers") as mock_dataset:
            mock_dataset.return_value = empty_data
            
            with patch("mixtrain.client.list_model_providers") as mock_model:
                mock_model.return_value = empty_data
                
                result = runner.invoke(app, ["status"])
                
                assert result.exit_code == 0
                assert "No providers configured yet" in result.stdout
                assert "mixtrain provider add" in result.stdout

    def test_provider_status_error(self, mock_config):
        """Test provider status with error."""
        runner = CliRunner()
        
        with patch("mixtrain.client.list_dataset_providers") as mock_dataset:
            mock_dataset.side_effect = Exception("API error")
            
            result = runner.invoke(app, ["status"])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "API error" in result.stdout

    def test_provider_add_dataset_provider(self, mock_config):
        """Test adding a dataset provider."""
        provider_config = {
            "provider_type": "apache_iceberg",
            "display_name": "Apache Iceberg",
            "description": "Apache Iceberg data lake format",
            "provider_category": "dataset",
            "secret_requirements": [
                {
                    "name": "CATALOG_URI",
                    "display_name": "Catalog URI",
                    "description": "PostgreSQL connection string",
                    "is_required": True
                }
            ]
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.provider.get_provider_config") as mock_get_config:
            mock_get_config.return_value = provider_config
            
            with patch("mixtrain.client.create_dataset_provider") as mock_create:
                mock_create.return_value = {"display_name": "Apache Iceberg"}
                
                # Mock user input
                with patch("typer.prompt") as mock_prompt:
                    mock_prompt.return_value = "postgresql://localhost:5432/catalog"
                    
                    result = runner.invoke(app, ["add", "apache_iceberg"])
                    
                    assert result.exit_code == 0
                    assert "✓" in result.stdout
                    assert "Successfully added Apache Iceberg!" in result.stdout
                    mock_create.assert_called_once_with(
                        "apache_iceberg",
                        {"CATALOG_URI": "postgresql://localhost:5432/catalog"}
                    )

    def test_provider_add_model_provider(self, mock_config):
        """Test adding a model provider."""
        provider_config = {
            "provider_type": "openai",
            "display_name": "OpenAI",
            "description": "OpenAI language models",
            "provider_category": "model",
            "secret_requirements": [
                {
                    "name": "API_KEY",
                    "display_name": "API Key",
                    "description": "OpenAI API key",
                    "is_required": True
                }
            ]
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.provider.get_provider_config") as mock_get_config:
            mock_get_config.return_value = provider_config
            
            with patch("mixtrain.client.create_model_provider") as mock_create:
                mock_create.return_value = {"display_name": "OpenAI"}
                
                # Mock user input (hidden for API key)
                with patch("typer.prompt") as mock_prompt:
                    mock_prompt.return_value = "sk-test-key"
                    
                    result = runner.invoke(app, ["add", "openai"])
                    
                    assert result.exit_code == 0
                    assert "✓" in result.stdout
                    assert "Successfully added OpenAI!" in result.stdout
                    mock_create.assert_called_once_with(
                        "openai",
                        {"API_KEY": "sk-test-key"}
                    )

    def test_provider_add_no_secrets(self, mock_config):
        """Test adding provider with no secrets provided."""
        provider_config = {
            "provider_type": "test_provider",
            "display_name": "Test Provider",
            "description": "Test provider",
            "provider_category": "dataset",
            "secret_requirements": [
                {
                    "name": "OPTIONAL_SECRET",
                    "display_name": "Optional Secret",
                    "description": "Optional secret",
                    "is_required": False
                }
            ]
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.provider.get_provider_config") as mock_get_config:
            mock_get_config.return_value = provider_config
            
            # Mock user input (empty for optional secret)
            with patch("typer.prompt") as mock_prompt:
                mock_prompt.return_value = ""
                
                result = runner.invoke(app, ["add", "test_provider"])
                
                assert result.exit_code == 1
                assert "No secrets provided" in result.stdout

    def test_provider_add_error(self, mock_config):
        """Test adding provider with error."""
        provider_config = {
            "provider_type": "apache_iceberg",
            "display_name": "Apache Iceberg",
            "description": "Apache Iceberg data lake format",
            "provider_category": "dataset",
            "secret_requirements": []
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.provider.get_provider_config") as mock_get_config:
            mock_get_config.return_value = provider_config
            
            with patch("mixtrain.client.create_dataset_provider") as mock_create:
                mock_create.side_effect = Exception("Creation failed")
                
                result = runner.invoke(app, ["add", "apache_iceberg"])
                
                assert result.exit_code == 1
                assert "Error:" in result.stdout
                assert "Creation failed" in result.stdout

    def test_provider_update_success(self, mock_config):
        """Test updating provider successfully."""
        provider_config = {
            "id": 1,
            "provider_type": "apache_iceberg",
            "display_name": "Apache Iceberg",
            "provider_category": "dataset",
            "secret_requirements": [
                {
                    "name": "CATALOG_URI",
                    "display_name": "Catalog URI",
                    "description": "PostgreSQL connection string",
                    "is_required": True
                }
            ]
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.provider.get_provider_config_by_id") as mock_get_config:
            mock_get_config.return_value = provider_config
            
            with patch("mixtrain.client.update_dataset_provider") as mock_update:
                mock_update.return_value = {"display_name": "Apache Iceberg"}
                
                # Mock user input
                with patch("typer.prompt") as mock_prompt:
                    mock_prompt.return_value = "postgresql://new-host:5432/catalog"
                    
                    result = runner.invoke(app, ["update", "1"])
                    
                    assert result.exit_code == 0
                    assert "✓" in result.stdout
                    assert "Successfully updated Apache Iceberg!" in result.stdout
                    mock_update.assert_called_once_with(
                        1,
                        {"CATALOG_URI": "postgresql://new-host:5432/catalog"}
                    )

    def test_provider_update_no_changes(self, mock_config):
        """Test updating provider with no changes."""
        provider_config = {
            "id": 1,
            "provider_type": "apache_iceberg",
            "display_name": "Apache Iceberg",
            "provider_category": "dataset",
            "secret_requirements": [
                {
                    "name": "CATALOG_URI",
                    "display_name": "Catalog URI",
                    "description": "PostgreSQL connection string",
                    "is_required": True
                }
            ]
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.provider.get_provider_config_by_id") as mock_get_config:
            mock_get_config.return_value = provider_config
            
            # Mock user input (empty to keep current values)
            with patch("typer.prompt") as mock_prompt:
                mock_prompt.return_value = ""
                
                result = runner.invoke(app, ["update", "1"])
                
                assert result.exit_code == 0
                assert "No secrets updated" in result.stdout

    def test_provider_remove_success(self, mock_config):
        """Test removing provider successfully."""
        provider_config = {
            "id": 1,
            "provider_type": "apache_iceberg",
            "display_name": "Apache Iceberg",
            "provider_category": "dataset"
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.provider.get_provider_config_by_id") as mock_get_config:
            mock_get_config.return_value = provider_config
            
            with patch("mixtrain.client.delete_dataset_provider") as mock_delete:
                # Mock user confirmation
                with patch("typer.confirm") as mock_confirm:
                    mock_confirm.return_value = True
                    
                    result = runner.invoke(app, ["remove", "1"])
                    
                    assert result.exit_code == 0
                    assert "✓" in result.stdout
                    assert "Successfully removed Apache Iceberg!" in result.stdout
                    mock_delete.assert_called_once_with(1)

    def test_provider_remove_cancelled(self, mock_config):
        """Test removing provider cancelled by user."""
        provider_config = {
            "id": 1,
            "provider_type": "apache_iceberg",
            "display_name": "Apache Iceberg",
            "provider_category": "dataset"
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.provider.get_provider_config_by_id") as mock_get_config:
            mock_get_config.return_value = provider_config
            
            # Mock user confirmation (cancelled)
            with patch("typer.confirm") as mock_confirm:
                mock_confirm.return_value = False
                
                result = runner.invoke(app, ["remove", "1"])
                
                assert result.exit_code == 0
                assert "Removal cancelled" in result.stdout

    def test_provider_info_success(self, mock_config):
        """Test provider info command successfully."""
        dataset_data = {
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
        
        runner = CliRunner()
        
        with patch("mixtrain.client.list_dataset_providers") as mock_dataset:
            mock_dataset.return_value = dataset_data
            
            with patch("mixtrain.client.list_model_providers") as mock_model:
                mock_model.return_value = {"available_providers": [], "onboarded_providers": []}
                
                result = runner.invoke(app, ["info", "apache_iceberg"])
                
                assert result.exit_code == 0
                assert "Apache Iceberg (dataset provider)" in result.stdout
                assert "Type: apache_iceberg" in result.stdout
                assert "Status: available" in result.stdout
                assert "Website: https://iceberg.apache.org" in result.stdout
                assert "Required Configuration:" in result.stdout
                assert "Setup Instructions:" in result.stdout

    def test_provider_info_not_found(self, mock_config):
        """Test provider info for non-existent provider."""
        runner = CliRunner()
        
        with patch("mixtrain.client.list_dataset_providers") as mock_dataset:
            mock_dataset.return_value = {"available_providers": [], "onboarded_providers": []}
            
            with patch("mixtrain.client.list_model_providers") as mock_model:
                mock_model.return_value = {"available_providers": [], "onboarded_providers": []}
                
                result = runner.invoke(app, ["info", "nonexistent"])
                
                assert result.exit_code == 1
                assert "Provider type 'nonexistent' not found" in result.stdout

    def test_provider_models_success(self, mock_config):
        """Test listing available models successfully."""
        mock_models = [
            {
                "name": "gpt-4",
                "provider_name": "OpenAI",
                "url": "https://api.openai.com"
            },
            {
                "name": "gpt-3.5-turbo",
                "provider_name": "OpenAI",
                "url": "https://api.openai.com"
            }
        ]
        
        runner = CliRunner()
        
        with patch("mixtrain.client.list_models") as mock_list:
            mock_list.return_value = mock_models
            
            result = runner.invoke(app, ["models"])
            
            assert result.exit_code == 0
            assert "Available Models:" in result.stdout
            assert "gpt-4" in result.stdout
            assert "gpt-3.5-turbo" in result.stdout
            assert "OpenAI" in result.stdout

    def test_provider_models_empty(self, mock_config):
        """Test listing models with no models available."""
        runner = CliRunner()
        
        with patch("mixtrain.client.list_models") as mock_list:
            mock_list.return_value = []
            
            result = runner.invoke(app, ["models"])
            
            assert result.exit_code == 0
            assert "No models available" in result.stdout
            assert "Configure a model provider first" in result.stdout

    def test_provider_models_error(self, mock_config):
        """Test listing models with error."""
        runner = CliRunner()
        
        with patch("mixtrain.client.list_models") as mock_list:
            mock_list.side_effect = Exception("Models error")
            
            result = runner.invoke(app, ["models"])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "Models error" in result.stdout
