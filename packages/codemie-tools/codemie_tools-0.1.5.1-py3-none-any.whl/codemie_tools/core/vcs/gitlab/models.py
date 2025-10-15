from pydantic import Field

from codemie_tools.base.models import CodeMieToolConfig


class GitlabConfig(CodeMieToolConfig):
    """Configuration for GitLab API access."""
    url: str = Field(
        description="GitLab instance URL",
        json_schema_extra={"placeholder": "https://gitlab.example.com"}
    )
    token: str = Field(
        default="",
        description="GitLab Personal Access Token with appropriate scopes",
        json_schema_extra={
            "sensitive": True,
            "help": "https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html"
        }
    )
