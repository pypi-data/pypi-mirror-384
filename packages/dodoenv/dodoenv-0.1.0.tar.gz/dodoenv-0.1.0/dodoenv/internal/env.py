import os
from typing import Callable, TypeVar, Generic
from .exception import EnvNotFoundException

T = TypeVar("T")

class Env(Generic[T]):
    def __init__(self, default:T|None=None, func: Callable[[str], T] | None = None) -> None:
        self.func = func
        self.default = default

    def __set_name__(self, owner, name):
        res = os.environ.get(name)
        if self.default is not None and res is None:
            self.value = self.default
            return

        assert res, EnvNotFoundException(name)

        if self.func:
            res = self.func(res)

        self.value = res

    def __get__(self, instance, owner) -> T:
        return self.value  # type:ignore