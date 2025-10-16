"""Module to compare type annotations"""

import typing
from typing import List, Dict, Iterable, Callable, Union, Tuple
from typing import _remove_dups_flatten

builtins = [int, float, str, bool]


def safe_issubclass(klass1, klass2):
    try:
        result = issubclass(klass1, klass2)
    except TypeError:
        result = False
    return result


def compatible_unions(union1, union2):
    args1 = typing.get_args(union1)
    args1 = _remove_dups_flatten(args1)

    args2 = typing.get_args(union2)
    args2 = _remove_dups_flatten(args2)

    for arg1 in args1:

        compats = [has_compatible_type(arg1, arg2) for arg2 in args2]
        if not any(compats):
            return False
    return True


def compatible_tuples(tuple1, tuple2):
    args1 = typing.get_args(tuple1)
    args2 = typing.get_args(tuple2)

    return all([has_compatible_type(arg1, arg2) for arg1, arg2 in zip(args1, args2)])


def compatible_callables(callable1, callable2):
    return True


def has_compatible_type(typing_inst1, typing_inst2):
    # types are compatible if equal
    if typing_inst1 == typing_inst2:
        return True

    # treat the builtins separately
    if typing_inst1 == int and typing_inst2 == float:
        return True

    # both types are classes
    if safe_issubclass(typing_inst1, typing_inst2):
        return True

    if (
        typing_inst1 in builtins
        and typing_inst2 in builtins
        and typing_inst1 != typing_inst2
    ):
        return False

    # split into root and leaves
    origin1, args1 = typing.get_origin(typing_inst1), typing.get_args(typing_inst1)
    origin2, args2 = typing.get_origin(typing_inst2), typing.get_args(typing_inst2)

    if origin1 == Union and origin2 == Union:
        return compatible_unions(typing_inst1, typing_inst2)

    if origin1 == Callable and origin2 == Callable:
        return True

    if origin1 == Tuple and origin2 == Tuple:
        return compatible_tuples(args1, args2)
    # roots must be compatible
    origin_comp = has_compatible_type(origin1, origin2)

    # args in the leaves must have equal numbers
    len_comp = len(args1) == len(args2)

    # corresponding args must be compatible
    args_comp = all(
        [has_compatible_type(arg1, arg2) for arg1, arg2 in zip(args1, args2)]
    )

    return origin_comp and len_comp and args_comp


if __name__ == '__main__':
    t1 = Union[int, float]
    t2 = Union[str, bool]
    t3 = Union[float, str]
    assert has_compatible_type(t1, t3)
