from abc import ABC, abstractmethod

from pydantic import BaseModel


class BaseToolkit(BaseModel, ABC):

    @classmethod
    def get_definition(cls):
        """
        Returns the toolkit definition containing information about the toolkit and its tools.
        This method is used by the toolkit scanner to discover available toolkits and their tools.
    
        Returns:
            ToolKit: A ToolKit object containing toolkit information and list of tools
        """
        # Get the toolkit UI info which contains the toolkit definition
        toolkit_info = cls.get_tools_ui_info()
    
        # If the result is a dictionary, convert it to a ToolKit object
        if isinstance(toolkit_info, dict):
            from codemie_tools.base.models import ToolKit
            return ToolKit(**toolkit_info)
    
        # If it's already a ToolKit object, return it directly
        return toolkit_info

    def get_tools(self, *args, **kwargs):
        raise NotImplementedError("get_tools method is not implemented for toolkit")

    @classmethod
    def get_tools_ui_info(cls, *args, **kwargs):
        raise NotImplementedError("Toolkit couldn't be used on UI")

    def get_toolkit(self, *args, **kwargs):
        return self.__class__()


class DiscoverableToolkit(BaseToolkit):
    """A marker interface that indicates a toolkit should be autodiscovered.

    Any toolkit that implements this interface will be automatically discovered
    by the toolkit_provider
    """
    pass
