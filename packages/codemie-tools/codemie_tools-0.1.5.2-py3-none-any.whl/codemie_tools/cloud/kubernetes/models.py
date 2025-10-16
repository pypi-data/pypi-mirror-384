from typing import Optional, Dict, Any, Union

from pydantic import BaseModel, Field, model_validator

from codemie_tools.base.models import CodeMieToolConfig


class KubernetesConfig(CodeMieToolConfig):
    """Configuration for Kubernetes integration."""

    url: str = Field(
        description="Kubernetes API Server URL",
        json_schema_extra={"placeholder": "https://kubernetes.default.svc"}
    )

    token: str = Field(
        description="Kubernetes Bearer Token for authentication",
        json_schema_extra={
            "placeholder": "your_bearer_token",
            "sensitive": True,
            "help": "https://kubernetes.io/docs/reference/access-authn-authz/authentication/#service-account-tokens"
        }
    )

    verify_ssl: Optional[bool] = Field(
        default=False,
        description="Whether to verify SSL certificates"
    )

    @model_validator(mode='before')
    def validate_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Support legacy credential keys for backward compatibility."""
        # Map legacy keys to new keys
        if "kubernetes_url" in values:
            values["url"] = values.pop("kubernetes_url")
        if "kubernetes_token" in values:
            values["token"] = values.pop("kubernetes_token")

        return values


class KubernetesInput(BaseModel):
    """Input schema for Kubernetes tool operations."""

    method: str = Field(
        description="""
        The HTTP method to use for the request.
        Supported methods: GET, POST, PUT, DELETE, PATCH

        Example: "GET", "POST"
        """
    )

    suburl: str = Field(
        description="""
        The relative URI for Kubernetes API.
        Must start with a forward slash (/).

        Examples:
        - "/api/v1/namespaces" (list namespaces)
        - "/api/v1/pods" (list all pods)
        - "/api/v1/namespaces/default/pods" (list pods in default namespace)
        - "/apis/apps/v1/deployments" (list deployments)

        Note: Do not include query parameters in the URL.
        Provide them separately in 'body' or 'headers'.
        """
    )

    body: Optional[Union[str, Dict[str, Any]]] = Field(
        default=None,
        description="""
        Optional JSON object to be sent in the request body.
        Used for POST, PUT, PATCH operations.

        Example: {"metadata": {"name": "my-pod"}, "spec": {...}}

        Note: Must be valid JSON. No comments allowed.
        """
    )

    headers: Optional[Union[str, Dict[str, Any]]] = Field(
        default=None,
        description="""
        Optional JSON object of headers to be sent in the request.

        Example: {"Content-Type": "application/json"}

        Note: Must be valid JSON. No comments allowed.
        """
    )
