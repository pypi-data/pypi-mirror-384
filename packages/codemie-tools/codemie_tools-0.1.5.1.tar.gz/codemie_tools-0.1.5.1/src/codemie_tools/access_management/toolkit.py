import logging
from typing import List

from codemie_tools.access_management.keycloak.tools import KeycloakTool
from codemie_tools.access_management.keycloak.tools_vars import KEYCLOAK_TOOL
from codemie_tools.base.base_toolkit import BaseToolkit, DiscoverableToolkit
from codemie_tools.base.models import ToolKit, ToolSet, Tool

logger = logging.getLogger(__name__)


class AccessManagementToolkitUI(ToolKit):
    """UI definition for Access Management Toolkit."""

    toolkit: ToolSet = ToolSet.ACCESS_MANAGEMENT
    tools: List[Tool] = [
        Tool.from_metadata(KEYCLOAK_TOOL, tool_class=KeycloakTool),
    ]
    label: str = "Access Management"
    description: str = "Comprehensive toolkit for identity and access management integrations"


class AccessManagementToolkit(DiscoverableToolkit):
    """Toolkit for Access Management integrations (Keycloak, IAM, etc.)."""

    @classmethod
    def get_definition(cls):
        """Return toolkit definition for UI autodiscovery."""
        return AccessManagementToolkitUI()