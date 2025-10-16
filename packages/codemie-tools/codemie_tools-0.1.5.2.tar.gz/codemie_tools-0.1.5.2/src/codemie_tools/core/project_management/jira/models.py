from typing import Optional, Dict, Any

from pydantic import model_validator, Field, ConfigDict

from codemie_tools.base.models import CodeMieToolConfig

class JiraConfig(CodeMieToolConfig):
    url: str = Field(
        default="",
        description="URL to your Jira instance, e.g. https://jira.example.com/ or https://jira.example.com/jira/",
        json_schema_extra={"placeholder": "https://jira.example.com/"}
    )
    username: Optional[str] = Field(
        default=None,
        description="Username/email for Jira (Required for Jira Cloud)",
        json_schema_extra={"placeholder": "user@example.com"}
    )
    token: str = Field(
        default="",
        description="Personal Access Token for authentication.",
        json_schema_extra={
            "placeholder": "Token/ApiKey",
            "sensitive": True,
            "help": "https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html"
        }
    )
    cloud: Optional[bool] = Field(
        default=False,
        description="Is this a Jira Cloud instance? Toggle on if using Atlassian Cloud"
    )

    @model_validator(mode='before')
    def validate_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "password" in values:
            values["token"] = values.pop("password")

        if "is_cloud" in values:
            # Special handling for creating model from UI. is_cloud field is passed and should be passed to cloud
            values["cloud"] = values.pop("is_cloud")

        return values
