from typing import Dict, Any
from pydantic import BaseModel, model_validator, Field

from codemie_tools.base.models import CodeMieToolConfig


class ServiceNowConfig(CodeMieToolConfig):
    url: str = Field(
        description="ServiceNow instance URL",
        json_schema_extra={"placeholder": "https://your-instance.service-now.com"}
    )
    api_key: str = Field(
        default="",
        description="ServiceNow API key for authentication",
        json_schema_extra={
            "sensitive": True,
            "help": "https://docs.servicenow.com/bundle/tokyo-platform-administration/page/administer/security/task/t_CreateAnOAuthAPIEndpointForExternalClients.html"
        }
    )


class ServiceNowInput(BaseModel):
    method: str = Field(
        ...,
        description="""
        Required parameter: The HTTP method to use for the request (GET, POST, PUT, DELETE, etc.). Required parameter.
        """
    )
    table: str = Field(
        ...,
        description="""
        Required parameter: The table name to use in API.
        This parameter will be used to form request url, e.g. /api/now/table/{table}
        """
    )
    sys_id: str = Field(
        default="",
        description="""
        Optional parameter: Sys_id of the record to use in API. Should only be supplied when working with individual record.
        This parameter will be used to form request url, e.g. /api/now/table/{table}/{sys_id}
        """
    )
    params: str = Field(
        default="",
        description="""
        Optional parameter: **JSON of parameters** to be sent in request body or query params. MUST be string with valid JSON. 
        For search/read operations, you MUST always get "key", "summary", "status", "assignee", "issuetype" and 
        set maxResult, until users ask explicitly for more fields.
        """
    )
    body: str = Field(
        default="",
        description="""
        Optional parameter: Body of JSON request to use with POST/PUT/PATCH methods.
        """
    )