import boto3
from botocore.config import Config
from typing import Any

from langchain_core.tools import ToolException


class AWSClient:
    """HTTP client for AWS API using boto3."""

    def __init__(self, region: str, access_key_id: str, secret_access_key: str):
        """
        Initialize the AWS client.

        Args:
            region: AWS region name
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
        """
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key

    def get_client(self, service: str):
        """
        Get a boto3 client for the specified AWS service.

        Args:
            service: AWS service name (e.g., 'ec2', 'iam', 's3')

        Returns:
            boto3 client instance for the service

        Raises:
            ToolException: If client creation fails
        """
        try:
            client_config = Config(region_name=self.region)
            client = boto3.client(
                service,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                config=client_config,
            )
            return client
        except Exception as e:
            raise ToolException(f"Failed to create AWS client for service '{service}': {str(e)}")

    def execute_method(self, service: str, method_name: str, method_arguments: dict) -> Any:
        """
        Execute a method on an AWS service client.

        Args:
            service: AWS service name
            method_name: The method to call on the client
            method_arguments: Arguments to pass to the method

        Returns:
            The response from the AWS API

        Raises:
            ToolException: If method execution fails
        """
        try:
            client = self.get_client(service)

            if not hasattr(client, method_name):
                raise ToolException(
                    f"Method '{method_name}' does not exist for AWS service '{service}'"
                )

            method = getattr(client, method_name)
            response = method(**method_arguments)
            return response

        except ToolException:
            raise
        except Exception as e:
            raise ToolException(
                f"Failed to execute {service}.{method_name}: {str(e)}"
            )

    def health_check(self):
        """
        Check if AWS credentials are valid by making a simple IAM call.
        """
        client = self.get_client("iam")
        client.get_user()
