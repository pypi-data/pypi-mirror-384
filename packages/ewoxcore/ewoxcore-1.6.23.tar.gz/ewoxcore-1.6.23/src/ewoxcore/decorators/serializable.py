from typing import Any, Callable, Generic, List, Dict, Text, Optional, Tuple, Union, TypeVar, Type
from collections.abc import Mapping
import types
from ewoxcore.service.class_registry import ClassRegistry

# def Serializable(cls):
#     class_name = cls.__name__
#     orig_init = cls.__init__

#     def __init__(self, *args, **kwargs):
#         orig_init(self, *args, **kwargs)
#         self.__type = class_name

#     def update(self, data: Union[Mapping[str, Any], Any], *,
#                 allow_new: bool = True,
#                 ignore_none: bool = False) -> Any:
#             # Mutates self by copying attributes/keys from `data`.
#             # - data can be a dict-like or another object.
#             # - allow_new=False will only update attributes that already exist on self.
#             # - ignore_none=True will skip None values from data.

#             # Accept dict-like or object
#             if isinstance(data, Mapping):
#                 src = dict(data)
#             else:
#                 # fall back to vars()/__dict__ for objects
#                 src = vars(data) if hasattr(data, "__dict__") else {}

#             for k, v in src.items():
#                 if not allow_new and not hasattr(cls, k):
#                     continue
#                 if ignore_none and v is None:
#                     continue

#                 # if isinstance(v, Mapping):
#                 #     print(f"Mapping: {k} -> {v}")
#                 if isinstance(v, types.SimpleNamespace) or hasattr(v, "__dict__"):
#                     print(f"Object: {k} -> {v}")
                
#                 # if (isinstance(v, dict)):
#                     if (hasattr(v, "__type") == True):
#                         name:str = getattr(v, "__type", "")
#                         if (name):
#                             ctor = ClassRegistry.get(name)
#                             if (ctor):
#                                 # data_v:Dict[str, Any] = dict(vars(v))
#                                 data_v:Dict[str, Any] = self.ns_to_dict(v)
#                                 v = ctor(data_v)

#                 setattr(self, k, v)

#             return self
        

#     def ns_to_dict(self, obj: Any) -> Any:
#         if isinstance(obj, types.SimpleNamespace):
#             return {k: self.ns_to_dict(v) for k, v in vars(obj).items()}
#         if isinstance(obj, dict):
#             return {k: self.ns_to_dict(v) for k, v in obj.items()}
#         if isinstance(obj, list):
#             return [self.ns_to_dict(x) for x in obj]
#         if isinstance(obj, tuple):
#             return tuple(self.ns_to_dict(x) for x in obj)

#         return obj

#     cls.__init__ = __init__
#     return cls


def Serializable(cls):
    class_name = cls.__name__
    orig_init = getattr(cls, "__init__", lambda self, *a, **k: None)

    def __init__(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        setattr(self, "__type", class_name)


    def _ns_to_dict(self, obj: Any) -> Any:
        if isinstance(obj, types.SimpleNamespace):
            return {k: self._ns_to_dict(v) for k, v in vars(obj).items()}

        if isinstance(obj, Mapping):
            return {k: self._ns_to_dict(v) for k, v in obj.items()}
        
        if isinstance(obj, list):
            return [self._ns_to_dict(x) for x in obj]

        if isinstance(obj, tuple):
            return tuple(self._ns_to_dict(x) for x in obj)

        if hasattr(obj, "__dict__") and not isinstance(obj, (str, bytes, int, float, bool)):
            return {k: self._ns_to_dict(v) for k, v in vars(obj).items()}

        return obj


    def _merge_classes(self, data: Union[Mapping[str, Any], Any], *,
               allow_new: bool = True,
               ignore_none: bool = False) -> Any:
        if isinstance(data, Mapping):
            src = dict(data)
        else:
            src = vars(data) if hasattr(data, "__dict__") else {}

        for k, v in src.items():
            if not allow_new and not hasattr(self, k):
                continue
            if ignore_none and v is None:
                continue

            if isinstance(v, (types.SimpleNamespace, object)) and hasattr(v, "__dict__"):
                t = getattr(v, "__type", None)
                if t:
                    ctor = ClassRegistry.get(t)
                    if ctor:
                        v = ctor(self._ns_to_dict(v))

            setattr(self, k, v)

        return self

    # Attach to the class
    cls.__init__ = __init__
    cls._ns_to_dict = _ns_to_dict
    cls._merge_classes = _merge_classes

    return cls