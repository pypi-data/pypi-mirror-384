from typing import Any, Optional, Dict, Tuple, get_args, get_origin, get_type_hints, Union, ForwardRef, TypeVar
from collections.abc import Mapping
from argparse import Namespace
from types import SimpleNamespace
import sys
from ewoxcore.utils.dictionary_util import DictionaryUtil

_PRIMITIVES = {str, int, float, bool, bytes}

T = TypeVar("T")


class ClassUtil:
    @staticmethod
    def merge(class_a:Any, class_b:Any) -> Any:
        if hasattr(class_a, "_merge_classes") and callable(getattr(class_a, "_merge_classes", None)):
            class_a._merge_classes(class_b.__dict__)
        else:
            class_a.__dict__.update(class_b.__dict__)

        return class_a


    @staticmethod
    def merge_from_type(class_type:T, class_b:Any) -> Any:
        model:T = None
        class_b:dict[str, Any] = DictionaryUtil.normalize(class_b)
        if (ClassUtil.is_namespace(class_b)):
            model = class_type(class_b.__dict__)
        elif (ClassUtil.is_dict(class_b)):
            model = class_type(class_b)
        else:
            raise Exception("class_b must be a Namespace or a Dict")

        return model


    @staticmethod
    def get_class_name(cls:Any) -> str:
        if cls is None:
            return ""
        return cls.__name__ if isinstance(cls, type) else type(cls).__name__


    @staticmethod
    def get_class_instance_name(cls:Any) -> str:
       return cls.__class__.__name__ if cls is not None else ""


    @staticmethod
    def is_namespace(val:Any) -> bool:
        return isinstance(val, (Namespace, SimpleNamespace))


    @staticmethod
    def is_dict(val:Any) -> bool:
        return isinstance(val, Mapping)

    # @staticmethod
    # def get_class_names(model: Any) -> List[str]:
    #     class_names = set()

    #     # Add class name of the model itself
    #     class_names.add(type(model).__name__)

    #     # Get attributes of the model
    #     try:
    #         attributes = vars(model)
    #     except TypeError:
    #         # model has no __dict__ (e.g. primitive)
    #         return List(class_names)

    #     for attr_name, attr_value in attributes.items():
    #         if attr_value is None:
    #             continue

    #         # Check if it's a list and has elements
    #         if isinstance(attr_value, list) and len(attr_value) > 0:
    #             first_elem = attr_value[0]
    #             elem_class_name = type(first_elem).__name__
    #             if elem_class_name not in ["dict", "list", "str", "int", "float", "bool"]:
    #                 class_names.add(elem_class_name)

    #         # Check if it's another object (not primitive, not list)
    #         elif hasattr(attr_value, "__dict__"):
    #             value_class_name = type(attr_value).__name__
    #             if value_class_name not in ["dict", "list", "str", "int", "float", "bool"]:
    #                 class_names.add(value_class_name)

    #     return list(class_names)

                # qualname:str = tp.__qualname__
                # print(f"{type(tp).__module__}.{type(tp).__qualname__}")


    # @staticmethod
    # def get_class_names_old(model: Any) -> List[str]:
    #     names: Set[str] = set()
    #     seen: Set[type] = set()

    #     def add_type(tp: Any):
    #         if isinstance(tp, type) and tp not in _PRIMITIVES and tp not in {list, dict, tuple, set}:
    #             names.add(tp.__name__)
    #             return True
    #         return False

    #     def walk_type(tp: Any, queue: List[type]):
    #         origin = get_origin(tp)
    #         if origin is None:
    #             if add_type(tp):
    #                 queue.append(tp)
    #             return
    #         if origin is Union:
    #             for arg in get_args(tp):
    #                 if arg is type(None):
    #                     continue
    #                 walk_type(arg, queue)
    #             return

    #         # List[T], Dict[K,V], etc.
    #         for arg in get_args(tp):
    #             walk_type(arg, queue)


    #     def inspect_class(cls: type, queue: List[type]):
    #         if cls in seen:
    #             return
    #         seen.add(cls)
    #         mod_globals = vars(sys.modules.get(cls.__module__, object()))
    #         hints = {}
    #         try:
    #             hints = get_type_hints(cls, globalns=mod_globals, localns=vars(cls))
    #         except Exception:
    #             hints = getattr(cls, "__annotations__", {}) or {}
    #         for tp in hints.values():
    #             walk_type(tp, queue)

    #     # seed with the model’s own type
    #     names.add(type(model).__name__)
    #     queue: List[type] = [type(model)]

    #     # Instance values to recover types from populated lists/objects
    #     try:
    #         for val in vars(model).values():
    #             if val is None:
    #                 continue
    #             if isinstance(val, list) and val:
    #                 if add_type(type(val[0])): queue.append(type(val[0]))
    #             elif not isinstance(val, (str, int, float, bool, bytes, list, dict, tuple, set)):
    #                 if add_type(type(val)): queue.append(type(val))
    #     except TypeError:
    #         pass

    #     while queue:
    #         inspect_class(queue.pop(), queue)

    #     return sorted(names)


    @staticmethod
    def get_class_names(model: Any) -> list[str]:
        names: set[str] = set()
        seen_types: set[type] = set()
        seen_ids: set[int] = set()  # for instance graph cycle protection

        def add_type(tp: Any) -> bool:
            if isinstance(tp, type) and tp not in _PRIMITIVES and tp not in {list, dict, tuple, set}:
                names.add(tp.__name__)
                return True
            return False

        # ----- Static/type-hint walk -----
        def walk_type(tp: Any, tqueue: list[type]):
            origin = get_origin(tp)
            if origin is None:
                if add_type(tp):
                    tqueue.append(tp)
                return
            if origin is Union:
                for arg in get_args(tp):
                    if arg is type(None):
                        continue
                    walk_type(arg, tqueue)
                return
            # e.g. List[T], Dict[K, V], Tuple[…], etc.
            for arg in get_args(tp):
                walk_type(arg, tqueue)

        def inspect_class(cls: type, tqueue: list[type]):
            if cls in seen_types:
                return
            seen_types.add(cls)
            mod_globals = vars(sys.modules.get(cls.__module__, object()))
            try:
                hints = get_type_hints(cls, globalns=mod_globals, localns=vars(cls))
            except Exception:
                hints = getattr(cls, "__annotations__", {}) or {}
            for tp in hints.values():
                walk_type(tp, tqueue)

        # ----- Dynamic/instance walk (RECURSIVE) -----
        def walk_instance(obj: Any):
            oid = id(obj)
            if oid in seen_ids:
                return
            seen_ids.add(oid)

            # record this object's concrete type
            add_type(type(obj))

            # containers
            if isinstance(obj, (list, tuple, set)):
                for item in obj:
                    walk_instance(item)
                return
            if isinstance(obj, dict):
                for k, v in obj.items():
                    walk_instance(k)
                    walk_instance(v)
                return

            # primitives stop here
            if isinstance(obj, tuple(_PRIMITIVES)):
                return

            # generic objects: traverse their attributes
            try:
                for val in vars(obj).values():
                    if val is not None:
                        walk_instance(val)
            except TypeError:
                # objects without __dict__
                pass

        # seed with the model’s own type
        add_type(type(model))

        # Walk the instance graph to capture runtime subclasses based on inheritance
        walk_instance(model)

        # Walk the type graph to include annotated types you might not have populated yet
        tqueue: list[type] = list({type(model), *[type(v) for v in vars(model).values()
                                                if not isinstance(v, tuple(_PRIMITIVES | {list, dict, tuple, set}))]})
        while tqueue:
            inspect_class(tqueue.pop(), tqueue)

        return sorted(names)