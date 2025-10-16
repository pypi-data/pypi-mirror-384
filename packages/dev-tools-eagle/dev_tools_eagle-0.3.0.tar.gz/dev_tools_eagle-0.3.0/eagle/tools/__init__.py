from langchain_core.tools import BaseTool
from eagle.tools.search_engines import *
from eagle.tools.math import *
from eagle.tools.memory_access import *
from eagle.utils.classes_utils import get_all_subclasses

def _generate_tools_dict():
    """
    Generate a dictionary of all tools available in the eagle.tools module.
    """
    __TOOLS_DICT = {
        cls.model_fields['name'].default: {"class": cls, "description": cls.model_fields['description'].default, "name": cls.model_fields['name'].default}
        for cls in get_all_subclasses(BaseTool) if hasattr(cls, '__name__') if isinstance(cls.model_fields['name'].default, str)
    }
    return __TOOLS_DICT

def get_tool(tool_name: str) -> BaseTool:
    """
    Get the tool class by name.
    """
    try:
        tools_dict = _generate_tools_dict()
        return tools_dict.get(tool_name)
    except KeyError:
        raise KeyError(f"Tool {tool_name} not found as a BaseTool.")