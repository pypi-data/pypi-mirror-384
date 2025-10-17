from typing import Any, Optional, Union

import yaml


class Bag:
    def __getitem__(self, k):
        return self.__dict__[k]

    def __contains__(self, k):
        return k in self.__dict__

    def __iter__(self):
        return iter(self.__dict__.items())

    def __repr__(self):
        return str(self.__dict__)


class Config:
    def __init__(self, path_or_parsed: Union[str, dict]):
        _t = type(path_or_parsed)
        if _t is str:
            with open(path_or_parsed) as f:
                d = yaml.safe_load(f.read())
        elif _t is dict:
            d = path_or_parsed
        else:
            raise Exception("Config requires either a YAML string or a dictionary")
        if d is not None:
            self.__to_members(d)
            self.map = d

    def __to_members(self, d: Any, root: Optional[Any] = None):
        if isinstance(d, list):
            d = [self.__to_members(x, Bag()) for x in d]

        if not isinstance(d, dict):
            return d

        if root is None:
            root = self

        for k in d:
            root.__dict__[k] = self.__to_members(d[k], Bag())

        return root
