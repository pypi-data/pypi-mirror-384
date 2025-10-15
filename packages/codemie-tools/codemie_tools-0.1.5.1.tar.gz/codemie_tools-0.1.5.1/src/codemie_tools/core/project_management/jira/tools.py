import logging
import re
from typing import Type, Optional

from atlassian import Jira
from pydantic import BaseModel, Field, model_validator

from codemie_tools.base.codemie_tool import CodeMieTool
from codemie_tools.core.project_management.jira.models import JiraConfig
from codemie_tools.core.project_management.jira.tools_vars import GENERIC_JIRA_TOOL, get_jira_tool_description
from codemie_tools.core.project_management.jira.utils import validate_jira_creds, parse_payload_params, \
    process_search_response

logger = logging.getLogger(__name__)

JIRA_TEST_URL: str = "/rest/api/2/myself"


class JiraInput(BaseModel):
    method: str = Field(
        ...,
        description="The HTTP method to use for the request (GET, POST, PUT, DELETE, etc.). Required parameter."
    )
    relative_url: str = Field(
        ...,
        description="""
        Required parameter: The relative URI for JIRA REST API V2.
        URI must start with a forward slash and '/rest/api/2/...'.
        Do not include query parameters in the URL, they must be provided separately in 'params'.
        For search/read operations, you MUST always get "key", "summary", "status", "assignee", "issuetype" and 
        set maxResult, until users ask explicitly for more fields.
        """
    )
    params: Optional[str] = Field(
        default="",
        description="""
        Optional JSON of parameters to be sent in request body or query params. MUST be string with valid JSON. 
        For search/read operations, you MUST always get "key", "summary", "status", "assignee", "issuetype" and 
        set maxResult, until users ask explicitly for more fields.
        """
    )
    file_paths: Optional[list] = Field(
        default=None,
        description="Optional list of file paths to attach to the Jira issue."
    )


class GenericJiraIssueTool(CodeMieTool):
    config: JiraConfig
    jira: Optional[Jira] = None
    name: str = GENERIC_JIRA_TOOL.name
    description: str = GENERIC_JIRA_TOOL.description or ""
    args_schema: Type[BaseModel] = JiraInput
    # Regular expression to match /rest/api/[any number]/search
    issue_search_pattern: str = r'/rest/api/\d+/search'

    @model_validator(mode='after')
    def validate_config(self) -> 'GenericJiraIssueTool':
        if self.config.cloud:
            self.issue_search_pattern = r'/rest/api/3/search/jql'
            self.description = get_jira_tool_description(api_version=3)
        self.jira = Jira(
            url=self.config.url,
            username=self.config.username if self.config.username else None,
            token=self.config.token if not self.config.cloud else None,
            password=self.config.token if self.config.cloud else None,
            cloud=self.config.cloud
        )
        validate_jira_creds(self.jira)
        return self

    def execute(
            self,
            method: str,
            relative_url: str,
            params: Optional[str] = "",
            *args
    ):
        payload_params = parse_payload_params(params)

        if method == "GET":
            response_text, response = self._handle_get_request(relative_url, payload_params)
        else:
            response_text, response = self._handle_non_get_request(method, relative_url, payload_params)

        response_string = f"HTTP: {method} {relative_url} -> {response.status_code} {response.reason} {response_text}"
        logger.debug(response_string)
        return response_string

    def _handle_get_request(self, relative_url, payload_params):
        response = self.jira.request(
            method="GET",
            path=relative_url,
            params=payload_params,
            advanced_mode=True,
            headers={"content-type": "application/json"},
        )
        self.jira.raise_for_status(response)
        if re.match(self.issue_search_pattern, relative_url):
            response_text = process_search_response(self.jira.url, response, payload_params)
        else:
            response_text = response.text
        return response_text, response

    def _handle_non_get_request(self, method, relative_url, payload_params):
        response = self.jira.request(
            method=method,
            path=relative_url,
            data=payload_params,
            advanced_mode=True
        )
        self.jira.raise_for_status(response)
        return response.text, response

    def _healthcheck(self):
        self.execute("GET", JIRA_TEST_URL)
