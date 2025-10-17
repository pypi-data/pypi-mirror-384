from __future__ import annotations

from abc import ABCMeta, abstractmethod
from atexit import register
from typing import Any, TypeVar

T = TypeVar("T")


class DBMeta(ABCMeta):
    def __call__(cls: type[T], *args: Any, **kwargs: Any) -> T:
        ins = super().__call__(*args, **kwargs)

        if hasattr(ins, "_open") and callable(getattr(ins, "_open")):
            getattr(ins, "_open")()

        if hasattr(ins, "_close") and callable(getattr(ins, "_close")):
            register(getattr(ins, "_close"))

        return ins


class DB(metaclass=DBMeta):
    @abstractmethod
    def _open(self) -> None:
        ...

    @abstractmethod
    def _close(self) -> None:
        ...

    @classmethod
    @abstractmethod
    def from_uri(cls, uri: str) -> DB:
        ...
