from typing import List

from codemie_tools.base.models import ToolKit, ToolSet, Tool
from codemie_tools.base.base_toolkit import DiscoverableToolkit
from codemie_tools.core.project_management.confluence.tools import GenericConfluenceTool
from codemie_tools.core.project_management.confluence.tools_vars import GENERIC_CONFLUENCE_TOOL
from codemie_tools.core.project_management.jira.tools import GenericJiraIssueTool
from codemie_tools.core.project_management.jira.tools_vars import GENERIC_JIRA_TOOL


class ProjectManagementToolkitUI(ToolKit):
    toolkit: ToolSet = ToolSet.PROJECT_MANAGEMENT
    tools: List[Tool] = [
        Tool.from_metadata(GENERIC_CONFLUENCE_TOOL, tool_class=GenericConfluenceTool),
        Tool.from_metadata(GENERIC_JIRA_TOOL, tool_class=GenericJiraIssueTool),
    ]
    label: str = ToolSet.PROJECT_MANAGEMENT.value


class ProjectManagementToolkit(DiscoverableToolkit):

    @classmethod
    def get_definition(cls):
        return ProjectManagementToolkitUI()
