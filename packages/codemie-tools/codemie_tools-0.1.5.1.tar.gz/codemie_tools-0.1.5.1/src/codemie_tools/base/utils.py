import ast
import json
import logging
import re
from typing import Type, Union, Dict, Optional, Any

from langchain_core.tools import ToolException
from pydantic import BaseModel, ValidationError
import tiktoken

logger = logging.getLogger(__name__)

def sanitize_string(input_string: str) -> str:
    """
    Sanitize a string by replacing or masking potentially sensitive information.

    This function uses predefined regular expressions to identify and replace common patterns
    of sensitive data such as passwords, usernames, IP addresses, email addresses,
    API keys and credit card numbers.

    Args:
        input_string (str): The original string to be sanitized.

    Returns:
        str: The sanitized string with sensitive information removed or masked.

    Example:
        >>> original_string = "Error: Unable to connect. Username: admin, Password: secret123, IP: 192.168.1.1"
        >>> sanitize_string(original_string)
        'Error: Unable to connect. Username: ***, Password: ***, IP: [IP_ADDRESS]'
    """
    patterns = [
        (r'\b(password|pwd|pass)(\s*[:=]\s*|\s+)(\S+)', r'\1\2***'),  # Passwords
        (r'\b(username|user|uname)(\s*[:=]\s*|\s+)(\S+)', r'\1\2***'),  # Usernames
        (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP_ADDRESS]'),  # IP addresses
        (r'\b(?:[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b', '[EMAIL]'),  # Email addresses
        (r'\b(api[_-]?key|access[_-]?token)(\s*[:=]\s*|\s+)(\S+)', r'\1\2[API_KEY]'),  # API keys and access tokens
        (r'([?&])(api[_-]?key|key|access[_-]?token)=([A-Za-z0-9_\-]+)', r'\1\2=[API_KEY]'),  # API keys in URL query parameters
        (r'\b(?:\d{4}[-\s]?){4}\b', '[CREDIT_CARD]'),  # Credit card numbers
    ]

    sanitized_string = input_string

    for pattern, replacement in patterns:
        sanitized_string = re.sub(pattern, replacement, sanitized_string, flags=re.IGNORECASE)

    return sanitized_string


def parse_to_dict(input_string):
    """
    Parse a string representation of a dictionary into an actual dictionary.
    Handles both JSON format and Python dictionary syntax.
    """
    if not input_string or not isinstance(input_string, str):
        return {}

    # Remove whitespace
    input_string = input_string.strip()

    # Try parsing as JSON directly
    try:
        return json.loads(input_string)
    except json.JSONDecodeError:
        pass

    # Try parsing as Python literal (for dictionary strings like "{'key': 'value'}")
    try:
        return ast.literal_eval(input_string)
    except (ValueError, SyntaxError):
        pass

    # If the above methods fail, try a more robust approach for Python dict syntax
    if input_string.startswith('{') and input_string.endswith('}'):
        try:
            # Convert Python dict string to proper JSON by handling single quotes
            # This regex replaces single quotes with double quotes while preserving quotes in values
            cleaned = re.sub(r"(?<!\\)'([^']*)'(?!\\)", r'"\1"', input_string)
            # Replace any remaining single quotes with double quotes
            cleaned = cleaned.replace("'", '"')
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try a simpler approach as a fallback
            try:
                simple_cleaned = input_string.replace("'", '"')
                return json.loads(simple_cleaned)
            except json.JSONDecodeError:
                pass

    # If all parsing attempts failed, log the error and return empty dict
    print(f"Failed to parse string to dict: {input_string}")
    return {}

OPEN_AI_TOOL_NAME_LIMIT = 64

def parse_tool_input(args_schema: Type[BaseModel], tool_input: Union[str, Dict]):
    try:
        input_args = args_schema
        logger.info(f"Starting parser with input: {tool_input}")
        if isinstance(tool_input, str):
            logger.info("isinstance(tool_input, str)")
            params = parse_to_dict(tool_input)
            result = input_args.model_validate(dict(params))
            return {
                k: getattr(result, k)
                for k, v in result.model_dump().items()
                if k in tool_input
            }
        else:
            logger.info("else isinstance(tool_input, dict)")
            if input_args is not None:
                result = input_args.model_validate(tool_input)
                return {
                    k: getattr(result, k)
                    for k, v in result.model_dump().items()
                    if k in tool_input
                }
        return tool_input
    except Exception as e:
        raise ToolException(f"""
                Cannot parse input parameters.
                Got wrong input: {tool_input}. See description of input parameters.
                Error: {e}
                """)


def clean_json_string(json_string):
    """
    Extract JSON object from a string, removing extra characters before '{' and after '}' 
    and escaping single quotes, newlines, and carriage returns.

    Args:
    json_string (str): Input string containing a JSON object.

    Returns:
    str: Cleaned JSON string or original string if no JSON object found.
    """
    json_string = json_string.replace("'", "\'").replace('\n', '\\n').replace('\r', '\\r')
    pattern = r'^[^{]*({.*})[^}]*$'
    match = re.search(pattern, json_string, re.DOTALL)
    if match:
        return match.group(1)
    return json_string


def get_encoding(llm_model: str) -> 'tiktoken.core.Encoding':
    try:
        encoding = tiktoken.encoding_for_model(llm_model)
    except Exception:
        logger.debug(f"Cannot find encoding for model {llm_model}. Using o200k_base encoding")
        encoding = tiktoken.get_encoding("o200k_base")
    return encoding


def humanize_error(error: Exception) -> str:
    """
    If an error is a Pyndatic ValidationError, return a human-readable string
    Otherwise, return the string representation of the error.
    """
    if not isinstance(error, ValidationError):
        return str(error)

    try:
      return ", ".join([
        f"{_format_pydantic_validation_loc(item['loc'])}: {item['msg'].lower()}"
        for item in error.errors()
      ]).capitalize()
    except Exception:
        logger.error("Error formatting Pydantic ValidationError", exc_info=True)
        return str(error)


def _format_pydantic_validation_loc(items):
  """Humanize the location field of a Pydantic validation error"""
  return ".".join(str(loc) for loc in items)


def parse_and_escape_args(query: Union[str, Dict[str, Any]], item_type: str = None) -> Dict[str, Any]:
    """
    Parses arguments from string or dictionary input.
    Handles JSON string parsing with proper error messaging.

    Args:
        query: Input query as either a JSON string or dictionary
        item_type: Optional name of the item type for error messages

    Returns:
        Dictionary of parsed arguments or None if query is None

    Raises:
        ValueError: If query is not a valid JSON string or dictionary
        ToolException: If parsing fails due to invalid format
    """
    if not query:
        return {}

    if isinstance(query, dict):
        return query

    if isinstance(query, str):
        try:
            # Remove markdown code block markers if present
            query_str = query.replace("```json", "").replace("```", "").strip()
            return json.loads(query_str)
        except json.JSONDecodeError as e:
            type_context = f" in {item_type}" if item_type else ""
            raise ToolException(f"Invalid JSON format{type_context}: {str(e)}")

    type_context = f"{item_type}" if item_type else "Input"
    raise ToolException(f"{type_context} must be a JSON string or dict, got {type(query)}")
