"""Tests for mixtrain dataset module."""

import os
import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from mixtrain.dataset import app, validate_file, DatasetBrowser


class TestDatasetValidation:
    """Test dataset file validation."""

    def test_validate_file_csv_success(self, sample_csv_file):
        """Test successful CSV file validation."""
        result = validate_file(sample_csv_file)
        assert result == sample_csv_file

    def test_validate_file_parquet_success(self, sample_parquet_file):
        """Test successful Parquet file validation."""
        result = validate_file(sample_parquet_file)
        assert result == sample_parquet_file

    def test_validate_file_unsupported_format(self):
        """Test validation with unsupported file format."""
        with pytest.raises(ValueError, match="Only parquet and CSV files are supported"):
            validate_file("test.txt")

    def test_validate_file_not_found(self):
        """Test validation with non-existent file."""
        with pytest.raises(FileNotFoundError):
            validate_file("/nonexistent/file.csv")


class TestDatasetBrowser:
    """Test DatasetBrowser TUI application."""

    def test_dataset_browser_initialization(self):
        """Test DatasetBrowser initialization."""
        data = [
            {"id": 1, "name": "test1", "value": 100},
            {"id": 2, "name": "test2", "value": 200}
        ]
        schema = ["id", "name", "value"]
        
        browser = DatasetBrowser(data, schema, "test-dataset")
        
        assert browser.data == data
        assert browser.schema == schema
        assert browser.dataset_name == "test-dataset"

    def test_dataset_browser_with_tuple_schema(self):
        """Test DatasetBrowser with tuple-based schema."""
        data = [
            [1, "test1", 100],
            [2, "test2", 200]
        ]
        schema = [("id", "bigint"), ("name", "string"), ("value", "bigint")]
        
        browser = DatasetBrowser(data, schema, "test-dataset")
        
        assert browser.schema == schema
        assert browser.dataset_name == "test-dataset"

    def test_dataset_browser_normalize_dict_rows(self):
        """Test DatasetBrowser normalizing dictionary rows."""
        data = [
            {"id": 1, "name": "test1", "value": 100},
            {"id": 2, "name": "test2", "value": 200}
        ]
        schema = ["id", "name", "value"]
        
        browser = DatasetBrowser(data, schema, "test-dataset")
        
        # The browser should normalize dict rows to lists during mount
        # We can't easily test the mount process, but we can verify the data structure
        assert len(browser.data) == 2

    def test_dataset_browser_normalize_list_rows(self):
        """Test DatasetBrowser with list rows."""
        data = [
            [1, "test1", 100],
            [2, "test2", 200]
        ]
        schema = ["id", "name", "value"]
        
        browser = DatasetBrowser(data, schema, "test-dataset")
        
        assert len(browser.data) == 2


class TestDatasetCLICommands:
    """Test dataset CLI commands."""

    def test_dataset_main_help(self):
        """Test dataset main command help."""
        runner = CliRunner()
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Usage:" in result.stdout

    def test_dataset_create_success(self, mock_config, sample_csv_file):
        """Test successful dataset creation."""
        runner = CliRunner()
        
        with patch("mixtrain.client.create_dataset_from_file") as mock_create:
            result = runner.invoke(app, [
                "create", "test-dataset", sample_csv_file,
                "--description", "Test dataset"
            ])
            
            assert result.exit_code == 0
            assert "Dataset 'test-dataset' created successfully" in result.stdout
            assert "Browse with: mixtrain dataset browse test-dataset" in result.stdout
            mock_create.assert_called_once_with("test-dataset", sample_csv_file, "Test dataset")

    def test_dataset_create_without_description(self, mock_config, sample_csv_file):
        """Test dataset creation without description."""
        runner = CliRunner()
        
        with patch("mixtrain.client.create_dataset_from_file") as mock_create:
            result = runner.invoke(app, ["create", "test-dataset", sample_csv_file])
            
            assert result.exit_code == 0
            mock_create.assert_called_once_with("test-dataset", sample_csv_file, None)

    def test_dataset_create_file_not_found(self, mock_config):
        """Test dataset creation with non-existent file."""
        runner = CliRunner()
        
        result = runner.invoke(app, ["create", "test-dataset", "/nonexistent/file.csv"])
        
        assert result.exit_code == 1
        assert "File /nonexistent/file.csv not found" in result.stdout

    def test_dataset_create_unsupported_format(self, mock_config):
        """Test dataset creation with unsupported file format."""
        runner = CliRunner()
        
        with patch("os.path.exists", return_value=True):
            result = runner.invoke(app, ["create", "test-dataset", "test.txt"])
            
            assert result.exit_code == 1
            assert "Only parquet and CSV files are supported" in result.stdout

    def test_dataset_create_api_error(self, mock_config, sample_csv_file):
        """Test dataset creation with API error."""
        runner = CliRunner()
        
        with patch("mixtrain.client.create_dataset_from_file") as mock_create:
            mock_create.side_effect = Exception("API error occurred")
            
            result = runner.invoke(app, ["create", "test-dataset", sample_csv_file])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "API error occurred" in result.stdout

    def test_dataset_list_success(self, mock_config):
        """Test successful dataset listing."""
        runner = CliRunner()
        
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
            
            result = runner.invoke(app, ["list"])
            
            assert result.exit_code == 0
            assert "dataset1" in result.stdout
            assert "dataset2" in result.stdout
            assert "First dataset" in result.stdout
            assert "Second dataset" in result.stdout

    def test_dataset_list_empty(self, mock_config):
        """Test dataset listing with no datasets."""
        runner = CliRunner()
        
        with patch("mixtrain.client.list_datasets") as mock_list:
            mock_list.return_value = {}
            
            result = runner.invoke(app, ["list"])
            
            assert result.exit_code == 0
            assert "No datasets found" in result.stdout

    def test_dataset_list_no_tables_key(self, mock_config):
        """Test dataset listing with missing tables key."""
        runner = CliRunner()
        
        with patch("mixtrain.client.list_datasets") as mock_list:
            mock_list.return_value = {"other_key": "value"}
            
            result = runner.invoke(app, ["list"])
            
            assert result.exit_code == 0
            assert "No datasets found" in result.stdout

    def test_dataset_list_error(self, mock_config):
        """Test dataset listing with error."""
        runner = CliRunner()
        
        with patch("mixtrain.client.list_datasets") as mock_list:
            mock_list.side_effect = Exception("List error")
            
            result = runner.invoke(app, ["list"])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "List error" in result.stdout

    def test_dataset_delete_success(self, mock_config):
        """Test successful dataset deletion."""
        runner = CliRunner()
        
        with patch("mixtrain.client.delete_dataset") as mock_delete:
            result = runner.invoke(app, ["delete", "test-dataset"])
            
            assert result.exit_code == 0
            assert "Table test-dataset deleted successfully" in result.stdout
            mock_delete.assert_called_once_with("test-dataset")

    def test_dataset_delete_error(self, mock_config):
        """Test dataset deletion with error."""
        runner = CliRunner()
        
        with patch("mixtrain.client.delete_dataset") as mock_delete:
            mock_delete.side_effect = Exception("Delete error")
            
            result = runner.invoke(app, ["delete", "test-dataset"])
            
            assert result.exit_code == 1
            assert "Delete error" in result.stdout

    def test_dataset_query_with_custom_sql(self, mock_config):
        """Test dataset query with custom SQL."""
        runner = CliRunner()
        
        # Mock the entire chain of calls
        mock_table = Mock()
        mock_scan = Mock()
        mock_duckdb = Mock()
        mock_arrow_table = Mock()
        
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
                
                result = runner.invoke(app, [
                    "query", "test-dataset", "SELECT * FROM test-dataset LIMIT 10"
                ])
                
                assert result.exit_code == 0
                mock_get.assert_called_once_with("test-dataset")
                mock_duckdb.execute.assert_called_once_with("SELECT * FROM test-dataset LIMIT 10")
                mock_browser.assert_called_once()
                mock_app.run.assert_called_once()

    def test_dataset_query_with_default_sql(self, mock_config):
        """Test dataset query with default SQL."""
        runner = CliRunner()
        
        # Mock the entire chain of calls
        mock_table = Mock()
        mock_scan = Mock()
        mock_duckdb = Mock()
        mock_arrow_table = Mock()
        
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
                
                result = runner.invoke(app, ["query", "test-dataset"])
                
                assert result.exit_code == 0
                # Verify default SQL was used
                mock_duckdb.execute.assert_called_once_with("SELECT * FROM test-dataset LIMIT 100")

    def test_dataset_query_error(self, mock_config):
        """Test dataset query with error."""
        runner = CliRunner()
        
        with patch("mixtrain.client.get_dataset") as mock_get:
            mock_get.side_effect = Exception("Query error")
            
            result = runner.invoke(app, ["query", "test-dataset"])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "Query error" in result.stdout

    def test_dataset_metadata_success(self, mock_config):
        """Test successful dataset metadata retrieval."""
        runner = CliRunner()
        
        mock_metadata = {
            "table_name": "test-dataset",
            "format_version": 2,
            "table_uuid": "test-uuid-123",
            "location": "s3://bucket/path",
            "schema": [
                {"name": "id", "type": "bigint"},
                {"name": "name", "type": "string"},
                {"name": "value", "type": "bigint"}
            ]
        }
        
        with patch("mixtrain.client.get_dataset_metadata") as mock_get:
            mock_get.return_value = mock_metadata
            
            result = runner.invoke(app, ["metadata", "test-dataset"])
            
            assert result.exit_code == 0
            assert "Dataset: test-dataset" in result.stdout
            assert "Format Version: 2" in result.stdout
            assert "Dataset UUID: test-uuid-123" in result.stdout
            assert "Location: s3://bucket/path" in result.stdout
            assert "Schema:" in result.stdout
            assert "id" in result.stdout
            assert "bigint" in result.stdout
            assert "name" in result.stdout
            assert "string" in result.stdout

    def test_dataset_metadata_no_schema(self, mock_config):
        """Test dataset metadata with no schema."""
        runner = CliRunner()
        
        mock_metadata = {
            "table_name": "test-dataset",
            "format_version": 2,
            "table_uuid": "test-uuid-123",
            "location": "s3://bucket/path"
        }
        
        with patch("mixtrain.client.get_dataset_metadata") as mock_get:
            mock_get.return_value = mock_metadata
            
            result = runner.invoke(app, ["metadata", "test-dataset"])
            
            assert result.exit_code == 0
            assert "Dataset: test-dataset" in result.stdout
            assert "Schema:" not in result.stdout

    def test_dataset_metadata_empty_response(self, mock_config):
        """Test dataset metadata with empty response."""
        runner = CliRunner()
        
        with patch("mixtrain.client.get_dataset_metadata") as mock_get:
            mock_get.return_value = None
            
            result = runner.invoke(app, ["metadata", "test-dataset"])
            
            assert result.exit_code == 0
            assert "No metadata returned" in result.stdout

    def test_dataset_metadata_error(self, mock_config):
        """Test dataset metadata with error."""
        runner = CliRunner()
        
        with patch("mixtrain.client.get_dataset_metadata") as mock_get:
            mock_get.side_effect = Exception("Metadata error")
            
            result = runner.invoke(app, ["metadata", "test-dataset"])
            
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "Metadata error" in result.stdout


class TestDatasetBrowserInteraction:
    """Test DatasetBrowser interactive features."""

    def test_dataset_browser_key_events(self):
        """Test DatasetBrowser key event handling."""
        data = [{"id": 1, "name": "test"}]
        schema = ["id", "name"]
        browser = DatasetBrowser(data, schema, "test-dataset")
        
        # Mock the exit method
        browser.exit = Mock()
        
        # Create a mock key event
        class MockKeyEvent:
            def __init__(self, key):
                self.key = key
        
        # Test 'q' key (quit)
        browser.on_key(MockKeyEvent("q"))
        browser.exit.assert_called_once()

    def test_dataset_browser_search_functionality(self):
        """Test DatasetBrowser search functionality."""
        data = [
            ["1", "test1", "100"],
            ["2", "test2", "200"],
            ["3", "other", "300"]
        ]
        schema = ["id", "name", "value"]
        browser = DatasetBrowser(data, schema, "test-dataset")
        
        # Set up the data after normalization
        browser.data = data
        
        # Mock the table and search input
        browser.table = Mock()
        browser.search_input = Mock()
        
        # Create a mock input change event
        class MockInputChanged:
            def __init__(self, value):
                self.value = value
        
        # Test search functionality
        browser.on_input_changed(MockInputChanged("test"))
        
        # Verify table was cleared and rows were added
        browser.table.clear.assert_called_once_with(columns=False)
        # Should add rows containing "test"
        assert browser.table.add_row.call_count >= 1

    def test_dataset_browser_escape_key(self):
        """Test DatasetBrowser escape key handling."""
        data = [{"id": 1, "name": "test"}]
        schema = ["id", "name"]
        browser = DatasetBrowser(data, schema, "test-dataset")
        
        # Mock components
        browser.search_input = Mock()
        browser.table = Mock()
        browser.on_input_changed = Mock()
        
        class MockKeyEvent:
            def __init__(self, key):
                self.key = key
        
        # Test escape key
        browser.on_key(MockKeyEvent("escape"))
        
        # Should clear search and focus table
        assert browser.search_input.value == ""
        browser.table.focus.assert_called_once()

    def test_dataset_browser_ctrl_f_key(self):
        """Test DatasetBrowser Ctrl+F key handling."""
        data = [{"id": 1, "name": "test"}]
        schema = ["id", "name"]
        browser = DatasetBrowser(data, schema, "test-dataset")
        
        # Mock search input
        browser.search_input = Mock()
        
        class MockKeyEvent:
            def __init__(self, key):
                self.key = key
        
        # Test Ctrl+F key
        browser.on_key(MockKeyEvent("ctrl+f"))
        
        # Should focus search input
        browser.search_input.focus.assert_called_once()
