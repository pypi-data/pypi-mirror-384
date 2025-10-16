"""Tests for mixtrain CLI commands."""

import os
from typer.testing import CliRunner
from mixtrain.cli import app, __version__


# run only if ~/.mixtrain/config.json exists
assert os.path.exists(os.path.expanduser("~/.mixtrain/config.json"))

TEST_WORKSPACE = "dharmeshkakadia-personal"
TEST_DATASET = "video_eval"
TEST_DATASET_LOCATION = (
    "gs://morphic-research/annahouse/iceberg_data/dharmeshkakadia-personal/video_eval"
)
TEST_SECRET = "CATALOG_TYPE"
TEST_SECRET_VALUE = "sql"
TEST_ROUTING_CONFIG_ID = 14
TEST_ROUTING_CONFIG_NAME = "CLI output"
TEST_ROUTING_CONFIG_OUTPUT = os.path.join(
    os.path.dirname(__file__), "config_14_view_output.json"
)


class TestCLIRealToken:
    """Test CLI real token commands."""

    def setup_method(self):
        self.env = {
            "MIXTRAIN_PLATFORM_URL": "http://localhost:8000/api/v1",
            "FRONTEND_URL": "http://localhost:5173",
        }
        self.runner = CliRunner()

    def test_app_version(self):
        result = self.runner.invoke(app, ["--version"], env=self.env)
        assert result.exit_code == 0
        assert "mixtrain" in result.stdout
        assert __version__ in result.stdout

    ## Secret commands

    def test_app_secret_list(self):
        result = self.runner.invoke(app, ["secret", "list"], env=self.env)
        print(result.stdout)
        assert result.exit_code == 0
        assert "No secrets found" not in result.stdout
        assert "Name" in result.stdout
        assert "Description" in result.stdout
        assert "Created" in result.stdout
        assert "Created By" in result.stdout

    def test_app_secret_get(self):
        result = self.runner.invoke(app, ["secret", "get", TEST_SECRET], env=self.env)
        print(result.stdout)
        assert result.exit_code == 0
        assert TEST_SECRET in result.stdout
        assert "Description" in result.stdout
        assert "Created" in result.stdout
        assert "Hidden (use --show to display)" in result.stdout
        assert TEST_SECRET_VALUE not in result.stdout
        assert "Created by" in result.stdout
        assert "💡 Use --show to display the secret value" in result.stdout

    def test_app_secret_get_show(self):
        result = self.runner.invoke(
            app, ["secret", "get", TEST_SECRET, "--show"], env=self.env
        )
        print(result.stdout)
        assert result.exit_code == 0
        assert TEST_SECRET in result.stdout
        assert "Description" in result.stdout
        assert "Created" in result.stdout
        assert "Created by" in result.stdout
        assert TEST_SECRET_VALUE in result.stdout
        assert "Hidden (use --show to display)" not in result.stdout
        assert "💡 Use --show to display the secret value" not in result.stdout

    ## Workspace commands

    def test_app_workspace_list(self):
        result = self.runner.invoke(app, ["workspace", "list"], env=self.env)
        print(result.stdout)
        assert result.exit_code == 0
        assert "No workspaces found" not in result.stdout
        assert "Name" in result.stdout
        assert "Description" in result.stdout
        assert "Role" in result.stdout
        assert "Members" in result.stdout
        assert "Created At" in result.stdout
        assert TEST_WORKSPACE[:10] in result.stdout

    ## Dataset commands

    def test_app_dataset_list(self):
        result = self.runner.invoke(app, ["dataset", "list"], env=self.env)
        print(result.stdout)
        assert result.exit_code == 0
        assert "No datasets found" not in result.stdout
        assert "dataset_name" in result.stdout
        assert "namespace" in result.stdout
        assert "description" in result.stdout
        assert TEST_DATASET in result.stdout
        assert TEST_WORKSPACE in result.stdout

    def test_app_dataset_metadata(self):
        result = self.runner.invoke(
            app, ["dataset", "metadata", TEST_DATASET], env=self.env
        )
        print(result.stdout)
        assert result.exit_code == 0
        assert TEST_DATASET in result.stdout
        assert "Format Version: 2" in result.stdout
        assert "Dataset UUID: " in result.stdout
        assert f"Location: {TEST_DATASET_LOCATION}" in result.stdout
        assert "schema: table {" in result.stdout

    # Routing commands

    def test_app_routing_list_configs(self):
        result = self.runner.invoke(app, ["routing", "list-configs"], env=self.env)
        print(result.stdout)
        assert result.exit_code == 0
        assert "No routing configurations found" not in result.stdout
        assert "ID" in result.stdout
        assert "Name" in result.stdout
        assert "Status" in result.stdout
        assert "Descrip" in result.stdout
        assert "Version" in result.stdout
        assert "Created" in result.stdout
        assert "Updated" in result.stdout
        assert TEST_ROUTING_CONFIG_NAME in result.stdout
        assert str(TEST_ROUTING_CONFIG_ID) in result.stdout

    def test_app_routing_view_config(self):
        result = self.runner.invoke(
            app,
            [
                "routing",
                "view",
                str(TEST_ROUTING_CONFIG_ID),
                "--json",
            ],
            env=self.env,
        )
        expected_response = open(TEST_ROUTING_CONFIG_OUTPUT, "r").read()
        assert result.exit_code == 0
        assert expected_response == result.stdout
