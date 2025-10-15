#  Copyright (c) Microsoft Corporation. All rights reserved.
#  Licensed under the MIT License.

from .mcp import MCPToolTrigger
from ..utils import parse_singular_param_to_enum

from azure.functions import (AuthLevel, DataType, TriggerApi, FunctionRegister)
from typing import Any, Callable, Optional, Union


class Blueprint(TriggerApi):
    """MCP Blueprint container.

    It allows functions to be declared via trigger decorators,
    but does not automatically index/register these functions.

    To register these functions, utilize the `register_functions` method from any
    :class:`FunctionRegister` subclass, such as `McpApp`.
    """
    def __init__(self,
                 http_auth_level: Union[AuthLevel, str] = AuthLevel.FUNCTION):
        """Instantiate an MCP app with which to register Functions.

        Parameters
        ----------
        http_auth_level: Union[AuthLevel, str]
            Authorization level required for Function invocation.
            Defaults to AuthLevel.Function.

        Returns
        -------
        McpApp
            New instance of an MCP app
        """
        super().__init__(auth_level=http_auth_level)

    def mcp_tool(self,
                 arg_name: str,
                 tool_name: str,
                 description: Optional[str] = None,
                 tool_properties: Optional[str] = None,
                 data_type: Optional[Union[DataType, str]] = None,
                 **kwargs) -> Callable[..., Any]:
        """
        The `mcp_tool` decorator adds :class:`MCPToolTrigger` to the
        :class:`FunctionBuilder` object for building a :class:`Function` object
        used in the worker function indexing model.

        This is equivalent to defining `MCPToolTrigger` in the `function.json`,
        which enables the function to be triggered when MCP tool requests are
        received by the host.

        All optional fields will be given default values by the function host when
        they are parsed.

        Ref: https://aka.ms/remote-mcp-functions-python

        :param arg_name: The name of the trigger parameter in the function code.
        :param tool_name: The logical tool name exposed to the host.
        :param description: Optional human-readable description of the tool.
        :param tool_properties: JSON-serialized tool properties/parameters list.
        :param data_type: Defines how the Functions runtime should treat the
            parameter value.
        :param kwargs: Keyword arguments for specifying additional binding
            fields to include in the binding JSON.

        :return: Decorator function.
        """

        @self._configure_function_builder
        def wrap(fb):
            def decorator():
                fb.add_trigger(
                    trigger=MCPToolTrigger(
                        name=arg_name,
                        tool_name=tool_name,
                        description=description,
                        tool_properties=tool_properties,
                        data_type=parse_singular_param_to_enum(data_type,
                                                               DataType),
                        **kwargs))
                return fb

            return decorator()

        return wrap


class McpApp(Blueprint, FunctionRegister):
    """MCP Function app.

    Exports the decorators required to declare and index MCP Function-types.
    """
    pass