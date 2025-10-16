"""Tests for mixtrain secret module."""

import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from mixtrain.secret import app


class TestSecretCLICommands:
    """Test secret CLI commands."""

    def test_secret_help(self):
        """Test secret help command."""
        runner = CliRunner()
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout

    def test_secret_list_success(self, mock_config):
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
        
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_response = Mock()
            mock_response.json.return_value = mock_secrets
            mock_call.return_value = mock_response
            
            result = runner.invoke(app, ["list"])
            
            assert result.exit_code == 0
            assert "API_KEY" in result.stdout
            assert "DATABASE_URL" in result.stdout
            assert "OpenAI API Key" in result.stdout
            assert "Database connection string" in result.stdout
            assert "2023-01-01 00:00" in result.stdout

    def test_secret_list_empty(self, mock_config):
        """Test secret list with no secrets."""
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_call.return_value = mock_response
            
            result = runner.invoke(app, ["list"])
            
            assert result.exit_code == 0
            assert "No secrets found" in result.stdout
            assert "mixtrain secret set" in result.stdout

    def test_secret_list_error(self, mock_config):
        """Test secret list with error."""
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.side_effect = Exception("API error")
            
            result = runner.invoke(app, ["list"])
            
            assert result.exit_code == 1
            assert "Error listing secrets:" in result.stdout
            assert "API error" in result.stdout

    def test_secret_get_success_hidden(self, mock_config):
        """Test successful secret get command with hidden value."""
        mock_secret = {
            "name": "API_KEY",
            "description": "OpenAI API Key",
            "value": "sk-test-key",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T12:00:00Z",
            "created_by": "user@example.com"
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_response = Mock()
            mock_response.json.return_value = mock_secret
            mock_call.return_value = mock_response
            
            result = runner.invoke(app, ["get", "API_KEY"])
            
            assert result.exit_code == 0
            assert "Secret 'API_KEY':" in result.stdout
            assert "OpenAI API Key" in result.stdout
            assert "Hidden (use --show to display)" in result.stdout
            assert "sk-test-key" not in result.stdout
            assert "💡 Use --show to display the secret value" in result.stdout

    def test_secret_get_success_shown(self, mock_config):
        """Test successful secret get command with shown value."""
        mock_secret = {
            "name": "API_KEY",
            "description": "OpenAI API Key",
            "value": "sk-test-key",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T12:00:00Z",
            "created_by": "user@example.com"
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_response = Mock()
            mock_response.json.return_value = mock_secret
            mock_call.return_value = mock_response
            
            result = runner.invoke(app, ["get", "API_KEY", "--show"])
            
            assert result.exit_code == 0
            assert "Secret 'API_KEY':" in result.stdout
            assert "OpenAI API Key" in result.stdout
            assert "sk-test-key" in result.stdout
            assert "Hidden" not in result.stdout

    def test_secret_get_not_found(self, mock_config):
        """Test secret get command with non-existent secret."""
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.side_effect = Exception("404")
            
            result = runner.invoke(app, ["get", "NONEXISTENT"])
            
            assert result.exit_code == 1
            assert "Secret 'NONEXISTENT' not found" in result.stdout

    def test_secret_get_error(self, mock_config):
        """Test secret get command with general error."""
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.side_effect = Exception("General error")
            
            result = runner.invoke(app, ["get", "API_KEY"])
            
            assert result.exit_code == 1
            assert "Error retrieving secret:" in result.stdout
            assert "General error" in result.stdout

    def test_secret_set_create_new_with_args(self, mock_config):
        """Test creating new secret with command line arguments."""
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            # First call to check if secret exists (returns 404)
            # Second call to create the secret
            mock_call.side_effect = [
                Exception("404"),  # Secret doesn't exist
                Mock()  # Creation successful
            ]
            
            result = runner.invoke(app, [
                "set", "NEW_SECRET", "secret_value",
                "--description", "New secret description"
            ])
            
            assert result.exit_code == 0
            assert "✓" in result.stdout
            assert "Secret 'NEW_SECRET' created successfully!" in result.stdout
            
            # Verify creation call
            create_call = mock_call.call_args_list[1]
            assert create_call[0] == ("POST", "/workspaces/test-workspace/secrets/")
            assert create_call[1]["json"]["name"] == "NEW_SECRET"
            assert create_call[1]["json"]["value"] == "secret_value"
            assert create_call[1]["json"]["description"] == "New secret description"

    def test_secret_set_create_new_with_prompts(self, mock_config):
        """Test creating new secret with interactive prompts."""
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.side_effect = [
                Exception("404"),  # Secret doesn't exist
                Mock()  # Creation successful
            ]
            
            with patch("rich.prompt.Prompt.ask") as mock_prompt:
                mock_prompt.side_effect = ["secret_value", "Prompted description"]
                
                result = runner.invoke(app, ["set", "NEW_SECRET"])
                
                assert result.exit_code == 0
                assert "✓" in result.stdout
                assert "Secret 'NEW_SECRET' created successfully!" in result.stdout

    def test_secret_set_update_existing(self, mock_config):
        """Test updating existing secret."""
        existing_secret = {
            "name": "EXISTING_SECRET",
            "value": "old_value",
            "description": "Old description"
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            # First call returns existing secret
            # Second call updates the secret
            mock_response = Mock()
            mock_response.json.return_value = existing_secret
            mock_call.side_effect = [
                mock_response,  # Secret exists
                Mock()  # Update successful
            ]
            
            result = runner.invoke(app, [
                "set", "EXISTING_SECRET", "new_value",
                "--description", "New description",
                "--update"
            ])
            
            assert result.exit_code == 0
            assert "✓" in result.stdout
            assert "Secret 'EXISTING_SECRET' updated successfully!" in result.stdout
            
            # Verify update call
            update_call = mock_call.call_args_list[1]
            assert update_call[0] == ("PUT", "/workspaces/test-workspace/secrets/EXISTING_SECRET")
            assert update_call[1]["json"]["value"] == "new_value"
            assert update_call[1]["json"]["description"] == "New description"

    def test_secret_set_existing_without_update_flag(self, mock_config):
        """Test setting existing secret without update flag."""
        existing_secret = {
            "name": "EXISTING_SECRET",
            "value": "old_value",
            "description": "Old description"
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_response = Mock()
            mock_response.json.return_value = existing_secret
            mock_call.return_value = mock_response
            
            result = runner.invoke(app, [
                "set", "EXISTING_SECRET", "new_value"
            ])
            
            assert result.exit_code == 1
            assert "Secret 'EXISTING_SECRET' already exists" in result.stdout
            assert "Use --update flag to update" in result.stdout

    def test_secret_set_empty_value(self, mock_config):
        """Test setting secret with empty value."""
        runner = CliRunner()
        
        with patch("rich.prompt.Prompt.ask") as mock_prompt:
            mock_prompt.return_value = "   "  # Whitespace only
            
            result = runner.invoke(app, ["set", "NEW_SECRET"])
            
            assert result.exit_code == 1
            assert "Secret value cannot be empty" in result.stdout

    def test_secret_set_error(self, mock_config):
        """Test secret set with API error."""
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.side_effect = Exception("API error")
            
            result = runner.invoke(app, ["set", "NEW_SECRET", "value"])
            
            assert result.exit_code == 1
            assert "Error creating/updating secret:" in result.stdout
            assert "API error" in result.stdout

    def test_secret_delete_success(self, mock_config):
        """Test successful secret deletion."""
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value = Mock()
            
            with patch("rich.prompt.Confirm.ask") as mock_confirm:
                mock_confirm.return_value = True
                
                result = runner.invoke(app, ["delete", "TEST_SECRET"])
                
                assert result.exit_code == 0
                assert "✓" in result.stdout
                assert "Secret 'TEST_SECRET' deleted successfully!" in result.stdout
                mock_call.assert_called_once_with("DELETE", "/workspaces/test-workspace/secrets/TEST_SECRET")

    def test_secret_delete_with_force(self, mock_config):
        """Test secret deletion with force flag."""
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.return_value = Mock()
            
            result = runner.invoke(app, ["delete", "TEST_SECRET", "--force"])
            
            assert result.exit_code == 0
            assert "✓" in result.stdout
            assert "Secret 'TEST_SECRET' deleted successfully!" in result.stdout

    def test_secret_delete_cancelled(self, mock_config):
        """Test secret deletion cancelled by user."""
        runner = CliRunner()
        
        with patch("rich.prompt.Confirm.ask") as mock_confirm:
            mock_confirm.return_value = False
            
            result = runner.invoke(app, ["delete", "TEST_SECRET"])
            
            assert result.exit_code == 0
            assert "Deletion cancelled" in result.stdout

    def test_secret_delete_not_found(self, mock_config):
        """Test deleting non-existent secret."""
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.side_effect = Exception("404")
            
            with patch("rich.prompt.Confirm.ask") as mock_confirm:
                mock_confirm.return_value = True
                
                result = runner.invoke(app, ["delete", "NONEXISTENT"])
                
                assert result.exit_code == 1
                assert "Secret 'NONEXISTENT' not found" in result.stdout

    def test_secret_delete_error(self, mock_config):
        """Test secret deletion with general error."""
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.side_effect = Exception("General error")
            
            with patch("rich.prompt.Confirm.ask") as mock_confirm:
                mock_confirm.return_value = True
                
                result = runner.invoke(app, ["delete", "TEST_SECRET"])
                
                assert result.exit_code == 1
                assert "Error deleting secret:" in result.stdout
                assert "General error" in result.stdout

    def test_secret_copy_success(self, mock_config):
        """Test successful secret copying."""
        source_secret = {
            "name": "SOURCE_SECRET",
            "value": "source_value",
            "description": "Source description"
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            # First call gets source secret
            # Second call creates new secret
            mock_response = Mock()
            mock_response.json.return_value = source_secret
            mock_call.side_effect = [
                mock_response,  # Get source secret
                Mock()  # Create new secret
            ]
            
            result = runner.invoke(app, [
                "copy", "SOURCE_SECRET", "TARGET_SECRET",
                "--description", "New description"
            ])
            
            assert result.exit_code == 0
            assert "✓" in result.stdout
            assert "Secret 'SOURCE_SECRET' copied to 'TARGET_SECRET' successfully!" in result.stdout
            
            # Verify creation call
            create_call = mock_call.call_args_list[1]
            assert create_call[0] == ("POST", "/workspaces/test-workspace/secrets/")
            assert create_call[1]["json"]["name"] == "TARGET_SECRET"
            assert create_call[1]["json"]["value"] == "source_value"
            assert create_call[1]["json"]["description"] == "New description"

    def test_secret_copy_with_source_description(self, mock_config):
        """Test copying secret using source description."""
        source_secret = {
            "name": "SOURCE_SECRET",
            "value": "source_value",
            "description": "Source description"
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_response = Mock()
            mock_response.json.return_value = source_secret
            mock_call.side_effect = [
                mock_response,  # Get source secret
                Mock()  # Create new secret
            ]
            
            result = runner.invoke(app, ["copy", "SOURCE_SECRET", "TARGET_SECRET"])
            
            assert result.exit_code == 0
            
            # Verify creation call uses source description
            create_call = mock_call.call_args_list[1]
            assert create_call[1]["json"]["description"] == "Source description"

    def test_secret_copy_source_not_found(self, mock_config):
        """Test copying non-existent source secret."""
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_call.side_effect = Exception("404")
            
            result = runner.invoke(app, ["copy", "NONEXISTENT", "TARGET_SECRET"])
            
            assert result.exit_code == 1
            assert "Source secret 'NONEXISTENT' not found" in result.stdout

    def test_secret_copy_target_exists(self, mock_config):
        """Test copying to existing target secret."""
        source_secret = {
            "name": "SOURCE_SECRET",
            "value": "source_value",
            "description": "Source description"
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_response = Mock()
            mock_response.json.return_value = source_secret
            mock_call.side_effect = [
                mock_response,  # Get source secret
                Exception("already exists")  # Target already exists
            ]
            
            result = runner.invoke(app, ["copy", "SOURCE_SECRET", "EXISTING_TARGET"])
            
            assert result.exit_code == 1
            assert "Target secret 'EXISTING_TARGET' already exists" in result.stdout

    def test_secret_copy_error(self, mock_config):
        """Test secret copying with general error."""
        source_secret = {
            "name": "SOURCE_SECRET",
            "value": "source_value",
            "description": "Source description"
        }
        
        runner = CliRunner()
        
        with patch("mixtrain.client.call_api") as mock_call:
            mock_response = Mock()
            mock_response.json.return_value = source_secret
            mock_call.side_effect = [
                mock_response,  # Get source secret
                Exception("General error")  # Creation error
            ]
            
            result = runner.invoke(app, ["copy", "SOURCE_SECRET", "TARGET_SECRET"])
            
            assert result.exit_code == 1
            assert "Error copying secret:" in result.stdout
            assert "General error" in result.stdout
