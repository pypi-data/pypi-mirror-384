import json
import re
import traceback
import urllib.parse
import requests
from json import JSONDecodeError
from typing import Type, Any, Dict

from codemie_tools.base.codemie_tool import CodeMieTool
from langchain_core.tools import ToolException

from .models import ServiceNowInput, ServiceNowConfig
from .tools_vars import SNOW_TABLE_TOOL


def clean_json_string(json_string):
    """
    Extract JSON object from a string, removing extra characters before '{' and after '}'.

    Args:
    json_string (str): Input string containing a JSON object.

    Returns:
    str: Cleaned JSON string or original string if no JSON object found.
    """
    pattern = r'^[^{]*({.*})[^}]*$'
    match = re.search(pattern, json_string, re.DOTALL)
    if match:
        return match.group(1)
    return json_string


def normalize_query_params(params: str) -> Dict[str, Any]:
    if params:
        try:
            return json.loads(clean_json_string(params))
        except JSONDecodeError:
            stacktrace = traceback.format_exc()
            raise ToolException(f"ServiceNow tool exception. Passed params are not valid JSON. {stacktrace}")
    return {}


def normalize_string(table: str) -> str:
    return table \
        .replace("\"", "") \
        .replace("'", "") \
        .replace("`", "") \
        .strip() \
        .lower()


class ServiceNowTableTool(CodeMieTool):

    args_schema: Type[ServiceNowInput] = ServiceNowInput
    name: str = SNOW_TABLE_TOOL.name
    description: str = SNOW_TABLE_TOOL.description
    config: ServiceNowConfig

    def _healthcheck(self):
        """Performs a healthcheck by querying a single incident record"""
        self.execute(
            method="GET",
            table="incident",
            params='{"sysparm_limit": 1}'
        )

    def execute(self, method: str, table: str, sys_id: str = "", params: str = "", body: str = "") -> Any:

        if not self.config.api_key or not self.config.url:
            raise ValueError(
                "ServiceNow config is not set. Please provide it before using the tool."
            )

        query_params = normalize_query_params(params)
        method = normalize_string(method).upper()
        headers = {
            "x-sn-apikey": self.config.api_key
        }

        url = urllib.parse.urljoin(self.config.url, '/api/now/table/')
        url += normalize_string(table)

        if sys_id:
            url += f"/{normalize_string(sys_id)}"

        request_args = {
            "method": method,
            "url": url,
            "headers": headers
        }

        if query_params:
            request_args["params"] = query_params

        if body:
            request_args["json"] = json.loads(body)
        response = requests.request(**request_args)

        if response.status_code >= 300:
            raise ToolException(f"ServiceNow tool exception. Status: {response.status_code}. Response: {response.text}")

        return response.text