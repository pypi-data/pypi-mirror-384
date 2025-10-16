from typing import List

from codemie_tools.base.models import ToolKit, ToolSet, Tool
from codemie_tools.base.base_toolkit import DiscoverableToolkit
from codemie_tools.notification.email.tools import EmailTool
from codemie_tools.notification.email.tools_vars import EMAIL_TOOL
from codemie_tools.notification.telegram.tools import TelegramTool
from codemie_tools.notification.telegram.tools_vars import TELEGRAM_TOOL


class NotificationToolkitUI(ToolKit):
    toolkit: ToolSet = ToolSet.NOTIFICATION
    tools: List[Tool] = [
        Tool.from_metadata(EMAIL_TOOL, tool_class=EmailTool),
        Tool.from_metadata(TELEGRAM_TOOL, tool_class=TelegramTool),
    ]
    label: str = ToolSet.NOTIFICATION.value


class NotificationToolkit(DiscoverableToolkit):
    @classmethod
    def get_definition(cls):
        return NotificationToolkitUI()
