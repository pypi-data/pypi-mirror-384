import logging
from typing import Type, Optional

from langchain_core.tools import ToolException
from pydantic import BaseModel

from codemie_tools.base.codemie_tool import CodeMieTool
from codemie_tools.base.utils import parse_to_dict
from .models import KeycloakConfig, KeycloakToolInput
from .tools_vars import KEYCLOAK_TOOL
from .keycloak_client import KeycloakClient

logger = logging.getLogger(__name__)


class KeycloakTool(CodeMieTool):
    """Generic tool for interacting with Keycloak Admin API."""

    config: KeycloakConfig
    client: Optional[KeycloakClient] = None
    name: str = KEYCLOAK_TOOL.name
    description: str = KEYCLOAK_TOOL.description
    args_schema: Type[BaseModel] = KeycloakToolInput

    def __init__(self, config: KeycloakConfig):
        """Initialize the tool with configuration."""
        super().__init__(config=config)
        self.client = KeycloakClient(
            base_url=config.base_url,
            realm=config.realm,
            client_id=config.client_id,
            client_secret=config.client_secret,
            timeout=config.timeout
        )

    def execute(
        self,
        method: str,
        relative_url: str,
        params: Optional[str] = None
    ) -> str:
        """
        Execute a Keycloak Admin API request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            relative_url: Relative URL starting with '/' (e.g., '/users')
            params: Optional string dictionary of parameters

        Returns:
            str: Response text from Keycloak API

        Raises:
            ToolException: If request fails
        """
        try:
            # Parse params if provided
            payload_params = None
            if params:
                payload_params = parse_to_dict(params)

            # Execute request via client
            response_text = self.client.execute_request(
                method=method,
                relative_url=relative_url,
                params=payload_params
            )

            return response_text

        except ToolException:
            # Re-raise ToolExceptions from client
            raise
        except Exception as e:
            logger.error(f"Error executing Keycloak request: {str(e)}")
            raise ToolException(f"Failed to execute Keycloak request: {str(e)}")

    def _healthcheck(self):
        """
        Check if Keycloak server is accessible.
        Raises ToolException if health check fails.
        """
        self.client.health_check()
