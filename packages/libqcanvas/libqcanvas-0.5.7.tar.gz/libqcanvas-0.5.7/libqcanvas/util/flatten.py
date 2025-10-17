import functools
import operator
from typing import Iterable


def flatten[T](the_list: Iterable[Iterable[T]]) -> list[T]:
    return functools.reduce(operator.iconcat, the_list, [])
