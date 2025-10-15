from .models import GitlabConfig

from codemie_tools.base.models import ToolMetadata

GITLAB_TOOL = ToolMetadata(
    name="gitlab",
    description="""
        Advanced GitLab REST API client tool that provides comprehensive access to GitLab's API endpoints.
        
        INPUT FORMAT:
        The tool accepts a `query` parameter containing a JSON with the following structure:
        {"query":
            {
                "method": "GET|POST|PUT|DELETE|PATCH",
                "url": "/api/v4/...",
                "method_arguments": {object with request data},
                "custom_headers": {optional dictionary of additional HTTP headers}
            }
        }
        
        REQUIREMENTS:
        - `method`: HTTP method (GET, POST, PUT, DELETE, PATCH)
        - `url`: Must start with "/api/v4/" (GitLab API v4 endpoint)
        - `method_arguments`: Object containing request parameters or body data
        - `custom_headers`: Optional dictionary for additional headers (authorization headers are protected)
        - The entire query must be valid JSON that passes json.loads() validation
        
        FEATURES:
        - Automatic request parameter handling (GET uses query params, others use request body)
        - Built-in authentication using configured GitLab Personal Access Token
        - Custom header support for specialized API calls
        - Detailed HTTP response logging with status codes and response bodies
        - Comprehensive error handling and validation
        
        RESPONSE FORMAT:
        Returns a formatted string containing:
        "HTTP: {method} {full_url} -> {status_code} {reason} {response_body}"
        
        This format provides complete visibility into the HTTP transaction including status and response data.
        
        SECURITY:
        Authorization headers are automatically managed and cannot be overridden via custom_headers.
        
        EXAMPLES:
        Get current user:
        {"query": {"method": "GET", "url": "/api/v4/user", "method_arguments": {}}}
        
        List project issues:
        {"query": {"method": "GET", "url": "/api/v4/projects/123/issues", "method_arguments": {"state": "opened"}}}
        
        Create merge request with custom headers:
        {"query":
            {
                "method": "POST", "url": "/api/v4/projects/123/merge_requests",
                "method_arguments": {"source_branch": "feature", "target_branch": "main", "title": "Feature"},
                "custom_headers": {"X-GitLab-Custom": "value"}
            }
        }
        """,
    label="Gitlab",
    user_description="""
        Provides comprehensive access to the GitLab REST API with detailed response formatting and flexible request handling. This tool enables the AI assistant to perform any GitLab operation available through the REST API.
        
        Key Capabilities:
        - Project and repository management
        - Issue and merge request operations
        - User and group management
        - Pipeline and job operations
        - File and commit operations
        - Wiki and snippet management
        - System administration (if token has admin privileges)
        - Detailed HTTP transaction visibility
        
        Setup Requirements:
        1. GitLab Server URL (e.g., https://gitlab.com or your self-hosted instance)
        2. GitLab Personal Access Token with appropriate scopes
        
        Response Features:
        - Complete HTTP transaction details including status codes
        - Full response body content for debugging and analysis
        - Automatic handling of different request types (GET vs POST/PUT/DELETE)
        
        Use this tool when you need direct access to GitLab's REST API endpoints that may not be covered by other specialized GitLab tools.
        """.strip(),
    settings_config=True,
    config_class=GitlabConfig
)
