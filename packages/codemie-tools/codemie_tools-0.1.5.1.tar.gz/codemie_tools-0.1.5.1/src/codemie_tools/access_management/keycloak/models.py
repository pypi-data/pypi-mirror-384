from typing import Optional, Dict, Any
from pydantic import Field, BaseModel, model_validator

from codemie_tools.base.models import CodeMieToolConfig


class KeycloakConfig(CodeMieToolConfig):
    """Configuration for Keycloak integration."""

    base_url: str = Field(
        description="Base URL of the Keycloak server",
        json_schema_extra={"placeholder": "https://keycloak.example.com"}
    )

    realm: str = Field(
        description="Keycloak realm name",
        json_schema_extra={"placeholder": "master"}
    )

    client_id: str = Field(
        description="Client ID for authentication",
        json_schema_extra={"placeholder": "admin-cli"}
    )

    client_secret: str = Field(
        description="Client secret for authentication",
        json_schema_extra={
            "placeholder": "your_client_secret",
            "sensitive": True,
            "help": "https://www.keycloak.org/docs/latest/server_admin/#_clients"
        }
    )

    timeout: Optional[int] = Field(
        default=30,
        description="Request timeout in seconds"
    )

    @model_validator(mode='before')
    def handle_url_compatibility(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Handle backward compatibility: map 'url' to 'base_url' if present."""
        if isinstance(values, dict):
            # If 'url' is present but 'base_url' is not, use 'url' as 'base_url'
            if 'url' in values and 'base_url' not in values:
                values['base_url'] = values.pop('url')
            # If both are present, prefer 'base_url' and remove 'url'
            elif 'url' in values and 'base_url' in values:
                values.pop('url')
        return values


class KeycloakToolInput(BaseModel):
    """Input schema for Keycloak tool operations."""

    method: str = Field(
        ...,
        description="The HTTP method to use for the request (GET, POST, PUT, DELETE, etc.). Required parameter."
    )

    relative_url: str = Field(
        ...,
        description="""
        The relative URL of the Keycloak Admin API to call, e.g. '/users'. Required parameter.
        Must start with '/'. In case of GET method, you MUST include query parameters in the URL.
        """
    )

    params: Optional[str] = Field(
        default=None,
        description="Optional string dictionary of parameters to be sent in the query string or request body."
    )
