from typing import Optional

from pydantic import Field, model_validator

from codemie_tools.base.models import CodeMieToolConfig


class OpenApiConfig(CodeMieToolConfig):
    """Configuration for OpenAPI tools."""

    model_config = {
        "populate_by_name": True,  # Allow initialization using either field name or alias
    }
    spec: str = Field(
        default="",  # Changed from None to empty string as default
        description="OpenAPI specification JSON or URL to the specification",
        json_schema_extra={"placeholder": "Paste OpenAPI specification JSON or URL"},
        alias='openapi_spec'
    )
    is_basic_auth: bool = Field(
        default=False,
        description="Whether to use Basic Authentication"
    )
    username: Optional[str] = Field(
        default=None,
        description="Username for Basic Authentication (only required if is_basic_auth is true)",
        json_schema_extra={"placeholder": "basic_auth_username"},
        alias='openapi_username'
    )
    api_key: str = Field(
        default="",
        description="API key for authentication",
        json_schema_extra={
            "placeholder": "API Key",
            "sensitive": True
        },
        alias='openapi_api_key'
    )
    timeout: int = Field(
        default=120,
        description="Request timeout in seconds"
    )
    auth_header_name: Optional[str] = Field(
        default=None,
        description="Custom authentication header name (defaults to 'Authorization' if not provided)",
        json_schema_extra={"placeholder": "X-API-Key"}
    )


    @model_validator(mode='after')
    def validate_basic_auth(self) -> 'OpenApiConfig':
        # Check if username is missing or empty when Basic Auth is enabled
        if self.is_basic_auth and not self.username:
            raise ValueError("Username is required when Basic Authentication is enabled")
        return self
