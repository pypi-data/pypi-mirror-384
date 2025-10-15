from __future__ import (
    annotations,
)

from collections.abc import Callable
from dataclasses import (
    dataclass,
)
from typing import (
    Generic,
    TypeVar,
)

from fa_purity._core.coproduct import Coproduct
from fa_purity._core.result import (
    Result,
)

_A = TypeVar("_A")
_B = TypeVar("_B")


@dataclass(frozen=True)
class Maybe(Generic[_A]):
    """
    Represents something or emptiness.

    Equivalent to `Result[_A, None]`, but designed to handle possible empty values
    """

    _value: Result[_A, None]

    @staticmethod
    def some(value: _A) -> Maybe[_A]:
        return Maybe(Result.success(value))

    @staticmethod
    def empty(_type: type[_A] | None = None) -> Maybe[_A]:
        return Maybe.from_optional(None)

    @staticmethod
    def from_optional(value: _A | None) -> Maybe[_A]:
        if value is None:
            return Maybe(Result.failure(value))
        return Maybe(Result.success(value))

    @staticmethod
    def from_result(result: Result[_A, None]) -> Maybe[_A]:
        return Maybe(result)

    def to_result(self) -> Result[_A, None]:
        return self._value

    def map(self, function: Callable[[_A], _B]) -> Maybe[_B]:
        return Maybe(self._value.map(function))

    def bind(self, function: Callable[[_A], Maybe[_B]]) -> Maybe[_B]:
        return Maybe(self._value.bind(lambda a: function(a).to_result()))

    def bind_optional(self, function: Callable[[_A], _B | None]) -> Maybe[_B]:
        return self.bind(lambda a: Maybe.from_optional(function(a)))

    def lash(self, function: Callable[[], Maybe[_A]]) -> Maybe[_A]:
        return Maybe(self._value.lash(lambda _: function().to_result()))

    def value_or(self, default: _B) -> _A | _B:
        return self._value.value_or(default)

    def or_else_call(self, function: Callable[[], _B]) -> _A | _B:
        return self._value.or_else_call(function)

    def to_coproduct(self) -> Coproduct[_A, None]:
        return self._value.to_coproduct()

    def __str__(self) -> str:
        return self.__class__.__name__ + self.map(
            lambda x: ".some(" + str(x) + ")",
        ).value_or(".empty()")

    def __repr__(self) -> str:
        return str(self)
