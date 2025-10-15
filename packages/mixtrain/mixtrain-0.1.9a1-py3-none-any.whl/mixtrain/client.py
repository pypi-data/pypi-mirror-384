"""MixClient - Client for Mixtrain SDK

This module provides the core MixClient class that handles authentication,
workspace management, and all API operations for the Mixtrain platform.
"""

import json
import os
from enum import Enum
from functools import lru_cache
from logging import getLogger
from typing import Any, Dict, List, Optional

import httpx
from mixtrain.routing.engine import RoutingEngineFactory
from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table

from .utils import auth as auth_utils
from .utils.config import get_config

logger = getLogger(__name__)


class AuthMethod(Enum):
    """Authentication methods supported by MixClient."""

    API_KEY = "api_key"
    LOGIN_TOKEN = "login_token"


def detect_rule_changes(
    old_rules: List[Dict[str, Any]], new_rules: List[Dict[str, Any]]
) -> str:
    """Detect changes between rule sets using JSON diff approach."""

    def rules_are_equal(rule1: Dict[str, Any], rule2: Dict[str, Any]) -> bool:
        """Compare two rules ignoring ID fields."""
        clean1 = {k: v for k, v in rule1.items() if k != "id"}
        clean2 = {k: v for k, v in rule2.items() if k != "id"}
        return json.dumps(clean1, sort_keys=True) == json.dumps(clean2, sort_keys=True)

    def get_rule_name(rule: Dict[str, Any], index: int) -> str:
        """Generate rule name for display."""
        return rule.get("name") or f"Rule {index + 1}"

    # Handle initial configuration
    if not old_rules:
        if new_rules:
            rule_names = [get_rule_name(rule, i) for i, rule in enumerate(new_rules)]
            return f"Added {', '.join(rule_names)}"
        return "Initial configuration"

    # Handle all rules deleted
    if not new_rules:
        rule_names = [get_rule_name(rule, i) for i, rule in enumerate(old_rules)]
        return f"Deleted all rules ({', '.join(rule_names)})"

    old_len = len(old_rules)
    new_len = len(new_rules)

    changes = []
    edited = []
    added = []
    deleted = []

    # Compare rules that exist in both (up to the shorter length)
    min_len = min(old_len, new_len)
    for i in range(min_len):
        if not rules_are_equal(old_rules[i], new_rules[i]):
            edited.append(get_rule_name(new_rules[i], i))

    # Handle length differences
    if new_len > old_len:
        # Rules were added
        for i in range(old_len, new_len):
            added.append(get_rule_name(new_rules[i], i))
    elif old_len > new_len:
        # Rules were deleted
        for i in range(new_len, old_len):
            deleted.append(get_rule_name(old_rules[i], i))

    # Build summary
    if added:
        changes.append(f"Added {', '.join(added)}")
    if edited:
        changes.append(f"Edited {', '.join(edited)}")
    if deleted:
        changes.append(f"Deleted {', '.join(deleted)}")

    return "; ".join(changes) if changes else "No rule changes"


class MixClient:
    """Main client for interacting with the Mixtrain platform.

    Handles authentication, workspace management, and all API operations.

    Usage:
        # Auto-detect authentication and workspace
        client = MixClient()

        # API key authentication - scoped to the key's workspace and role
        client = MixClient(api_key="mix-abc123")

        # Login token with specific workspace
        client = MixClient(workspace_name="my-workspace")

    Note:
        API keys authenticate to a specific workspace with a specific role (ADMIN/MEMBER/VIEWER).
        Each API key can only access its assigned workspace and cannot perform user-specific
        operations like managing invitations or creating new workspaces.

        The workspace_name parameter is automatically determined from the API key and should
        not be manually specified when using API key authentication.
    """

    def __init__(
        self, workspace_name: Optional[str] = None, api_key: Optional[str] = None
    ):
        """Initialize MixClient.

        Args:
            workspace_name: Workspace to use (only for login token auth).
                          For API keys, workspace is auto-determined.
            api_key: API key for authentication. If not provided, will check environment
                    or fall back to login token.
        """
        self._explicit_workspace = workspace_name
        self._explicit_api_key = api_key
        self._auth_method = self._detect_auth_method()

        # Validate that workspace_name is not provided with API key
        if self._auth_method == AuthMethod.API_KEY and workspace_name:
            raise ValueError(
                "workspace_name should not be specified when using API key authentication. "
                "The workspace is automatically determined from the API key."
            )

        self._workspace_name = self._determine_workspace_name()

    def _detect_auth_method(self) -> AuthMethod:
        """Detect which authentication method to use."""
        # Priority: explicit API key > env API key > login token
        if self._explicit_api_key:
            if not self._explicit_api_key.startswith("mix-"):
                raise ValueError("API key must start with 'mix-'")
            return AuthMethod.API_KEY

        env_api_key = os.getenv("MIXTRAIN_API_KEY")
        if env_api_key:
            if not env_api_key.startswith("mix-"):
                raise ValueError(
                    "MIXTRAIN_API_KEY environment variable must start with 'mix-'"
                )
            return AuthMethod.API_KEY

        # Check if we have a login token
        config = get_config()
        if config.get_auth_token():
            return AuthMethod.LOGIN_TOKEN

        raise ValueError(
            "No authentication method available. "
            "Please set MIXTRAIN_API_KEY environment variable or authenticate with 'mixtrain login'"
        )

    def _determine_workspace_name(self) -> str:
        """Determine which workspace to use."""
        if self._explicit_workspace:
            return self._explicit_workspace

        if self._auth_method == AuthMethod.API_KEY:
            # For API key auth, the key is workspace-specific, so we can determine the workspace
            # from the key itself by calling the workspaces endpoint. Since the API key belongs to
            # a specific workspace, it will only have access to that workspace.
            workspaces = self._list_workspaces_raw()
            workspace_list = workspaces.get("data", [])
            if not workspace_list:
                raise ValueError("No workspaces available with current API key")

            # Since API keys are workspace-specific, there should typically be only one workspace
            # If there are multiple, use the first one (the key has access to it)
            return workspace_list[0]["name"]

        else:  # LOGIN_TOKEN
            # For login token, use configured active workspace
            config = get_config()
            active_workspace = next((w for w in config.workspaces if w.active), None)
            if not active_workspace:
                raise ValueError(
                    "No active workspace found. Please authenticate with 'mixtrain login'"
                )
            return active_workspace.name

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        if self._auth_method == AuthMethod.API_KEY:
            api_key = self._explicit_api_key or os.getenv("MIXTRAIN_API_KEY")
            return {"X-API-Key": api_key}
        else:  # LOGIN_TOKEN
            config = get_config()
            auth_token = config.get_auth_token()
            if not auth_token:
                raise ValueError("No auth token available")
            return {"Authorization": f"Bearer {auth_token}"}

    def _get_platform_url(self) -> str:
        """Get platform URL with environment variable override."""
        return os.getenv("MIXTRAIN_PLATFORM_URL", "https://platform.mixtrain.ai/api/v1")

    def _make_request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make HTTP request to the platform API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (will be prefixed with platform URL)
            json: JSON payload
            files: Files to upload
            params: Query parameters
            headers: Additional headers

        Returns:
            HTTP response object

        Raises:
            Exception: On HTTP errors or connection issues
        """
        with httpx.Client(timeout=10.0) as client:
            # Prepare headers
            request_headers = self._get_auth_headers()
            if headers:
                request_headers.update(headers)

            # Build full URL
            url = f"{self._get_platform_url()}{path}"

            logger.debug(f"Making {method} request to {url}")

            try:
                if files:
                    response = client.request(
                        method, url, files=files, params=params, headers=request_headers
                    )
                else:
                    response = client.request(
                        method, url, json=json, params=params, headers=request_headers
                    )

                if response.status_code != 200:
                    try:
                        error_detail = response.json().get("detail", response.text)
                    except:
                        error_detail = response.text

                    logger.error(f"API error {response.status_code}: {error_detail}")
                    raise Exception(
                        f"API error ({response.status_code}): {error_detail}"
                    )

                return response

            except httpx.RequestError as exc:
                logger.error(f"Request error for {url}: {exc}")
                raise Exception(f"Network error: {exc}")

    @property
    def workspace_name(self) -> str:
        """Get current workspace name."""
        return self._workspace_name

    @property
    def auth_method(self) -> AuthMethod:
        """Get current authentication method."""
        return self._auth_method

    # Workspace operations
    def _list_workspaces_raw(self) -> Dict[str, Any]:
        """Internal method to list workspaces (used during initialization)."""
        response = self._make_request("GET", "/workspaces/list")
        return response.json()

    def list_workspaces(self) -> Dict[str, Any]:
        """List all workspaces the user has access to."""
        response = self._make_request("GET", "/workspaces/list")
        return response.json()

    def create_workspace(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new workspace."""
        response = self._make_request(
            "POST", "/workspaces/", json={"name": name, "description": description}
        )
        return response.json()

    def delete_workspace(self, workspace_name: str) -> Dict[str, Any]:
        """Delete a workspace."""
        response = self._make_request("DELETE", f"/workspaces/{workspace_name}")
        return response.json()

    # Dataset operations
    def list_datasets(self) -> Dict[str, Any]:
        """List all datasets in the current workspace."""
        response = self._make_request(
            "GET", f"/lakehouse/workspaces/{self._workspace_name}/tables"
        )
        return response.json()

    # Evaluation operations
    def list_evaluations(self) -> Dict[str, Any]:
        """List all evaluations in the current workspace."""
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/evaluations/"
        )
        return response.json()

    def create_evaluation(
        self, name: str, config: Dict[str, Any], description: str = ""
    ) -> Dict[str, Any]:
        """Create a new evaluation in the current workspace."""
        payload = {"name": name, "description": description, "config": config}
        response = self._make_request(
            "POST", f"/workspaces/{self._workspace_name}/evaluations/", json=payload
        )
        return response.json()

    def get_evaluation(self, evaluation_name: str) -> Dict[str, Any]:
        """Get a specific evaluation by name.

        Args:
            evaluation_name: Name of the evaluation (slug format: lowercase, hyphens only)

        Returns:
            Evaluation data
        """
        # evaluation_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/evaluations/{evaluation_name}"
        )
        return response.json()

    def update_evaluation(
        self,
        evaluation_name: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update fields on an evaluation.

        Args:
            evaluation_name: Current name of the evaluation
            name: Optional new name for the evaluation
            description: Optional new description
            config: Optional new config
            status: Optional new status

        Returns:
            Updated evaluation data
        """
        # evaluation_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if config is not None:
            payload["config"] = config
        if status is not None:
            payload["status"] = status
        response = self._make_request(
            "PUT",
            f"/workspaces/{self._workspace_name}/evaluations/{evaluation_name}",
            json=payload,
        )
        return response.json()

    def delete_evaluation(self, evaluation_name: str) -> Dict[str, Any]:
        """Delete an evaluation by name.

        Args:
            evaluation_name: Name of the evaluation to delete

        Returns:
            Deletion result
        """
        # evaluation_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        response = self._make_request(
            "DELETE",
            f"/workspaces/{self._workspace_name}/evaluations/{evaluation_name}",
        )
        return response.json()

    def get_evaluation_data(
        self,
        datasets: List[Dict[str, Any]],
        evaluation_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Fetch evaluation data for side-by-side comparison across datasets.

        Args:
            datasets: List of dataset configs with keys: tableName, columnName, dataType.
            evaluation_name: Optional evaluation name for caching.
            limit: Page size.
            offset: Offset for pagination.
        """
        payload: Dict[str, Any] = {
            "datasets": datasets,
            "limit": limit,
            "offset": offset,
        }
        if evaluation_name is not None:
            payload["evaluationName"] = evaluation_name
        response = self._make_request(
            "POST",
            f"/lakehouse/workspaces/{self._workspace_name}/evaluation/data",
            json=payload,
        )
        return response.json()

    def create_dataset_from_file(
        self,
        name: str,
        file_path: str,
        description: Optional[str] = None,
        provider_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a dataset from a file using the lakehouse API."""
        headers = {}
        if description:
            headers["X-Description"] = description

        if not provider_type:
            provider_type = "apache_iceberg"

        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1], f, "application/octet-stream")}
            response = self._make_request(
                "POST",
                f"/lakehouse/workspaces/{self._workspace_name}/tables/{name}?provider_type={provider_type}",
                files=files,
                headers=headers,
            )
        return response.json()

    def delete_dataset(self, name: str) -> httpx.Response:
        """Delete a dataset."""
        return self._make_request(
            "DELETE", f"/lakehouse/workspaces/{self._workspace_name}/tables/{name}"
        )

    def upload_file(self, dataset_name: str, file_path: str) -> Dict[str, Any]:
        """Upload a file to a dataset."""
        with open(file_path, "rb") as f:
            response = self._make_request(
                "POST",
                f"/datasets/{self._workspace_name}/{dataset_name}/upload",
                files={"file": f},
            )
            return response.json().get("data")

    @lru_cache(maxsize=1)
    def get_catalog(self) -> Any:
        """Get PyIceberg catalog for the workspace."""
        try:
            provider_secrets = self._make_request(
                "GET",
                f"/workspaces/{self._workspace_name}/dataset-providers/type/apache_iceberg",
            ).json()

            if provider_secrets["provider_type"] != "apache_iceberg":
                raise Exception(
                    f"Dataset provider {provider_secrets['provider_type']} is not supported"
                )

            if (
                os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is None
                and provider_secrets["secrets"]["CATALOG_WAREHOUSE_URI"].startswith(
                    "gs://"
                )
                and provider_secrets["secrets"]["SERVICE_ACCOUNT_JSON"]
            ):
                service_account_json = provider_secrets["secrets"][
                    "SERVICE_ACCOUNT_JSON"
                ]
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
                    f"/tmp/{self._workspace_name}/service_account.json"
                )

                # Set up Google Cloud credentials (temporary file)
                os.makedirs(f"/tmp/mixtrain/{self._workspace_name}", exist_ok=True)
                with open(
                    f"/tmp/mixtrain/{self._workspace_name}/service_account.json", "w"
                ) as f:
                    f.write(service_account_json)

                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
                    f"/tmp/mixtrain/{self._workspace_name}/service_account.json"
                )

            # Load the catalog
            catalog_config = {
                "type": provider_secrets["secrets"]["CATALOG_TYPE"],
                "uri": provider_secrets["secrets"]["CATALOG_URI"],
                "warehouse": provider_secrets["secrets"]["CATALOG_WAREHOUSE_URI"],
            }
            catalog = load_catalog("default", **catalog_config)
            return catalog

        except Exception as e:
            raise Exception(f"Failed to load catalog: {e}")

    def get_dataset(self, name: str) -> Table:
        """Get an Iceberg table using workspace secrets and PyIceberg catalog API."""
        catalog = self.get_catalog()
        table_identifier = f"{self._workspace_name}.{name}"
        table = catalog.load_table(table_identifier)
        return table

    def get_dataset_metadata(self, name: str) -> Any:
        """Get detailed metadata for a table."""
        return self.get_dataset(name).metadata

    # Dataset provider operations
    def list_dataset_providers(self) -> Dict[str, Any]:
        """List available and onboarded dataset providers."""
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/dataset-providers/"
        )
        return response.json()

    def create_dataset_provider(
        self, provider_type: str, secrets: Dict[str, str]
    ) -> Dict[str, Any]:
        """Onboard a new dataset provider for the workspace."""
        payload = {"provider_type": provider_type, "secrets": secrets}
        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/dataset-providers/",
            json=payload,
        )
        return response.json()

    def update_dataset_provider(
        self, provider_id: int, secrets: Dict[str, str]
    ) -> Dict[str, Any]:
        """Update secrets for an existing dataset provider."""
        payload = {"secrets": secrets}
        response = self._make_request(
            "PUT",
            f"/workspaces/{self._workspace_name}/dataset-providers/{provider_id}",
            json=payload,
        )
        return response.json()

    def delete_dataset_provider(self, provider_id: int) -> Dict[str, Any]:
        """Remove a dataset provider from the workspace."""
        response = self._make_request(
            "DELETE",
            f"/workspaces/{self._workspace_name}/dataset-providers/{provider_id}",
        )
        return response.json()

    # Model provider operations
    def list_model_providers(self) -> Dict[str, Any]:
        """List available and onboarded model providers."""
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/models/providers"
        )
        return response.json()

    def create_model_provider(
        self, provider_type: str, secrets: Dict[str, str]
    ) -> Dict[str, Any]:
        """Onboard a new model provider for the workspace."""
        payload = {"provider_type": provider_type, "secrets": secrets}
        response = self._make_request(
            "POST", f"/workspaces/{self._workspace_name}/models/providers", json=payload
        )
        return response.json()

    def update_model_provider(
        self, provider_id: int, secrets: Dict[str, str]
    ) -> Dict[str, Any]:
        """Update secrets for an existing model provider."""
        payload = {"secrets": secrets}
        response = self._make_request(
            "PUT",
            f"/workspaces/{self._workspace_name}/models/providers/{provider_id}",
            json=payload,
        )
        return response.json()

    def delete_model_provider(self, provider_id: int) -> Dict[str, Any]:
        """Remove a model provider from the workspace."""
        response = self._make_request(
            "DELETE",
            f"/workspaces/{self._workspace_name}/models/providers/{provider_id}",
        )
        return response.json()

    # Secret operations
    def get_secret(self, secret_name: str) -> str:
        """Get a secret value by name.

        Args:
            secret_name: Name of the secret to retrieve

        Returns:
            The decoded secret value as a string

        Raises:
            Exception: If secret is not found or there's an API error
        """
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/secrets/{secret_name}"
        )
        secret_data = response.json()
        return secret_data.get("value", "")

    def get_all_secrets(self) -> Dict[str, Any]:
        """Get all secrets in the current workspace."""
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/secrets/"
        )
        return response.json()

    def list_models(self) -> Dict[str, Any]:
        """List all internal models in the current workspace."""
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/models/"
        )
        return response.json()

    # Routing configuration operations
    def list_routing_configs(self, status: Optional[str] = None) -> Dict[str, Any]:
        """List all routing configurations in the workspace.

        Args:
            status: Optional filter by status ('active', 'inactive')

        Returns:
            Dict with 'data' key containing list of routing configuration summaries
        """
        params = {"status": status} if status else None
        response = self._make_request(
            "GET",
            f"/workspaces/{self._workspace_name}/inference/configs",
            params=params,
        )
        return response.json()

    def get_routing_config(
        self, config_id: int, version: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get a specific routing configuration.

        Args:
            config_id: ID of the routing configuration
            version: Optional specific version to retrieve

        Returns:
            Full routing configuration with rules and metadata
        """
        params = {"version": version} if version else None
        response = self._make_request(
            "GET",
            f"/workspaces/{self._workspace_name}/inference/configs/{config_id}",
            params=params,
        )
        return response.json()

    def get_active_routing_config(self) -> Optional[Dict[str, Any]]:
        """Get the currently active routing configuration for the workspace.

        Returns:
            Active routing configuration dict or None if no active config
        """
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/inference/active-config"
        )
        result = response.json()
        if not result:
            raise Exception("No active routing configuration found in workspace")
        return result

    def get_routing_engine(
        self, config_id: Optional[int] = None, version: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get the currently active routing engine for the workspace.

        Returns:
            Routing engine instance
        """
        if config_id:
            config = self.get_routing_config(config_id, version=version)
        else:
            config = self.get_active_routing_config()
        return RoutingEngineFactory.from_json(config)

    def create_routing_config(
        self, name: str, description: str, rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a new routing configuration.

        Args:
            name: Name of the configuration
            description: Description of the configuration
            rules: List of routing rules

        Returns:
            Created routing configuration
        """
        payload = {"name": name, "description": description, "rules": rules}
        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/inference/configs",
            json=payload,
        )
        return response.json()

    def update_routing_config(
        self,
        config_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        rules: Optional[List[Dict[str, Any]]] = None,
        change_message: None = None,
    ) -> Dict[str, Any]:
        """Update a routing configuration (creates a new version).

        Args:
            config_id: ID of the configuration to update
            name: Optional new name
            description: Optional new description
            rules: Optional new rules list

        Returns:
            Updated routing configuration
        """
        payload = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if rules is not None:
            payload["rules"] = rules

            # Detect rule changes and generate change summary
            try:
                # Get current config to compare rules
                current_config = self.get_routing_config(config_id)
                old_rules = current_config.get("rules", [])
                _change_message = change_message or detect_rule_changes(
                    old_rules, rules
                )
                payload["change_message"] = _change_message
            except Exception as e:
                # If we can't get the current config, fall back to generic message
                logger.warning(
                    f"Failed to detect rule changes for config {config_id}: {e}"
                )
                payload["change_message"] = "Configuration updated via CLI"

        response = self._make_request(
            "PUT",
            f"/workspaces/{self._workspace_name}/inference/configs/{config_id}",
            json=payload,
        )
        return response.json()

    def activate_routing_config(
        self, config_id: int, version: Optional[int] = None
    ) -> Dict[str, Any]:
        """Activate a routing configuration.

        Args:
            config_id: ID of the configuration to activate
            version: Optional specific version to activate

        Returns:
            Activation result
        """
        payload = {}
        if version is not None:
            payload["version"] = version

        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/inference/configs/{config_id}/activate",
            json=payload,
        )
        return response.json()

    def delete_routing_config(self, config_id: int) -> Dict[str, Any]:
        """Delete a routing configuration and all its versions.

        Args:
            config_id: ID of the configuration to delete

        Returns:
            Deletion result
        """
        response = self._make_request(
            "DELETE",
            f"/workspaces/{self._workspace_name}/inference/configs/{config_id}",
        )
        return response.json()

    def test_routing_config(
        self, config_id: int, test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test routing configuration against sample data.

        Args:
            config_id: ID of the configuration to test
            test_data: Sample request data for testing

        Returns:
            Test results with matched rule and targets
        """
        payload = {"config_id": config_id, "test_data": test_data}
        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/inference/configs/{config_id}/test",
            json=payload,
        )
        return response.json()

    def get_routing_config_versions(self, config_id: int) -> Dict[str, Any]:
        """Get all versions of a routing configuration.

        Args:
            config_id: ID of the configuration

        Returns:
            List of all configuration versions
        """
        response = self._make_request(
            "GET",
            f"/workspaces/{self._workspace_name}/inference/configs/{config_id}/versions",
        )
        return response.json()

    # Workflow operations
    def list_workflows(self) -> Dict[str, Any]:
        """List all workflows in the workspace."""
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/workflows/"
        )
        return response.json()

    def create_workflow(
        self,
        name: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """Create a new workflow."""
        payload = {
            "name": name,
            "description": description,
        }
        response = self._make_request(
            "POST", f"/workspaces/{self._workspace_name}/workflows/", json=payload
        )
        return response.json()

    def create_workflow_with_files(
        self,
        name: str,
        workflow_file: str,
        src_files: List[str],
        description: str = "",
    ) -> Dict[str, Any]:
        """Create a new workflow with file uploads."""
        import os

        # Prepare files dict for multipart/form-data
        files = {}
        data = {}

        # Add form fields
        data["name"] = (None, name)
        data["description"] = (None, description)

        # Add workflow file
        workflow_file_handle = open(workflow_file, "rb")
        files["workflow_file"] = (
            os.path.basename(workflow_file),
            workflow_file_handle,
            "application/octet-stream",
        )

        # Add source files
        src_file_handles = []
        for src_file in src_files:
            src_file_handle = open(src_file, "rb")
            src_file_handles.append(src_file_handle)
            if "src_files" not in files:
                files["src_files"] = []
            files["src_files"].append(
                (
                    os.path.basename(src_file),
                    src_file_handle,
                    "application/octet-stream",
                )
            )

        try:
            # Combine data and files for upload
            files.update(data)

            response = self._make_request(
                "POST",
                f"/workspaces/{self._workspace_name}/workflows/",
                files=files,
            )
            return response.json()
        finally:
            # Close all file handles
            workflow_file_handle.close()
            for handle in src_file_handles:
                handle.close()

    def get_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Get a specific workflow with its runs.

        Args:
            workflow_name: Name of the workflow (slug format: lowercase, hyphens only)

        Returns:
            Workflow data with runs
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/workflows/{workflow_name}"
        )
        return response.json()

    def update_workflow(
        self,
        workflow_name: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a workflow.

        Args:
            workflow_name: Current name of the workflow
            name: Optional new name for the workflow
            description: Optional new description

        Returns:
            Updated workflow data
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        payload = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description

        response = self._make_request(
            "PUT",
            f"/workspaces/{self._workspace_name}/workflows/{workflow_name}",
            json=payload,
        )
        return response.json()

    def delete_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Delete a workflow.

        Args:
            workflow_name: Name of the workflow to delete

        Returns:
            Deletion result
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        response = self._make_request(
            "DELETE", f"/workspaces/{self._workspace_name}/workflows/{workflow_name}"
        )
        return response.json()

    def list_workflow_runs(self, workflow_name: str) -> Dict[str, Any]:
        """List all runs for a workflow.

        Args:
            workflow_name: Name of the workflow

        Returns:
            List of workflow runs
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        response = self._make_request(
            "GET", f"/workspaces/{self._workspace_name}/workflows/{workflow_name}/runs"
        )
        return response.json()

    def start_workflow_run(
        self, workflow_name: str, json_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Start a new workflow run with optional configuration overrides.

        Args:
            workflow_name: Name of the workflow to run
            json_config: Optional configuration to override workflow defaults

        Returns:
            Workflow run data
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        payload = {"json_config": json_config or {}}
        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/workflows/{workflow_name}/runs",
            json=payload,
        )
        return response.json()

    def get_workflow_run(self, workflow_name: str, run_number: int) -> Dict[str, Any]:
        """Get a specific workflow run.

        Args:
            workflow_name: Name of the workflow
            run_number: Per-workflow run number (1, 2, 3...)

        Returns:
            Workflow run data
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9-]{0,62}$), encoding not needed
        response = self._make_request(
            "GET",
            f"/workspaces/{self._workspace_name}/workflows/{workflow_name}/runs/{run_number}",
        )
        return response.json()

    def update_workflow_run_status(
        self,
        workflow_name: str,
        run_number: int,
        status: Optional[str] = None,
        json_config: Optional[Dict[str, Any]] = None,
        logs_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a workflow run status and other fields.

        Args:
            workflow_name: Name of the workflow
            run_number: Per-workflow run number
            status: Optional new status. Valid values: 'pending', 'running', 'completed', 'failed', 'cancelled'
            json_config: Optional configuration to override
            logs_url: Optional URL to the run logs

        Returns:
            Updated workflow run data
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9-]{0,62}$), encoding not needed
        payload = {}
        if status is not None:
            payload["status"] = status
        if json_config is not None:
            payload["json_config"] = json_config
        if logs_url is not None:
            payload["logs_url"] = logs_url

        response = self._make_request(
            "PUT",
            f"/workspaces/{self._workspace_name}/workflows/{workflow_name}/runs/{run_number}",
            json=payload,
        )
        return response.json()

    def cancel_workflow_run(
        self, workflow_name: str, run_number: int
    ) -> Dict[str, Any]:
        """Cancel a running workflow.

        Args:
            workflow_name: Name of the workflow
            run_number: Per-workflow run number to cancel

        Returns:
            Cancellation result
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9-]{0,62}$), encoding not needed
        response = self._make_request(
            "POST",
            f"/workspaces/{self._workspace_name}/workflows/{workflow_name}/runs/{run_number}/cancel",
            json={},
        )
        return response.json()

    # Authentication operations
    def authenticate_browser(self) -> str:
        """Authenticate using browser-based OAuth flow."""
        return auth_utils.authenticate_browser(get_config, self._make_request_for_auth)

    def authenticate_with_token(self, token: str, provider: str) -> str:
        """Authenticate using OAuth token (GitHub or Google)."""
        return auth_utils.authenticate_with_token(
            token, provider, get_config, self._make_request_for_auth
        )

    def authenticate_github(self, access_token: str) -> str:
        """Authenticate using GitHub access token."""
        return auth_utils.authenticate_github(
            access_token, get_config, self._make_request_for_auth
        )

    def authenticate_google(self, id_token: str) -> str:
        """Authenticate using Google ID token."""
        return auth_utils.authenticate_google(
            id_token, get_config, self._make_request_for_auth
        )

    def _make_request_for_auth(
        self, method: str, path: str, **kwargs
    ) -> httpx.Response:
        """Helper method for authentication flows that don't need full client setup."""
        # This is a simpler version used during auth flows before client is fully initialized
        with httpx.Client(timeout=10.0) as client:
            url = f"{self._get_platform_url()}{path}"
            response = client.request(method, url, **kwargs)
            if response.status_code != 200:
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text
                raise Exception(f"Auth error ({response.status_code}): {error_detail}")
            return response


# Backward compatibility functions - delegate to default MixClient instance


def call_api(method: str, endpoint: str, **kwargs) -> httpx.Response:
    """Make an API call using the default MixClient instance."""
    client = MixClient()
    return client._make_request(method, endpoint, **kwargs)


def list_workspaces() -> Dict[str, Any]:
    """List workspaces using the default MixClient instance."""
    client = MixClient()
    return client.list_workspaces()


def create_workspace(name: str, description: str = "") -> Dict[str, Any]:
    """Create a workspace using the default MixClient instance."""
    client = MixClient()
    return client.create_workspace(name, description)


def delete_workspace(name: str) -> Dict[str, Any]:
    """Delete a workspace using the default MixClient instance."""
    client = MixClient()
    return client.delete_workspace(name)


def list_models() -> Dict[str, Any]:
    """List models using the default MixClient instance."""
    client = MixClient()
    return client.list_models()


def list_model_providers() -> Dict[str, Any]:
    """List model providers using the default MixClient instance."""
    client = MixClient()
    return client.list_model_providers()


def list_routing_configs(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List routing configs using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    response = client.list_routing_configs(status=status)
    return response.get("data", [])


def get_active_routing_config() -> Optional[Dict[str, Any]]:
    """Get active routing config using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    response = client.get_active_routing_config()
    return response.get("data") if response else None


def get_routing_config(config_id: int, version: Optional[int] = None) -> Dict[str, Any]:
    """Get routing config using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    response = client.get_routing_config(config_id, version=version)
    return response.get("data", {})


def create_routing_config(
    name: str, description: str, rules: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Create routing config using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    response = client.create_routing_config(name, description, rules)
    return response.get("data", {})


def update_routing_config(config_id: int, **kwargs) -> Dict[str, Any]:
    """Update routing config using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    response = client.update_routing_config(config_id, **kwargs)
    return response.get("data", {})


def test_routing_config(config_id: int, test_data: Dict[str, Any]) -> Dict[str, Any]:
    """Test routing config using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    response = client.test_routing_config(config_id, test_data)
    return response.get("data", {})


def get_routing_config_versions(config_id: int) -> List[Dict[str, Any]]:
    """Get routing config versions using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    response = client.get_routing_config_versions(config_id)
    return response.get("data", [])


def activate_routing_config(
    config_id: int, version: Optional[int] = None
) -> Dict[str, Any]:
    """Activate routing config using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    response = client.activate_routing_config(config_id, version=version)
    return response


# Dataset provider functions
def create_dataset_provider(**kwargs) -> Dict[str, Any]:
    """Create dataset provider using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    return client.create_dataset_provider(**kwargs)


def delete_dataset_provider(provider_id: str) -> Dict[str, Any]:
    """Delete dataset provider using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    return client.delete_dataset_provider(provider_id)


def list_dataset_providers() -> Dict[str, Any]:
    """List dataset providers using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    return client.list_dataset_providers()


def update_dataset_provider(provider_id: str, **kwargs) -> Dict[str, Any]:
    """Update dataset provider using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    return client.update_dataset_provider(provider_id, **kwargs)


# Model provider functions
def create_model_provider(**kwargs) -> Dict[str, Any]:
    """Create model provider using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    return client.create_model_provider(**kwargs)


def delete_model_provider(provider_id: str) -> Dict[str, Any]:
    """Delete model provider using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    return client.delete_model_provider(provider_id)


def update_model_provider(provider_id: str, **kwargs) -> Dict[str, Any]:
    """Update model provider using the default MixClient instance (backward compatibility)."""
    client = MixClient()
    return client.update_model_provider(provider_id, **kwargs)


# Evaluation functions
def list_evaluations() -> Dict[str, Any]:
    """List evaluations using the default MixClient instance."""
    client = MixClient()
    return client.list_evaluations()


def create_evaluation(
    name: str, config: Dict[str, Any], description: str = ""
) -> Dict[str, Any]:
    """Create evaluation using the default MixClient instance."""
    client = MixClient()
    return client.create_evaluation(name=name, config=config, description=description)


def get_evaluation(evaluation_name: str) -> Dict[str, Any]:
    """Get an evaluation using the default MixClient instance."""
    client = MixClient()
    return client.get_evaluation(evaluation_name)


def update_evaluation(
    evaluation_name: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an evaluation using the default MixClient instance."""
    client = MixClient()
    return client.update_evaluation(
        evaluation_name=evaluation_name,
        name=name,
        description=description,
        config=config,
        status=status,
    )


def delete_evaluation(evaluation_name: str) -> Dict[str, Any]:
    """Delete an evaluation using the default MixClient instance."""
    client = MixClient()
    return client.delete_evaluation(evaluation_name)


def get_evaluation_data(
    datasets: List[Dict[str, Any]],
    evaluation_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """Get evaluation data using the default MixClient instance."""
    client = MixClient()
    return client.get_evaluation_data(
        datasets=datasets, evaluation_name=evaluation_name, limit=limit, offset=offset
    )


def mixflow_param(
    default: Optional[Any] = None,
    description: Optional[str] = None,
) -> Any:
    """Define a configurable parameter for a MixFlow workflow.

    This function marks a class attribute as a configurable workflow parameter.
    The parameter metadata (type, description, default value) will be extracted
    automatically when the workflow is created and shown in the UI.

    Args:
        default: Default value for the parameter (optional)
        description: Human-readable description of the parameter (optional)

    Returns:
        The default value (for use in the class definition)

    Example:
        ```python
        from mixtrain import MixFlow, mixflow_param

        class MyWorkflow(MixFlow):
            # With type annotation and description
            learning_rate: float = mixflow_param(
                default=0.001,
                description="Learning rate for training"
            )

            # With type annotation, no default
            model_name: str = mixflow_param(
                description="Name of the model to use"
            )

            # Simple case - just a default value
            batch_size: int = mixflow_param(default=32)

            def run(self):
                print(f"Using learning_rate: {self.learning_rate}")
                print(f"Using model: {self.model_name}")
                print(f"Batch size: {self.batch_size}")
        ```

    Note:
        Parameters defined with mixflow_param() will be:
        - Extracted automatically when the workflow is created
        - Displayed in the web UI with their types and descriptions
        - Configurable via a form interface or JSON when running the workflow
    """
    return default


class MixFlow:
    def __init__(self):
        self.mix = MixClient()

    def setup(self):
        pass

    def run(self):
        raise NotImplementedError(
            "Run method should be implemented by the workflow subclass"
        )

    def cleanup(self):
        pass
