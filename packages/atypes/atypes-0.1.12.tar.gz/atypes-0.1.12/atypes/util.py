"""Utilities to use in atypes functionality"""

from typing import Optional, Iterable, TypeVar, Union, NewType, Any


def MyType(
    name: str,
    tp: type = Any,
    doc: Optional[str] = None,
    aka: Optional[Union[str, Iterable[str]]] = None,
    *,
    assign_to_globals=False
):
    """Like `typing.NewType` with some extras (`__doc__` and `_aka` attributes, etc.)

    See (NewType docs)[https://docs.python.org/3/library/typing.html#typing.NewType]
    for more.

    Args:
        name: Name to give the variable
        tp: Type
        doc: Optional string to put in __doc__ attribute
        aka: Optional set (or any iterable) to put in _aka attribute,
            meant to list names the variables of this type often appear as.

    Returns: None

    >>> from typing import Any, List
    >>> T = MyType('T')  # can be Anything (`Any` is the default type
    >>> Key = MyType('Key', Any, aka=['key', 'k'])

    The `aka` argument will be added to the a `._aka` attribute, which is a set
    containing names instances of the type might come as.

    >>> assert isinstance(Key._aka, set)
    >>> sorted(Key._aka)
    ['k', 'key']

    You can also add docs:

    >>> Val = MyType(
    ... 'Val',
    ... Union[int, float, List[Union[int, float]]],
    ... doc="A number or list of numbers."
    ... )
    >>> Val.__doc__
    'A number or list of numbers.'

    `MyType` is neither a type nor returns a type -- contrary to what the name would
    make you expect. We chose this name to mimic `typing.NewType` since `MyType` just
    does what `NewType` does, just a bit more.
    What is returned is really the identity function, so
    `x is NewType('Name', int)(x)` is always `True`.

    >>> type(Val)
    <class 'function'>

    """

    new_tp = NewType(name, tp)
    new_tp = _add_doc_and_aka(new_tp, doc, aka)

    if assign_to_globals:
        globals()[
            name
        ] = new_tp  # not sure how kosher this is... Should only use at top level of module, for sure!
    return new_tp


# TODO: Add
def MyVar(
    name: str,
    constraint: type = Any,
    *more_constraints,
    doc: Optional[str] = None,
    aka: Optional[Union[str, Iterable[str]]] = None,
    covariant=False,
    contravariant=False,
    assign_to_globals=False
):
    """Like `typing.TypeVar` with some extras (`__doc__` and `_aka` attributes, etc.)

    See (TypeVar docs)[https://docs.python.org/3/library/typing.html#typing.TypeVar]
    for more.

    >>> from typing import Any, List, Union
    >>> Key = MyVar('Key', Any, aka=['key', 'k'])

    The `aka` argument will be added to the a `._aka` attribute, which is a set
    containing names instances of the type might come as.

    >>> assert isinstance(Key._aka, set)
    >>> sorted(Key._aka)
    ['k', 'key']

    You can also add docs:

    >>> Val = MyVar(
    ... 'Val',
    ... int, float, List[Union[int, float]],
    ... doc="A number or list of numbers.")
    >>> Val.__doc__
    'A number or list of numbers.'

    Contrary to `MyType`, `MyVar` actually returns a type (though `MyVar` is not
    itself a type, contrary to pep8's expectations -- blame `typing.NewVar`;
    `MyVar` is just an enanced version of it).

    >>> type(Val)
    <class 'typing.TypeVar'>

    """

    if len(more_constraints) == 0:
        new_tp = TypeVar(
            name, bound=constraint, covariant=covariant, contravariant=contravariant
        )
    else:
        new_tp = TypeVar(
            name,
            constraint,
            *more_constraints,
            covariant=covariant,
            contravariant=contravariant
        )

    new_tp = _add_doc_and_aka(new_tp, doc, aka)

    if assign_to_globals:
        globals()[
            name
        ] = new_tp  # not sure how kosher this is... Should only use at top level of module, for sure!
    return new_tp


def _add_doc_and_aka(obj, doc=None, aka=None):
    """Add `doc` (as `__doc__` attr) and aka (as `_aka` attr) to obj and return obj"""
    if doc is not None:
        try:
            setattr(obj, '__doc__', doc)
        except AttributeError:  # because TypeVar attributes are read only in 3.6,
            # it seems...
            pass
    if aka is not None:
        if isinstance(aka, str):
            aka = {aka}
    else:
        aka = set()
    try:
        setattr(obj, '_aka', set(aka))
    except AttributeError:  # because TypeVar attributes are read only in 3.6,
        # it seems...
        pass
    return obj
