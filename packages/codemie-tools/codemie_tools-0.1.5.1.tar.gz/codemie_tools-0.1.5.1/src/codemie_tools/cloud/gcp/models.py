from typing import Optional, Dict, Any, Union, List

from pydantic import BaseModel, Field, model_validator

from codemie_tools.base.models import CodeMieToolConfig


class GCPConfig(CodeMieToolConfig):
    """Configuration for GCP integration."""

    service_account_key: str = Field(
        description="GCP Service Account Key in JSON format",
        json_schema_extra={
            "placeholder": '{"type": "service_account", "project_id": "...", "private_key_id": "...", ...}',
            "sensitive": True,
            "help": "https://cloud.google.com/iam/docs/creating-managing-service-account-keys"
        }
    )

    @model_validator(mode='before')
    def validate_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Support legacy credential keys for backward compatibility."""
        # Map legacy key to new key
        if "gcp_api_key" in values:
            values["service_account_key"] = values.pop("gcp_api_key")

        return values


class GCPInput(BaseModel):
    """Input schema for GCP tool operations."""

    method: str = Field(
        description="""
        The HTTP method to use for the request.
        Supported methods: GET, POST, PUT, DELETE, PATCH

        Example: "GET", "POST"
        """
    )

    scopes: List[str] = Field(
        description="""
        List of OAuth 2.0 scopes for Google APIs.
        Required for authentication and authorization.

        Common scopes:
        - https://www.googleapis.com/auth/cloud-platform (Full access to all Google Cloud resources)
        - https://www.googleapis.com/auth/compute (Google Compute Engine)
        - https://www.googleapis.com/auth/devstorage.read_write (Cloud Storage)
        - https://www.googleapis.com/auth/logging.admin (Cloud Logging)

        Example: ["https://www.googleapis.com/auth/cloud-platform"]
        """
    )

    url: str = Field(
        description="""
        Absolute URI for Google Cloud REST API.
        Must be a valid googleapis.com endpoint.

        Example: "https://compute.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances"
        Example: "https://storage.googleapis.com/storage/v1/b/{bucket}/o"
        """
    )

    optional_args: Optional[Union[str, Dict[str, Any]]] = Field(
        default=None,
        description="""
        Optional JSON object containing additional request parameters.
        Possible keys: 'data', 'json', 'params', 'headers'

        Example: {"params": {"maxResults": 100}, "headers": {"Content-Type": "application/json"}}

        Note: Must be valid JSON. No comments allowed.
        """
    )
