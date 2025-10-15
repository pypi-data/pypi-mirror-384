from typing import Type, Union, Dict, Any, Optional

from langchain_core.tools import ToolException
from pydantic import BaseModel, model_validator

from ...base.utils import parse_and_escape_args

from codemie_tools.base.codemie_tool import CodeMieTool
from .models import AWSConfig, AWSInput
from .tools_vars import AWS_TOOL
from .aws_client import AWSClient


class GenericAWSTool(CodeMieTool):
    """Generic tool for interacting with AWS services using boto3."""

    config: AWSConfig
    client: Optional[AWSClient] = None
    name: str = AWS_TOOL.name
    description: str = AWS_TOOL.description
    args_schema: Type[BaseModel] = AWSInput

    @model_validator(mode='after')
    def initialize_client(self) -> 'GenericAWSTool':
        """Initialize the AWS client with configuration."""
        self.client = AWSClient(
            region=self.config.region,
            access_key_id=self.config.access_key_id,
            secret_access_key=self.config.secret_access_key
        )
        return self

    def execute(self, query: Union[str, Dict[str, Any]]) -> str:
        """
        Execute an AWS API operation.

        Args:
            query: JSON object or string containing:
                   - service: AWS service name
                   - method_name: API method to call
                   - method_arguments: Method parameters

        Returns:
            str: String representation of the API response

        Raises:
            ToolException: If operation fails
        """
        try:
            # Parse query using common utility
            loaded_query = parse_and_escape_args(query, item_type="optional_args")

            # Validate required field 'service'
            if "service" not in loaded_query:
                raise ToolException(
                    "Error: 'service' key is missing in the query. "
                    "Please provide a valid query with 'service'."
                )

            # Execute the AWS API call
            response = self.client.execute_method(
                service=loaded_query["service"],
                method_name=loaded_query["method_name"],
                method_arguments=loaded_query["method_arguments"]
            )

            return str(response)

        except ToolException:
            raise
        except Exception as e:
            raise ToolException(f"AWS tool execution failed: {str(e)}")

    def _healthcheck(self):
        """
        Check if AWS service is accessible.
        Raises an exception if the service is not accessible.
        """
        self.client.health_check()
