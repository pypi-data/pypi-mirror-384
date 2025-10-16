from enum import Enum
from typing import List, Optional, Any

from pydantic import BaseModel, model_validator, Field


class ToolMetadata(BaseModel):
    name: str
    description: Optional[str] = ''
    label: Optional[str] = ''
    react_description: Optional[str] = ''
    user_description: Optional[str] = ''
    settings_config: Optional[bool] = False
    config_class: Optional[Any] = Field(default=None, exclude=True)

    @model_validator(mode='after')
    def validate_settings_config(self) -> 'ToolMetadata':
        if self.settings_config and self.config_class is None:
            raise ValueError("config_class must be provided when settings_config is True")
        return self


class ToolSet(str, Enum):
    GIT = "Git"
    VCS = "VCS"
    CODEBASE_TOOLS = "Codebase Tools"
    KB_TOOLS = "Knowledge Base"
    CODE_PLAN = "Code plan"
    GENERAL = "General"
    RESEARCH = "Research"
    CLOUD = "Cloud"
    PLUGIN = "Plugin"
    ADMIN = "CodeMie admin"
    ACCESS_MANAGEMENT = "Access Management"
    PROJECT_MANAGEMENT = "Project Management"
    OPEN_API = "OpenAPI"
    DATA_MANAGEMENT = "Data Management"
    VISION = "Vision"
    FILE_SYSTEM = "FileSystem"
    PANDAS = "Pandas"
    FILE_ANALYSIS = "File Analysis"
    NOTIFICATION = "Notification"
    CODE_QUALITY = "Code Quality"
    OPEN_API_LABEL = "Open API"
    FILE_SYSTEM_LABEL = "File System"
    FILE_MANAGEMENT_LABEL = "File Management"
    QUALITY_ASSURANCE = "Quality Assurance"
    AZURE_DEVOPS_WIKI = "Azure DevOps Wiki"
    AZURE_DEVOPS_WORK_ITEM = "Azure DevOps Work Item"
    AZURE_DEVOPS_TEST_PLAN = "Azure DevOps Test Plan"
    ITSM = "IT Service Management"
    REPORT_PORTAL = "Report Portal"
    PLATFORM_TOOLS = "Platform Tools"


class Tool(BaseModel):
    name: str
    label: Optional[str] = None
    settings_config: Optional[bool] = False
    description: Optional[str] = None
    user_description: Optional[str] = None
    config_class: Optional[Any] = Field(default=None, exclude=True)
    tool_class: Optional[Any] = Field(default=None, exclude=True)

    @model_validator(mode="before")
    def set_label(cls, values):
        name = values.get('name', '')
        label = values.get('label', '')
        if not label:
            values['label'] = ' '.join(word.capitalize() for word in name.split('_'))
        else:
            values['label'] = label
        return values

    @classmethod
    def from_metadata(cls, metadata: 'ToolMetadata', **kwargs):
        config_class = _clazz if (_clazz := kwargs.get('config_class')) else metadata.config_class
        settings_config = _settings_config if (
            _settings_config := kwargs.get('settings_config')) else metadata.settings_config
        tool_class = kwargs.get('tool_class')
        return cls(
            name=metadata.name,
            label=metadata.label or None,
            description=metadata.description or None,
            user_description=metadata.user_description or None,
            config_class=config_class,
            settings_config=settings_config,
            tool_class=tool_class
        )


class ToolKit(BaseModel):
    toolkit: str
    tools: List[Tool]
    label: Optional[str] = ""
    settings_config: Optional[bool] = False
    is_external: bool = False
    config_class: Optional[Any] = None


class ToolOutputFormat(str, Enum):
    TEXT = "text"
    MARKDOWN = "markdown"


class CodeMieToolConfig(BaseModel):
    """Empty Pydantic class for CodeMie tool configuration."""
    pass
