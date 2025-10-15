from pydantic import Field

from codemie_tools.base.models import CodeMieToolConfig


class TelegramConfig(CodeMieToolConfig):
    bot_token: str = Field(
        default="",
        alias="token",
        description="Telegram Bot API token",
        json_schema_extra={
            "placeholder": "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "sensitive": True,
        },
    )
