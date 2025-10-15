from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, model_validator

from codemie_tools.base.models import CodeMieToolConfig


PAGE_NUMBER_DESCRIPTION = "Number of page to retrieve. Pass if page.totalPages > 1"


class ReportPortalConfig(CodeMieToolConfig):
    """Configuration for Report Portal integration."""

    url: str = Field(
        description="Report Portal endpoint URL",
        json_schema_extra={"placeholder": "https://reportportal.example.com"}
    )
    api_key: str = Field(
        description="Report Portal API key for authentication",
        json_schema_extra={
            "placeholder": "your_api_key",
            "sensitive": True,
            "help": "https://reportportal.io/docs/authorization/ApiTokens"
        }
    )
    project: str = Field(
        description="Report Portal project name",
        json_schema_extra={"placeholder": "my_project"}
    )

    @model_validator(mode='before')
    @classmethod
    def validate_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that all required fields are provided."""
        required_fields = ['url', 'api_key', 'project']
        for field in required_fields:
            if field not in values or not values[field]:
                raise ValueError(f"{field} is a required field and must be provided.")
        return values


class GetExtendedLaunchDataInput(BaseModel):
    """Input schema for getting extended launch data."""
    launch_id: str = Field(description="Launch ID of the launch to export")


class GetExtendedLaunchDataAsRawInput(BaseModel):
    """Input schema for getting extended launch data as raw."""
    launch_id: str = Field(description="Launch ID of the launch to export")
    format: Optional[str] = Field(
        default="html",
        description="Format of the exported data. May be 'pdf' or 'html'"
    )


class GetLaunchDetailsInput(BaseModel):
    """Input schema for getting launch details."""
    launch_id: str = Field(description="Launch ID of the launch to get details for")


class GetAllLaunchesInput(BaseModel):
    """Input schema for getting all launches."""
    page_number: Optional[int] = Field(
        default=1,
        description=PAGE_NUMBER_DESCRIPTION
    )
    page_sort: Optional[str] = Field(
        default="startTime,number,DESC",
        description="Sort order for launches. Defaults to 'startTime,number,DESC' if not specified"
    )
    filter_has_composite_attribute: Optional[str] = Field(
        default=None,
        description="Composite attribute filter"
    )


class FindTestItemByIdInput(BaseModel):
    """Input schema for finding test item by ID."""
    item_id: str = Field(description="Item ID of the item to get details for")


class GetTestItemsForLaunchInput(BaseModel):
    """Input schema for getting test items for launch."""
    launch_id: str = Field(description="Launch ID of the launch to get test items for")
    page_number: Optional[int] = Field(
        default=1,
        description=PAGE_NUMBER_DESCRIPTION
    )
    status: Optional[str] = Field(
        default=None,
        description="Status of the test item"
    )


class GetLogsForTestItemInput(BaseModel):
    """Input schema for getting logs for test item."""
    item_id: str = Field(description="Item ID of the item to get logs for")
    page_number: Optional[int] = Field(
        default=1,
        description=PAGE_NUMBER_DESCRIPTION
    )


class GetUserInformationInput(BaseModel):
    """Input schema for getting user information."""
    username: str = Field(description="Username of the user to get information for")


class GetDashboardDataInput(BaseModel):
    """Input schema for getting dashboard data."""
    dashboard_id: str = Field(description="Dashboard ID of the dashboard to get data for")


class UpdateTestItemInput(BaseModel):
    """Input schema for updating test item."""
    item_id: str = Field(description="ID of the test item to update")
    status: str = Field(
        description="New status for the test item. Must be one of: FAILED, PASSED, SKIPPED"
    )
    description: Optional[str] = Field(
        default="Status updated manually",
        description="Description for the status update"
    )
