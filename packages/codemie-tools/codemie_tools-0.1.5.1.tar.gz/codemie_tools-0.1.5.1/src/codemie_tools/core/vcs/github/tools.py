import json
from typing import Type, Any, Union

import requests
from pydantic import BaseModel, Field

from codemie_tools.base.codemie_tool import CodeMieTool
from codemie_tools.core.vcs.utils import _build_headers, file_response_handler
from .models import GithubConfig
from .tools_vars import GITHUB_TOOL

GITHUB_DEFAULT_HEADERS = {
    "Accept": "application/vnd.github+json"
}


class GithubInput(BaseModel):
    query: Union[str, dict[str, Any]] = Field(description="""
        JSON containing the GitHub API request specification. Must be valid JSON with no comments allowed.

        Required JSON structure:
        {
            "method": "GET|POST|PUT|DELETE|PATCH",
            "url": "https://api.github.com/...",
            "method_arguments": {request_parameters_or_body_data}
        }

        Optional with custom headers:
        {
            "method": "GET|POST|PUT|DELETE|PATCH",
            "url": "https://api.github.com/...", 
            "method_arguments": {request_parameters_or_body_data},
            "custom_headers": {additional_http_headers}
        }

        Field Requirements:
        - method: HTTP method (GET, POST, PUT, DELETE, PATCH) - REQUIRED
        - url: Complete GitHub API URL starting with "https://api.github.com" - REQUIRED
        - method_arguments: Object with request data (query params, body data, etc.) - REQUIRED (can be empty {})
        - custom_headers: Optional dictionary of additional HTTP headers - OPTIONAL

        Important Notes:
        - GitHub Personal Access Token is automatically added to Authorization header
        - custom_headers cannot override authorization headers (protected for security)
        - All request data goes in method_arguments regardless of HTTP method
        - Response will be raw JSON from GitHub API with automatic Base64 file decoding
        - The entire query must pass json.loads() validation

        Examples:
        Get user: {"method": "GET", "url": "https://api.github.com/user", "method_arguments": {}}
        Get repo file: {"method": "GET", "url": "https://api.github.com/repos/owner/repo/contents/file.py", "method_arguments": {}}
        Create issue: {"method": "POST", "url": "https://api.github.com/repos/owner/repo/issues", "method_arguments": {"title": "Bug", "body": "Description"}}
        """
                                              )


class GithubTool(CodeMieTool):
    name: str = GITHUB_TOOL.name
    description: str = GITHUB_TOOL.description
    args_schema: Type[BaseModel] = GithubInput
    config: GithubConfig

    # High value to support large source files.
    tokens_size_limit: int = 70_000

    @file_response_handler
    def execute(self, query: Union[str, dict[str, Any]], *args):
        """
        Execute GitHub API request with optional custom headers.

        Args:
            query: JSON containing request details

        Returns:
            JSON response from GitHub API

        Raises:
            ToolException: If credentials are missing or request fails
        """
        if not self.config.token or not self.config.url:
            raise ValueError(
                "Git config is not set. Please provide it before using the tool."
            )

        try:
            if isinstance(query, str):
                query = json.loads(query)
        except json.JSONDecodeError as e:
            raise ValueError(f"Query must be a JSON string: {e}")

        custom_headers = query.get('custom_headers')
        headers = _build_headers(GITHUB_DEFAULT_HEADERS, self.config.token, custom_headers)

        return requests.request(
            method=query.get('method'),
            url=query.get('url'),
            headers=headers,
            data=json.dumps(query.get('method_arguments'))
        ).json()
