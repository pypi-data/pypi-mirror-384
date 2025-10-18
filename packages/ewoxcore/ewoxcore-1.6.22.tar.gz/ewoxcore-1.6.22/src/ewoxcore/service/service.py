from typing import Any, Callable, List, Dict, Text, Optional, Tuple, Union, Awaitable, TypeVar, Type
from ewoxcore.constants.global_key import GlobalKey

T = TypeVar('T')


def get_service(type:T) -> T:
    globals_dict:Dict[str, Any] = globals()
    if (GlobalKey.GetService not in globals_dict):
        return None

    get_service:Callable[[Type[T]], T] = globals()[GlobalKey.GetService]
    return get_service(type)


def add_service(get_service:Callable[[Type[T]], T]) -> None:
    globals()[GlobalKey.GetService] = get_service
