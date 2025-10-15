from typing import Optional

from pydantic import Field

from codemie_tools.base.models import CodeMieToolConfig


class GithubConfig(CodeMieToolConfig):
    token: str = Field(
        default="",
        description="GitHub Personal Access Token with appropriate scopes for repository access",
        json_schema_extra={
            "sensitive": True,
            "help": "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
        }
    )
    url: Optional[str] = Field(
        default="https://api.github.com",
        description="GitHub API URL, typically https://api.github.com",
        json_schema_extra={"placeholder": "https://api.github.com"}
    )
