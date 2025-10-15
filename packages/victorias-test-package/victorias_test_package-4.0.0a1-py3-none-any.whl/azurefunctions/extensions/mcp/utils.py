#  Copyright (c) Microsoft Corporation. All rights reserved.
#  Licensed under the MIT License.

from enum import Enum
from typing import TypeVar, Type, Optional, Union


T = TypeVar("T", bound=Enum)


def parse_singular_param_to_enum(param: Optional[Union[T, str]],
                                 class_name: Type[T]) -> Optional[T]:
    if param is None:
        return None
    if isinstance(param, str):
        try:
            return class_name[param.upper()]
        except KeyError:
            raise KeyError(
                f"Can not parse str '{param}' to {class_name.__name__}. "
                f"Allowed values are {[e.name for e in class_name]}")

    return param