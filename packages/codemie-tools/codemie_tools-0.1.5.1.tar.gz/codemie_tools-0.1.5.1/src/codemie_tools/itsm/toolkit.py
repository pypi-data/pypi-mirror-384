from typing import List

from codemie_tools.base.base_toolkit import DiscoverableToolkit
from codemie_tools.base.models import ToolKit, Tool, ToolSet
from .servicenow.tools import ServiceNowTableTool
from .servicenow.tools_vars import SNOW_TABLE_TOOL


class ITSMToolkitUI(ToolKit):
    toolkit: ToolSet = ToolSet.ITSM
    tools: List[Tool] = [
        Tool.from_metadata(SNOW_TABLE_TOOL, tool_class=ServiceNowTableTool)
    ]
    label: str = ToolSet.ITSM.value


class ITSMToolkit(DiscoverableToolkit):

    @classmethod
    def get_definition(cls):
        return ITSMToolkitUI()
