from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Awaitable,
    Callable,
    Collection,
    Generator,
    Iterable,
    Iterator,
)
from inspect import isclass, isfunction
from types import GenericAlias, UnionType
from typing import (
    Annotated,
    Any,
    TypeAliasType,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

type TypeDef[T] = type[T] | TypeAliasType | GenericAlias
type InputType[T] = TypeDef[T] | UnionType
type TypeInfo[T] = (
    InputType[T]
    | Callable[..., T]
    | Callable[..., Awaitable[T]]
    | Collection[TypeInfo[T]]
)


def get_return_types(*args: TypeInfo[Any]) -> Iterator[InputType[Any]]:
    for arg in args:
        if isinstance(arg, Collection) and not isclass(arg):
            inner_args = arg

        elif isfunction(arg) and (return_type := get_return_hint(arg)):
            inner_args = (return_type,)

        else:
            yield arg  # type: ignore[misc]
            continue

        yield from get_return_types(*inner_args)


def get_return_hint[T](function: Callable[..., T]) -> InputType[T] | None:
    return get_type_hints(function).get("return")


def get_yield_hint[T](
    function: Callable[..., Iterator[T]] | Callable[..., AsyncIterator[T]],
) -> tuple[InputType[T]] | tuple[()]:
    return_type = get_return_hint(function)

    if get_origin(return_type) in {
        AsyncGenerator,
        AsyncIterable,
        AsyncIterator,
        Generator,
        Iterable,
        Iterator,
    }:
        for arg in get_args(return_type):
            return (arg,)

    return ()


def standardize_types(
    *types: InputType[Any],
    with_origin: bool = False,
) -> Iterator[TypeDef[Any]]:
    for tp in types:
        if tp is None:
            continue

        origin = get_origin(tp)

        if origin is Union or isinstance(tp, UnionType):
            inner_types = get_args(tp)

        elif origin is Annotated:
            inner_types = get_args(tp)[:1]

        else:
            yield tp

            if with_origin:
                if origin is not None:
                    yield origin

                for alias in (tp, origin):
                    if isinstance(alias, TypeAliasType):
                        yield from standardize_types(
                            alias.__value__,
                            with_origin=with_origin,
                        )

            continue

        yield from standardize_types(*inner_types, with_origin=with_origin)
