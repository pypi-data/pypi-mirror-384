#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import operator
import random
import sys
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Hashable,
    Iterable,
    List,
    Literal,
    Mapping,
    MutableSequence,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    get_args,
    overload,
)

from typing_extensions import TypeGuard, TypeIs

from pythonwrench.collections.prop import all_eq
from pythonwrench.collections.reducers import reduce_or
from pythonwrench.functools import identity
from pythonwrench.semver import Version
from pythonwrench.typing.checks import is_builtin_scalar, isinstance_generic
from pythonwrench.typing.classes import T_BuiltinScalar

K = TypeVar("K", covariant=True, bound=Hashable)

T = TypeVar("T", covariant=True)
U = TypeVar("U", covariant=True)
V = TypeVar("V", covariant=True)
W = TypeVar("W", covariant=True)
X = TypeVar("X", covariant=True)
Y = TypeVar("Y", covariant=True)

KeyMode = Literal["intersect", "same", "union"]
Order = Literal["left", "right"]


def contained(
    x: T,
    include: Optional[Iterable[T]] = None,
    exclude: Optional[Iterable[T]] = None,
    *,
    match_fn: Callable[[T, T], bool] = operator.eq,
    order: Literal["left", "right"] = "right",
) -> bool:
    """Returns True if name in include set and not in exclude set."""
    if (
        include is not None
        and find(x, include, match_fn=match_fn, order=order, default=-1) == -1
    ):
        return False

    if (
        exclude is not None
        and find(x, exclude, match_fn=match_fn, order=order, default=-1) != -1
    ):
        return False

    return True


@overload
def dict_list_to_list_dict(
    dic: Mapping[T, Iterable[U]],
    key_mode: Literal["union"] = "union",
    default_val: W = None,
) -> List[Dict[T, Union[U, W]]]: ...


@overload
def dict_list_to_list_dict(
    dic: Mapping[T, Iterable[U]],
    key_mode: Literal["same", "intersect"],
    default_val: Any = None,
) -> List[Dict[T, U]]: ...


def dict_list_to_list_dict(
    dic: Mapping[T, Iterable[U]],
    key_mode: KeyMode = "union",
    default_val: W = None,
) -> List[Dict[T, Union[U, W]]]:
    """Convert dict of lists with same sizes to list of dicts.

    Example 1
    ---------
    >>> dic = {"a": [1, 2], "b": [3, 4]}
    >>> dict_list_to_list_dict(dic)
    ... [{"a": 1, "b": 3}, {"a": 2, "b": 4}]

    Example 2
    ---------
    >>> dic = {"a": [1, 2, 3], "b": [4], "c": [5, 6]}
    >>> dict_list_to_list_dict(dic, key_mode="union", default=-1)
    ... [{"a": 1, "b": 4, "c": 5}, {"a": 2, "b": -1, "c": 6}, {"a": 3, "b": -1, "c": -1}]
    """
    if len(dic) == 0:
        return []

    dic = {k: list(v) if not isinstance(v, Sequence) else v for k, v in dic.items()}
    lengths = [len(seq) for seq in dic.values()]

    if key_mode == "same":
        if not all_eq(lengths):
            msg = f"Invalid sequences for batch. (found different lengths in sub-lists: {set(lengths)})"
            raise ValueError(msg)
        length = lengths[0]

    elif key_mode == "intersect":
        length = min(lengths)

    elif key_mode == "union":
        length = max(lengths)

    else:
        msg = f"Invalid argument key_mode={key_mode}. (expected one of {get_args(KeyMode)})"
        raise ValueError(msg)

    result = [
        {k: (v[i] if i < len(v) else default_val) for k, v in dic.items()}
        for i in range(length)
    ]
    return result


def dump_dict(
    dic: Optional[Mapping[str, T]] = None,
    /,
    join: str = ", ",
    fmt: str = "{key}={value}",
    ignore_lst: Iterable[T] = (),
    **kwargs,
) -> str:
    """Dump dictionary of scalars to string function to customize representation.

    Example 1:
    ----------
    >>> d = {"a": 1, "b": 2}
    >>> dump_dict(d)
    ... 'a=1, b=2'
    """
    if dic is None:
        dic = {}
    else:
        dic = dict(dic.items())
    dic.update(kwargs)

    ignore_lst = dict.fromkeys(ignore_lst)
    result = join.join(
        fmt.format(key=key, value=value)
        for key, value in dic.items()
        if value not in ignore_lst
    )
    return result


def filter_iterable(
    it: Iterable[T],
    include: Optional[Iterable[T]] = None,
    exclude: Optional[Iterable[T]] = None,
    *,
    match_fn: Callable[[T, T], bool] = operator.eq,
    order: Literal["left", "right"] = "right",
) -> List[T]:
    return [
        item
        for item in it
        if contained(
            item,
            include=include,
            exclude=exclude,
            match_fn=match_fn,
            order=order,
        )
    ]


@overload
def find(
    target: T,
    it: Iterable[V],
    *,
    match_fn: Callable[[V, T], bool] = operator.eq,
    order: Literal["right"] = "right",
    default: U = -1,
    return_value: Literal[False] = False,
) -> Union[int, U]: ...


@overload
def find(
    target: T,
    it: Iterable[V],
    *,
    match_fn: Callable[[T, V], bool] = operator.eq,
    order: Literal["left"],
    default: U = -1,
    return_value: Literal[False] = False,
) -> Union[int, U]: ...


@overload
def find(
    target: T,
    it: Iterable[V],
    *,
    match_fn: Callable[[V, T], bool] = operator.eq,
    order: Literal["right"] = "right",
    default: U = -1,
    return_value: Literal[True],
) -> Tuple[Union[int, U], Union[V, U]]: ...


@overload
def find(
    target: T,
    it: Iterable[V],
    *,
    match_fn: Callable[[T, V], bool] = operator.eq,
    order: Literal["left"],
    default: U = -1,
    return_value: Literal[True],
) -> Tuple[Union[int, U], Union[V, U]]: ...


def find(
    target: Any,
    it: Iterable[V],
    *,
    match_fn: Callable[[Any, Any], bool] = operator.eq,
    order: Order = "right",
    default: U = -1,
    return_value: bool = False,
) -> Union[int, U, Tuple[Union[int, U], Union[V, U]]]:
    if not return_value:
        result = find(
            target,
            it,
            match_fn=match_fn,
            order=order,
            default=default,
            return_value=True,
        )
        return result[0]

    if order == "right":
        pass
    elif order == "left":

        def revert(f):
            def reverted_f(a, b):
                return f(b, a)

            return reverted_f

        match_fn = revert(match_fn)
    else:
        raise ValueError(
            f"Invalid argument {order=}. (expected one of {get_args(Order)})"
        )

    for i, xi in enumerate(it):
        if match_fn(xi, target):
            return i, xi

    return default, default


@overload
def flatten(
    x: T_BuiltinScalar,
    start_dim: int = 0,
    end_dim: Optional[int] = None,
) -> List[T_BuiltinScalar]: ...


@overload
def flatten(  # type: ignore
    x: Iterable[T_BuiltinScalar],
    start_dim: int = 0,
    end_dim: Optional[int] = None,
) -> List[T_BuiltinScalar]: ...


@overload
def flatten(
    x: Any,
    start_dim: int = 0,
    end_dim: Optional[int] = None,
    is_scalar_fn: Union[
        Callable[[Any], TypeGuard[T]], Callable[[Any], TypeIs[T]]
    ] = is_builtin_scalar,
) -> List[Any]: ...


def flatten(
    x: Any,
    start_dim: int = 0,
    end_dim: Optional[int] = None,
    is_scalar_fn: Union[
        Callable[[Any], TypeGuard[T]], Callable[[Any], TypeIs[T]]
    ] = is_builtin_scalar,
) -> List[Any]:
    if end_dim is None:
        end_dim = sys.maxsize
    if start_dim < 0:
        raise ValueError(f"Invalid argument {start_dim=}. (expected positive integer)")
    if end_dim < 0:
        raise ValueError(f"Invalid argument {end_dim=}. (expected positive integer)")
    if start_dim > end_dim:
        msg = f"Invalid arguments {start_dim=} and {end_dim=}. (expected start_dim <= end_dim)"
        raise ValueError(msg)

    def flatten_impl(x: Any, start_dim: int, end_dim: int) -> List[Any]:
        if is_scalar_fn(x):
            return [x]
        elif isinstance(x, Iterable):
            if start_dim > 0:
                return [flatten_impl(xi, start_dim - 1, end_dim - 1) for xi in x]
            elif end_dim > 0:
                return [
                    xij
                    for xi in x
                    for xij in flatten_impl(xi, start_dim - 1, end_dim - 1)
                ]
            else:
                return list(x)
        else:
            raise TypeError(f"Invalid argument type {type(x)=}.")

    return flatten_impl(x, start_dim, end_dim)


def flat_dict_of_dict(
    nested_dic: Mapping[str, Any],
    *,
    sep: str = ".",
    flat_iterables: bool = False,
    overwrite: bool = True,
) -> Dict[str, Any]:
    """Flat a nested dictionary.

    Example 1
    ---------
    >>> dic = {
    ...     "a": 1,
    ...     "b": {
    ...         "a": 2,
    ...         "b": 10,
    ...     },
    ... }
    >>> flat_dict_of_dict(dic)
    ... {"a": 1, "b.a": 2, "b.b": 10}

    Example 2
    ---------
    >>> dic = {"a": ["hello", "world"], "b": 3}
    >>> flat_dict_of_dict(dic, flat_iterables=True)
    ... {"a.0": "hello", "a.1": "world", "b": 3}

    Args:
        nested_dic: Nested mapping containing sub-mappings or iterables.
        sep: Separators between keys.
        flat_iterables: If True, flat iterable and use index as key.
        overwrite: If True, overwrite duplicated keys in output. Otherwise duplicated keys will raises a ValueError.
    """

    def _impl(nested_dic: Mapping[str, Any]) -> Dict[str, Any]:
        output = {}
        for k, v in nested_dic.items():
            if isinstance_generic(v, Mapping[str, Any]):
                v = _impl(v)
                v = {f"{k}{sep}{kv}": vv for kv, vv in v.items()}
                output.update(v)

            elif flat_iterables and isinstance(v, Iterable) and not isinstance(v, str):
                v = {f"{i}": vi for i, vi in enumerate(v)}
                v = _impl(v)
                v = {f"{k}{sep}{kv}": vv for kv, vv in v.items()}
                output.update(v)

            elif overwrite or k not in output:
                output[k] = v

            else:
                msg = f"Ambiguous flatten dict with key '{k}'. (with value '{v}')"
                raise ValueError(msg)
        return output

    return _impl(nested_dic)


@overload
def flat_list_of_list(
    lst: Iterable[Sequence[T]],
    return_sizes: Literal[True] = True,
) -> Tuple[List[T], List[int]]: ...


@overload
def flat_list_of_list(
    lst: Iterable[Sequence[T]],
    return_sizes: Literal[False],
) -> List[T]: ...


def flat_list_of_list(
    lst: Iterable[Sequence[T]],
    return_sizes: bool = True,
) -> Union[Tuple[List[T], List[int]], List[T]]:
    """Return a flat version of the input list of sublists with each sublist size."""
    flatten_lst = [elt for sublst in lst for elt in sublst]
    sizes = [len(sents) for sents in lst]

    if return_sizes:
        return flatten_lst, sizes
    else:
        return flatten_lst


def intersect_lists(lst_of_lst: Sequence[Iterable[T]]) -> List[T]:
    """Performs intersection of elements in lists (like set intersection), but keep their original order."""
    if len(lst_of_lst) <= 0:
        return []
    out = list(dict.fromkeys(lst_of_lst[0]))
    for lst_i in lst_of_lst[1:]:
        out = [name for name in out if name in lst_i]
        if len(out) == 0:
            break
    return out


@overload
def list_dict_to_dict_list(
    lst: Iterable[Mapping[K, V]],
    key_mode: Literal["intersect", "same"] = "same",
    default_val: Any = None,
    *,
    default_val_fn: Any = None,
    list_fn: None = None,
) -> Dict[K, List[V]]: ...


@overload
def list_dict_to_dict_list(
    lst: Iterable[Mapping[K, V]],
    key_mode: Literal["union"],
    default_val: Any = None,
    *,
    default_val_fn: Callable[[K], X],
    list_fn: None = None,
) -> Dict[K, List[Union[V, X]]]: ...


@overload
def list_dict_to_dict_list(
    lst: Iterable[Mapping[K, V]],
    key_mode: Literal["union"],
    default_val: W = None,
    *,
    default_val_fn: None = None,
    list_fn: None = None,
) -> Dict[K, List[Union[V, W]]]: ...


@overload
def list_dict_to_dict_list(
    lst: Iterable[Mapping[K, V]],
    key_mode: Union[KeyMode, Iterable[K]] = "same",
    default_val: W = None,
    *,
    default_val_fn: Optional[Callable[[K], X]] = None,
    list_fn: Callable[[List[Union[V, W, X]]], Y],
) -> Dict[K, Y]: ...


def list_dict_to_dict_list(
    lst: Iterable[Mapping[K, V]],
    key_mode: Union[KeyMode, Iterable[K]] = "same",
    default_val: W = None,
    *,
    default_val_fn: Optional[Callable[[K], X]] = None,
    list_fn: Optional[Callable[[List[Union[V, W, X]]], Y]] = identity,
) -> Dict[K, Y]:
    """Convert list of dicts to dict of lists.

    Args:
        lst: The list of dict to merge.
        key_mode: Can be "same" or "intersect". \
            - If "same", all the dictionaries must contains the same keys otherwise a ValueError will be raised. \
            - If "intersect", only the intersection of all keys will be used in output. \
            - If "union", the output dict will contains the union of all keys, and the missing value will use the argument default_val. \
            - If an iterable of elements, use them as keys for output dict.
        default_val: Default value of an element when key_mode is "union". defaults to None.
        default_val_fn: Function to return the default value according to a specific key. defaults to None.
        list_fn: Optional function to build the values. defaults to identity.
    """
    try:
        item0 = next(iter(lst))
    except StopIteration:
        return {}

    if isinstance(key_mode, str):
        unique_keys = set(item0.keys())

        if key_mode == "same":
            invalids = [
                list(item.keys()) for item in lst if unique_keys != set(item.keys())
            ]
            if len(invalids) > 0:
                msg = f"Invalid dict keys for conversion from List[dict] to Dict[list]. (with {key_mode=}, {unique_keys=} and {invalids=})"
                raise ValueError(msg)
            keys = list(item0.keys())

        elif key_mode == "intersect":
            keys = intersect_lists([item.keys() for item in lst])

        elif key_mode == "union":
            keys = union_lists(item.keys() for item in lst)

        else:
            msg = f"Invalid argument key_mode={key_mode}. (expected one of {get_args(KeyMode)})"
            raise ValueError(msg)
    else:
        keys = list(key_mode)

    if list_fn is None:
        list_fn = identity  # type: ignore

    result = {
        key: list_fn(
            [
                item.get(
                    key,
                    default_val_fn(key) if default_val_fn is not None else default_val,
                )
                for item in lst
            ]
        )  # type: ignore
        for key in keys
    }
    return result  # type: ignore


def recursive_generator(x: Any) -> Generator[Tuple[Any, int, int], None, None]:
    def recursive_generator_impl(
        x: Any,
        i: int,
        deep: int,
    ) -> Generator[Tuple[Any, int, int], None, None]:
        if is_builtin_scalar(x):
            yield x, i, deep
        elif isinstance(x, Iterable):
            for j, xj in enumerate(x):
                if xj == x:
                    yield xj, i, deep
                    return
                else:
                    yield from recursive_generator_impl(xj, j, deep + 1)
        else:
            yield x, i, deep
        return

    return recursive_generator_impl(x, 0, 0)


def sorted_dict(
    x: Mapping[K, V],
    /,
    *,
    key: Optional[Callable[[K], Any]] = None,
    reverse: bool = False,
) -> Dict[K, V]:
    return {k: x[k] for k in sorted(x.keys(), key=key, reverse=reverse)}  # type: ignore


def shuffled(
    x: MutableSequence[T],
    *,
    seed: Optional[int] = None,
    deep: bool = False,
) -> MutableSequence[T]:
    if deep:
        x = copy.deepcopy(x)
    else:
        x = copy.copy(x)

    if seed is None:
        random.shuffle(x)
        return x
    else:
        state = random.getstate()
        random.seed(seed)
        random.shuffle(x)
        state = random.setstate(state)
        return x


def unflat_dict_of_dict(dic: Mapping[str, Any], *, sep: str = ".") -> Dict[str, Any]:
    """Unflat a dictionary.

    Example 1
    ----------
    >>> dic = {
        "a.a": 1,
        "b.a": 2,
        "b.b": 3,
        "c": 4,
    }
    >>> unflat_dict_of_dict(dic)
    ... {"a": {"a": 1}, "b": {"a": 2, "b": 3}, "c": 4}
    """
    output = {}
    for k, v in dic.items():
        if sep not in k:
            output[k] = v
        else:
            idx = k.index(sep)
            k, kk = k[:idx], k[idx + 1 :]
            if k not in output:
                output[k] = {}
            elif not isinstance(output[k], Mapping):
                msg = f"Invalid dict argument. (found keys {k} and {k}{sep}{kk})"
                raise ValueError(msg)

            output[k][kk] = v

    output = {
        k: (unflat_dict_of_dict(v) if isinstance(v, Mapping) else v)
        for k, v in output.items()
    }
    return output


def unflat_list_of_list(
    flatten_lst: Sequence[T],
    sizes: Iterable[int],
) -> List[List[T]]:
    """Unflat a list to a list of sublists of given sizes."""
    lst = []
    start = 0
    stop = 0
    for count in sizes:
        stop += count
        lst.append(flatten_lst[start:stop])
        start = stop
    return lst


def union_dicts(dicts: Iterable[Dict[K, V]]) -> Dict[K, V]:
    """Performs union of dictionaries."""
    if Version.python() >= Version("3.9.0"):
        return reduce_or(*dicts)

    it = iter(dicts)
    try:
        dic0 = next(it)
    except StopIteration:
        return {}
    for dic in it:
        dic0.update(dic)
    return dic0


def union_lists(lst_of_lst: Iterable[Iterable[K]]) -> List[K]:
    """Performs union of elements in lists (like set union), but keep their original order."""
    out = {}
    for lst_i in lst_of_lst:
        out.update(dict.fromkeys(lst_i))
    out = list(out)
    return out


@overload
def unzip(lst: Iterable[Tuple[()]]) -> Tuple[()]: ...


@overload
def unzip(lst: Iterable[Tuple[T]]) -> Tuple[List[T]]: ...


@overload
def unzip(lst: Iterable[Tuple[T, U]]) -> Tuple[List[T], List[U]]: ...


@overload
def unzip(lst: Iterable[Tuple[T, U, V]]) -> Tuple[List[T], List[U], List[V]]: ...


@overload
def unzip(
    lst: Iterable[Tuple[T, U, V, W]],
) -> Tuple[List[T], List[U], List[V], List[W]]: ...


@overload
def unzip(
    lst: Iterable[Tuple[T, U, V, W, X]],
) -> Tuple[List[T], List[U], List[V], List[W], List[X]]: ...


@overload
def unzip(
    lst: Iterable[Tuple[T, ...]],
) -> Tuple[List[T], ...]: ...


def unzip(lst):
    """Invert function of builtin zip().

    Example
    -------
    >>> lst1 = [1, 2, 3, 4]
    >>> lst2 = [5, 6, 7, 8]
    >>> zipped_list = list(zip(lst1, lst2))
    >>> zipped_list
    ... [(1, 5), (2, 6), (3, 7), (4, 8)]
    >>> unzip(zipped_list)
    ... [1, 2, 3, 4], [5, 6, 7, 8]
    """
    return tuple(map(list, zip(*lst)))


def duplicate_list(lst: List[T], sizes: List[int]) -> List[T]:
    """Duplicate elements elements of a list with the corresponding sizes.

    Example
    -------
    >>> lst = ["a", "b", "c", "d", "e"]
    >>> sizes = [1, 0, 2, 1, 3]
    >>> duplicate_list(lst, sizes)
    ... ["a", "c", "c", "d", "e", "e", "e"]
    """
    if len(lst) != len(sizes):
        msg = f"Invalid arguments lengths. (found {len(lst)=} != {len(sizes)=})"
        raise ValueError(msg)

    out_size = sum(sizes)
    out: List[T] = [None for _ in range(out_size)]  # type: ignore
    curidx = 0
    for size, elt in zip(sizes, lst):
        out[curidx : curidx + size] = [elt] * size
        curidx += size
    return out
