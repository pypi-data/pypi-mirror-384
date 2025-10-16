import json
import logging
import traceback
from json import JSONDecodeError
from typing import Dict, Any, Optional

from atlassian import Jira
from langchain_core.tools import ToolException

from codemie_tools.base.errors import InvalidCredentialsError
from codemie_tools.base.utils import clean_json_string

logger = logging.getLogger(__name__)


def validate_jira_creds(jira: Jira):
    if jira.url is None or jira.url == "":
        logger.error("Jira URL is required. Seems there no Jira credentials provided.")
        raise InvalidCredentialsError("Jira URL is required. You should provide Jira credentials in 'Integrations'.")


def parse_payload_params(params: Optional[str]) -> Dict[str, Any]:
    """
    Parse JSON payload parameters.

    Args:
        params: JSON string to parse

    Returns:
        Dictionary representation of the JSON string

    Raises:
        ToolException: If the JSON string is invalid
    """
    if params:
        try:
            return json.loads(clean_json_string(params))
        except JSONDecodeError:
            stacktrace = traceback.format_exc()
            logger.error(f"Jira tool: Error parsing payload params: {stacktrace}")
            raise ToolException(f"JIRA tool exception. Passed 'params' string is not valid to transform to vaild JSON. {stacktrace}. Please correct and send again.")
    return {}


def get_issue_field(issue, field, default=None):
    """
    Get a field value from a Jira issue.

    Args:
        issue: Jira issue object
        field: Field name to retrieve
        default: Default value if field does not exist

    Returns:
        Field value or default if not found
    """
    if not issue:
        return default
    field_value = issue.get("fields", {})
    if field_value:
        field_value = field_value.get(field, default)
    # Additional verification. In some cases key is present, but value is None. Need to return default value
    return field_value if field_value else default


def get_additional_fields(issue, additional_fields):
    """
    Get additional fields from a Jira issue.

    Args:
        issue: Jira issue object
        additional_fields: List of additional field names to retrieve

    Returns:
        Dictionary of additional field names and values
    """
    additional_data = {}
    for field in additional_fields:
        if field not in additional_data:  # Avoid overwriting any main fields
            additional_data[field] = get_issue_field(issue, field)
    return additional_data


def process_issue(jira_base_url, issue, payload_params: Dict[str, Any] = None):
    """
    Process a Jira issue to extract relevant information.

    Args:
        jira_base_url: Base URL of the Jira instance
        issue: Jira issue object
        payload_params: Additional parameters for processing

    Returns:
        Dictionary with processed issue data
    """
    issue_key = issue.get('key')
    jira_link = f"{jira_base_url}/browse/{issue_key}"

    parsed_issue = {
        "key": issue_key,
        "url": jira_link,
        "summary": get_issue_field(issue, "summary", ""),
        "assignee": get_issue_field(issue, "assignee", {}).get("displayName", "None"),
        "status": get_issue_field(issue, "status", {}).get("name", ""),
        "issuetype": get_issue_field(issue, "issuetype", {}).get("name", "")
    }

    process_payload(issue, payload_params, parsed_issue)
    return parsed_issue


def process_payload(issue, payload_params, parsed_issue):
    """
    Process payload parameters for a Jira issue.

    Args:
        issue: Jira issue object
        payload_params: Parameters for processing
        parsed_issue: Issue object to update with processed data
    """
    fields_list = extract_fields_list(payload_params)

    if fields_list:
        update_parsed_issue_with_additional_data(issue, fields_list, parsed_issue)


def extract_fields_list(payload_params):
    """
    Extract list of fields from payload parameters.

    Args:
        payload_params: Parameters containing fields

    Returns:
        List of field names
    """
    if payload_params and 'fields' in payload_params:
        fields = payload_params['fields']
        if isinstance(fields, str) and fields.strip():
            return [field.strip() for field in fields.split(",")]
        elif isinstance(fields, list) and fields:
            return fields
    return []


def update_parsed_issue_with_additional_data(issue, fields_list, parsed_issue):
    """
    Update a parsed issue with additional data.

    Args:
        issue: Jira issue object
        fields_list: List of field names to include
        parsed_issue: Issue object to update
    """
    additional_data = get_additional_fields(issue, fields_list)
    for field, value in additional_data.items():
        if field not in parsed_issue and value:
            parsed_issue[field] = value


def process_search_response(jira_url, response, payload_params: Dict[str, Any] = None):
    """
    Process a search response from Jira.

    Args:
        jira_url: URL of the Jira instance
        response: Response object from Jira API
        payload_params: Additional parameters for processing

    Returns:
        Tuple of (processed issues string, total count string)
    """
    if response.status_code != 200:
        return response.text

    processed_issues = []
    json_response = response.json()

    for issue in json_response.get('issues', []):
        processed_issues.append(process_issue(jira_url, issue, payload_params))

    return f"Issues: {processed_issues}", f"Total: {json_response.get('total', 0)}"
