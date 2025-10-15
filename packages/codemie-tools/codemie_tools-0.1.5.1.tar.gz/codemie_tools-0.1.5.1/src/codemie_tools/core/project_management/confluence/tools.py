import logging
import re
from typing import Optional, Type

from atlassian import Confluence
from markdownify import markdownify
from pydantic import BaseModel, Field

from codemie_tools.base.codemie_tool import CodeMieTool
from codemie_tools.core.project_management.confluence.models import ConfluenceConfig
from codemie_tools.core.project_management.confluence.tools_vars import GENERIC_CONFLUENCE_TOOL
from codemie_tools.core.project_management.confluence.utils import validate_creds, prepare_page_payload, \
    parse_payload_params

logger = logging.getLogger(__name__)

# Url that is used for testing confluence integration
CONFLUENCE_TEST_URL: str = "/rest/api/user/current"
CONFLUENCE_TEST_RESPONSE: str = 'HTTP: GET/rest/api/user/current -> 200'
CONFLUENCE_ERROR_MSG: str = 'Access denied'

class ConfluenceInput(BaseModel):
    method: str = Field(
        ...,
        description="The HTTP method to use for the request (GET, POST, PUT, DELETE, etc.). Required parameter."
    )
    relative_url: str = Field(
        ...,
        description="""
        Required parameter: The relative URI for Confluence API.
        URI must start with a forward slash and '/rest/...'.
        Do not include query parameters in the URL, they must be provided separately in 'params'.
        For search/read operations, you MUST always get minimum fields and set max results, until users ask explicitly for more fields.
        """.strip()
    )
    params: Optional[str] = Field(
        default="",
        description="""
        Optional JSON of parameters to be sent in request body or query params. MUST be string with valid JSON. 
        For search/read operations, you MUST always get minimum fields and set max results, until users ask explicitly for more fields.
        For search/read operations you must generate CQL query string and pass it as params.
        """.strip()
    )
    is_markdown: bool = Field(
        default=False,
        description="""
        Optional boolean to indicate if the payload main content is in Markdown format. 
        If true, the payload will be converted to HTML before sending to Confluence.
        """.strip()
    )


class GenericConfluenceTool(CodeMieTool):
    config: ConfluenceConfig
    name: str = GENERIC_CONFLUENCE_TOOL.name
    description: str = GENERIC_CONFLUENCE_TOOL.description
    args_schema: Type[BaseModel] = ConfluenceInput
    page_search_pattern: str = r'/rest/api/content/\d+'
    throw_truncated_error: bool = False
    page_action_prefix: str = "/rest/api/content"

    def execute(self, method: str, relative_url: str, params: Optional[str] = "", is_markdown: bool = False, *args):
        confluence = Confluence(
            url=self.config.url,
            username=self.config.username if self.config.username else None,
            token=self.config.token if not self.config.cloud else None,
            password=self.config.token if self.config.cloud else None,
            cloud=self.config.cloud
        )
        validate_creds(confluence)
        payload_params = parse_payload_params(params)
        if method == "GET":
            response = confluence.request(
                method=method,
                path=relative_url,
                params=payload_params,
                advanced_mode=True
            )
            response_text = self.process_search_response(relative_url, response)
        else:
            if relative_url.startswith(self.page_action_prefix) and is_markdown:
                payload_params = prepare_page_payload(payload_params)
            response = confluence.request(
                method=method,
                path=relative_url,
                data=payload_params,
                advanced_mode=True,
            )
            response_text = response.text
        response_string = f"HTTP: {method}{relative_url} -> {response.status_code}{response.reason}{response_text}"
        logger.debug(response_string)
        return response_string

    def process_search_response(self, relative_url: str, response) -> str:
        if re.match(self.page_search_pattern, relative_url):
            self.tokens_size_limit = 20000
            body = markdownify(response.text, heading_style="ATX")
            return body
        return response.text

    def _healthcheck(self):
        response = self.execute("GET", CONFLUENCE_TEST_URL)
        assert response.startswith(CONFLUENCE_TEST_RESPONSE), CONFLUENCE_ERROR_MSG
