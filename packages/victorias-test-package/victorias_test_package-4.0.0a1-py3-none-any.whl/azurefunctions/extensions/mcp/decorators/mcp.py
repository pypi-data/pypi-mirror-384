#  Copyright (c) Microsoft Corporation. All rights reserved.
#  Licensed under the MIT License.

from ..constants import (
    MCP_TOOL_TRIGGER
)

from typing import get_origin, get_args, Annotated, Tuple, Any, Dict, Optional
from azure.functions.decorators.core import Trigger, DataType


class MCPToolTrigger(Trigger):

    @staticmethod
    def get_binding_name() -> str:
        return MCP_TOOL_TRIGGER

    def __init__(self,
                 name: str,
                 tool_name: str,
                 description: Optional[str] = None,
                 tool_properties: Optional[str] = None,
                 data_type: Optional[DataType] = None,
                 **kwargs):
        self.tool_name = tool_name
        self.description = description
        self.tool_properties = tool_properties
        super().__init__(name=name, data_type=data_type)


class MCPToolContext(Dict[str, Any]):
    pass


class ToolProperty:
    def __init__(self, property_name: str, property_type: str, description: str):
        self.propertyName = property_name
        self.propertyType = property_type
        self.description = description

    def to_dict(self):
        return {
            "propertyName": self.propertyName,
            "propertyType": self.propertyType,
            "description": self.description,
        }


def _extract_type_and_description(param_name: str, type_hint: Any) -> Tuple[Any, str]:
    """
    Extract the actual type and description from a type hint, handling Annotated types.
    
    Args:
        param_name: The parameter name
        type_hint: The type hint (could be Annotated or regular type)
    
    Returns:
        tuple: (actual_type, description)
    """
    # Check if it's an Annotated type
    if get_origin(type_hint) is Annotated:
        args = get_args(type_hint)
        actual_type = args[0]  # First argument is the actual type
        # Look for string descriptions in the annotations
        param_description = f"The {param_name} parameter."  # Default description
        for annotation in args[1:]:
            if isinstance(annotation, str):
                param_description = annotation
                break
        return actual_type, param_description
    else:
        # Regular type hint
        return type_hint, f"The {param_name} parameter."