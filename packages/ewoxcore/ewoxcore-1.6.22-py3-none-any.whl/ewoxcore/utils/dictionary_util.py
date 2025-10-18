from typing import Any
from collections.abc import Mapping
from argparse import Namespace
from types import SimpleNamespace
import inspect


class DictionaryUtil:
    @staticmethod
    def get(dict:dict[str, Any], name:str, default:Any) -> Any:
        return dict[name] if (name in dict) else default


    @staticmethod
    def to_dict(obj) -> dict[str, Any]:
        d = {}
        for name in dir(obj):
            value = getattr(obj, name)
            if not name.startswith('__') and not inspect.ismethod(value):
                d[name] = value
        return d
    
    
    @staticmethod
    def convert(model:Any) -> dict[str, Any]:
        d = dict((name, getattr(model, name)) for name in dir(model) if not name.startswith('__') and not inspect.ismethod(name))

        return d


    @staticmethod
    def normalize(obj: Any) -> dict[str, Any]:
        if isinstance(obj, (Namespace, SimpleNamespace)):
            return {k: DictionaryUtil.normalize(v) for k, v in vars(obj).items()}

        if isinstance(obj, Mapping):
            return {k: DictionaryUtil.normalize(v) for k, v in obj.items()}

        if isinstance(obj, list):
            return [DictionaryUtil.normalize(v) for v in obj]
        if isinstance(obj, tuple):
            return tuple(DictionaryUtil.normalize(v) for v in obj)

        if isinstance(obj, set):
            return [DictionaryUtil.normalize(v) for v in obj]

        return obj
