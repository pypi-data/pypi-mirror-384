from typing import List

from codemie_tools.base.models import ToolKit, ToolSet, Tool
from ...base.base_toolkit import DiscoverableToolkit
from .github.tools import GithubTool
from .github.tools_vars import GITHUB_TOOL
from .gitlab.tools import GitlabTool
from .gitlab.tools_vars import GITLAB_TOOL


class VcsToolkitUI(ToolKit):
    toolkit: ToolSet = ToolSet.VCS
    tools: List[Tool] = [
        Tool.from_metadata(GITHUB_TOOL, tool_class=GithubTool),
        Tool.from_metadata(GITLAB_TOOL, tool_class=GitlabTool),
    ]


class VcsToolkit(DiscoverableToolkit):

    @classmethod
    def get_definition(cls):
        return VcsToolkitUI()
