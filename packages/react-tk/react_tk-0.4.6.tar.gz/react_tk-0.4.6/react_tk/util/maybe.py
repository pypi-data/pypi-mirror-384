from typing import overload
from expression import Option, Some, Nothing


def maybe_normalize[T](x: T | Option[T]) -> Option[T]:

    if isinstance(x, Option):
        return x

    return Some(x)


type MaybeOption[T] = Option[T] | T
