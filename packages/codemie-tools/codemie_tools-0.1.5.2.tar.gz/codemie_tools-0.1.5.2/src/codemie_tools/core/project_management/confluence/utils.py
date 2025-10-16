import json
import logging
import traceback
from json import JSONDecodeError
from typing import Optional, Dict, Any

from atlassian import Confluence
from langchain_core.tools import ToolException
from markdown import markdown

try:
    # Try using the direct imports first (for production)
    from codemie_tools.base.utils import clean_json_string
except ModuleNotFoundError:
    # Fall back to relative imports (for tests)
    from src.codemie_tools.base.utils import clean_json_string

logger = logging.getLogger(__name__)


def validate_creds(confluence: Confluence):
    if confluence.url is None or confluence.url == "":
        logger.error("Confluence URL is required. Seems there no Confluence credentials provided.")
        raise ToolException("Confluence URL is required. You should provide Confluence credentials in 'Integrations'.")


def prepare_page_payload(payload: dict) -> dict:
    """Convert Confluence payload from Markdown to HTML format for body.storage.value field."""
    if value := payload.get("body", {}).get("storage", {}).get("value"):
        payload["body"]["storage"]["value"] = markdown(value) # convert markdown to HTML

    return payload


def parse_payload_params(params: Optional[str]) -> Dict[str, Any]:
    if params:
        try:
            return json.loads(clean_json_string(params))
        except JSONDecodeError:
            stacktrace = traceback.format_exc()
            raise ToolException(f"Confluence tool exception. Passed params are not valid JSON. {stacktrace}")
    return {}
