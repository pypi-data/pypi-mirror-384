from typing import List

from codemie_tools.base.base_toolkit import BaseToolkit
from codemie_tools.base.models import Tool, ToolKit, ToolSet
from codemie_tools.base.base_toolkit import DiscoverableToolkit
from codemie_tools.open_api.tools import InvokeRestApiBySpec, GetOpenApiSpec
from codemie_tools.open_api.tools_vars import OPEN_API_TOOL, OPEN_API_SPEC_TOOL


class OpenApiToolkitUI(ToolKit):
    """UI representation of the OpenAPI toolkit."""
    toolkit: ToolSet = ToolSet.OPEN_API
    tools: List[Tool] = [
        Tool.from_metadata(OPEN_API_TOOL, tool_class=InvokeRestApiBySpec),
        Tool.from_metadata(OPEN_API_SPEC_TOOL, tool_class=GetOpenApiSpec),
    ]
    settings_config: bool = True


class OpenApiToolkit(DiscoverableToolkit):
    """Toolkit for OpenAPI tools."""

    @classmethod
    def get_definition(cls):
        """Return the toolkit definition."""
        return OpenApiToolkitUI()
