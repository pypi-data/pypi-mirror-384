from typing import (
    TypeVar,
)

from fa_purity import (
    FrozenDict,
    FrozenList,
    Maybe,
    ResultE,
    ResultFactory,
)

_T = TypeVar("_T")
_K = TypeVar("_K")
_V = TypeVar("_V")


def assert_non_list(item: _T | FrozenList[_T]) -> ResultE[_T]:
    factory: ResultFactory[_T, Exception] = ResultFactory()
    if isinstance(item, tuple):
        return factory.failure(ValueError("Expected single value"))
    return factory.success(item)


def get_key(items: FrozenDict[_K, _V], key: _K) -> Maybe[_V]:
    if key in items:
        return Maybe.some(items[key])
    return Maybe.empty()
