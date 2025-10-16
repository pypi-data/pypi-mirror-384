"""Protocols for sound recognition"""

import typing as ty
from typing import Protocol, Any, KT, VT, runtime_checkable
from atypes.typ import Waveform, Chunk, Chunks, Feature


@runtime_checkable
class Gettable(Protocol):
    """The missing type for objects that can be fetched from.
    The contract is that we can fetch an element from ``obj`` with brackets: ``obj[k]``.
    That is, ``obj`` has a ``__getitem__`` method.

    >>> isinstance(3, Gettable)  # 3 is not Gettable (can't do 3[...])
    False

    But ``dict``, ``list``, and ``str`` are Gettable:

    >>> isinstance([1, 2, 3], Gettable)
    True
    >>> isinstance({'foo': 'bar'}, Gettable)
    True
    >>> isinstance('foo', Gettable)
    True

    Note that so are their types:
    >>> all(isinstance(c, Gettable) for c in (list, dict, str))
    True

    """

    def __getitem__(self, k: KT) -> VT:
        pass


# TODO: Can we really distinguish non-Sliceable Gettables? Test?
class Sliceable(Protocol):
    """Can fetch an element from obj with brackets: obj[i:j]

    >>> t: Sliceable = 3  # will make linter complain
    >>> tt: Sliceable = [1, 2, 3]  # linter won't complain because a list is Gettable
    """

    def __getitem__(self, k: slice) -> Any:
        pass


# TODO: Not having the effect I want. Want linter to complain in these situations:


@ty.runtime_checkable
class WfChunker(Protocol):
    """
    Experimental. Doesn't have the desired behavior (yet).

    ```
    foo: WfChunker

    # linter (unexpectedly) DOES NOT COMPLAIN
    def foo(wf) -> int:
        return 3


    def bar(wf_chunker: WfChunker):
        return 42


    bar(wf_chunker=3)  # linter complains (wf_chunker not Callable)
    bar(wf_chunker=lambda wf: 3)  # linter complains (wf_chunker doesn't return iterable)
    bar(wf_chunker=lambda wf: [1, 2, 3])  # linter complains
    bar(wf_chunker=lambda wf: [[1, 2, 3], [4, 5]])  # linter (unexpectedly) complains
    bar(wf_chunker=lambda wf: None)  # linter (unexpectedly) DOES NOT complain


    def not_a_chunker(wf):
        return 3


    bar(wf_chunker=not_a_chunker)  # linter complains


    def chunker(wf):
        return [[1, 2, 3], [3, 4, 5]]


    bar(wf_chunker=chunker)  # linter (unexpectedly) complains


    def annotated_chunker(wf: Waveform) -> Chunks:
        return [[1, 2, 3], [3, 4, 5]]


    bar(wf_chunker=annotated_chunker)  # linter (unexpectedly) complains


    def still_not_a_chunker(wf):
        return 3


    still_not_a_chunker: WfChunker
    bar(wf_chunker=still_not_a_chunker)  # linter (unexpectedly) DOES NOT COMPLAIN


    # Try again with

    from atypes.typ import Waveform, Chunks

    WfChunker = Callable[[Waveform], Chunks]

    # There, too many cases pass

    ```
    """

    def __call__(self, wf: Waveform, *args, **kwargs) -> Chunks:
        """Transforms a waveform into an iterable of fixed sized iterables called chunks"""


@ty.runtime_checkable
class ChkFeaturizer(Protocol):
    def __call__(self, chk: Chunk, *args, **kwargs) -> Feature:
        """Transforms a waveform chk into an iterable of fixed sized iterables called chunks"""


import typing as ty
import collections.abc

# TODO: Make this work
# class SizableIterable(collections.abc.Sized, collections.abc.Iterable):
#     pass
#
#
# class SizableIterable2(ty.Protocol):
#     __len__: Callable
#     __iter__: Callable
#
#
# # return
# # [[1, 2, 3], [3, 4, 5], [5, 6, 7]]  # Iterable[SizableIterable[T]]
#
# T = ty.TypeVar('T')
#
#
# class Chunker(ty.Protocol):
#     def __call__(self, x: Iterable[T]) -> Iterable[SizableIterable[T]]:
#         ...
