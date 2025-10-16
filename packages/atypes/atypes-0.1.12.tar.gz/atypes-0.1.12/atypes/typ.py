"""Types and protocols"""

from typing import (
    Callable,
    Any,
    List,
    Tuple,
    Iterable,
    Sequence,
    Mapping,
    TypeVar,
    T,
    KT,
    MutableMapping,
)
from numbers import Number

# from numpy import ndarray, int16, int32, float32, float64

# Note I'm using Tuple to denote fixed sized sequences and List to denote a sliceable
#  unbounded sized iterator and tuple as a fixed size one

from atypes.util import MyType

# This would have been convenient, but pycharm doesn't see the globals created by NT!
# from functools import partial
# NT = partial(new_type, assign_to_globals=True)

# ------------------ GENERAL ------------------------------------------------------------

Factory = Callable[..., T]
Factory.__doc__ = 'A function that makes objects of a specific kind'

Store = Mapping[Any, T]
Store.__doc__ = 'A mapping-interface to a store (usually persistent) of data'

WritableStore = MutableMapping[Any, T]
WritableStore.__doc__ = (
    'A (mutuable-)mapping-interface to a store of data that allows writing to it'
)
# ------------------ ML -----------------------------------------------------------------


Feature = MyType(
    'Feature',
    Number,  # if categorical needs to be cast to number (as sklearn obliges)
    doc='A number that represents a characteristic of something. '
    'Usually appears as an item of an FV (a sequence of Features)',
)
# FV = FixedSizeSeq[Feature]

FV = MyType(
    'FV',
    Sequence[Feature],
    doc='Feature Vector. The informational fingerprint of something.',
)
FVs = MyType('FVs', Iterable[FV], aka=['fvs'], doc='An iterable of FVs')

Featurizer = MyType(
    'Featurizer',
    Callable[[Any], FV],
    doc='A function that makes FVs (out of Chunks, other FVs, or anything really. '
    '(This is a declaration that the output will be FVs, not what the input should be.)',
)

# from typing import Protocol
#
#
# Data = Any
#
# ModelFunc = Callable
# Learner = Any
# Fitter = Callable[[Learner, Data, ...], ModelFunc]
#
# Xtype = TypeVar('Xtype')
# Ytype = TypeVar('Ytype')
#
# # SupervisedFitter = Callable[[Xtype, Ytype, ...], Callable[[Xtype], Ytype]]
# # didn't work, so:
# class SupervisedFitter(Protocol):
#     """Describes a supervised fitting function that takes some (X, y) pair of
#     iterables and returns a callable that takes an X and returns a y.
#     The X is meant to describe an array of feature vectors and y a corresponding
#     array of values associated with each vector.
#     A supervised fitter takes a (X, y) pair and returns a function whose role it is
#     to take X inputs and return estimations/predictions of what y would be.
#     """
#
#     def __call__(
#         # note, using double underscores here to indicate that the name of the
#         # argument shouldn't matter
#         # See: https://mypy.readthedocs.io/en/stable/protocols.html#callback-protocols
#         self, __X: Xtype, __y: Ytype, *args, **kwargs
#     ) -> Callable[[Xtype], Ytype]:
#         pass


# SupervisedFitter = Callable[[FVs, Iterable[TargetType]], ModelFunc]
# Fitter = Callable[[Learner, Data, ...], ModelFunc]

# SupervisedData = Tuple[Fv]


# ------------------ SIGNAL ML ----------------------------------------------------------
FiltFunc = MyType(
    'FiltFunc',
    Callable[[Any], bool],
    doc='boolean function usually used to filter iterables',
    aka={'filt', 'filt_func'},
)
# TODO: how do we express the fixed size-ness?
FixedSizeSeq = MyType('FixedSizeSeq', Sequence)

VarSizeSeq = MyType('VarSizeSeq', List)

Key = MyType('Key', Any, doc='Any object used to reference another', aka={'key', 'k'})

# Waveform = Iterable[Union[float, int]]
Sample = MyType('Sample', Number, doc='The numerical value of a digital signal sample',)

# TODO: How do we use the waveform? Several modes. Sometimes only iterable is needed.
#  Sometimes iterable and sliceable. Sometimes length. But never reversable. So Sequence too strong.
# Waveform = MyType('Waveform', VarSizeSeq[Sample])
Waveform = MyType('Waveform', Sequence[Sample])
Waveforms = Iterable[Waveform]

# WfGen = MyType('WfGen', Iterable[Waveform], doc='A iterable of Waveforms')
KeyWfGen = MyType(
    'KeyWfGen',
    Iterable[Tuple[Key, Waveform]],
    doc='A iterable of (Key, Waveform) pairs',
)

# Chunk = MyType('Chunk', FixedSizeSeq[Sample])
Chunk = MyType('Chunk', Sequence[Sample], aka=['chk'])
Chunks = MyType('Chunks', Iterable[Chunk], aka=['chunks', 'chks'])
Chunker = MyType(
    'Chunker',
    Callable[[Waveform], Iterable[Chunk]],
    aka=['chunker', 'wf_to_chks'],
    doc='A callable that generates Chunks from a Waveform',
)

ChkFeaturizer = MyType(
    'ChkFeaturizer',
    Callable[[Chunk], FV],
    aka=['featurizer', 'chk_to_fv'],
    doc='A function that makes FVs specifically from Chunks.',
)

Segment = MyType(
    'Segment',
    Sequence[Sample],
    aka='segment',
    doc='Data regarding an interval of time. This is often just a piece of waveform, '
    'but could also be a bundle of several waveforms and other signals/datas that '
    'happened in that interval of time.',
)
Segments = MyType(
    'Segments', Iterable[Segment], aka='segments', doc='An iterable of segments',
)

TimeIndex = MyType(
    'TimeIndex',
    Number,
    doc='A number indexing time. Could be in an actual time unit, or could just be '
    'an enumerator (i.e. "ordinal time")',
)
BT = MyType(
    'BT',
    TimeIndex,
    doc='TimeIndex for the lower bound of an interval of time. '
    'Stands for "Bottom Time". By convention, a BT is inclusive.',
)
TT = MyType(
    'TT',
    TimeIndex,
    doc='TimeIndex for the upper bound of an interval of time. '
    'Stands for "Upper Time". By convention, a TT is exclusive.',
)
IntervalTuple = MyType(
    'IntervalTuple',
    Tuple[BT, TT],
    doc='Denotes an interval of time by specifying the (BT, TT) pair',
)
IntervalSlice = MyType(
    'IntervalSlice',
    slice,  # Note: extra condition: non-None .start and .end, and no .step
    doc='Denotes an interval of time by specifying the (BT, TT) pair',
)

# Note: Like a segment in that it hold data from an interval of time, but there's no
#  constraints on the data items format.
# Name options: piece, part, section, portion, fragment, wedge, slab, hunk

TimeIndexedItem = MyType(
    'TimeIndexedItem', Any, doc='Data that is (implicitly or explicitly) time-indexed.'
)
Slab = MyType(
    'Slab',
    Iterable[TimeIndexedItem],  # extra condition: all items within a same interval
    doc='A collection of (time-indexed) items of a same interval of time.',
)
Hunk = MyType(
    'Hunk',
    Slab,  # extra condition over Slab: Fixed size interval
    doc='A slab of items for an interval coming from a fixed-size segmentation of time. '
    '(A slab: A collection of (time-indexed) items of a same interval of time.)',
)

WaveformBytes = MyType('WaveformBytes', bytes)

# --------------- STORES ----------------------------------------------------------------

# WfStore = StoreType[Waveform]

WfStore = MyType(
    'WfStore',
    Store[Waveform],
    aka=['wf_store', 'wfs', 'audio_store'],
    doc='A waveform store. More precisely, a key-value (Mapping) interface to waveforms',
)

# --------------- SLANG TYPES -----------------------------------------------------------

# ChkFeaturizer
# Note: Snips are ints, but with an upper limit... From an "alphabet",
#  so akin to a very big Enum in a sense.
Snip = MyType(
    'Snip',
    int,
    aka=['snip'],
    doc='The smallest element of a signal language. '
    'Technically, an index representing a region of a feature space partition.',
)
Snips = MyType(
    'Snips',
    Iterable[Snip],
    aka=['snips'],
    doc='A sequence or stream whose elements are Snips',
)

Quantizer = MyType(
    'Quantizer',
    Callable[[Any], Snip],
    aka=['quantizer', 'fv_to_snip'],
    doc='The function that computes a Snip out of an FV.',
)

Snipper = MyType(
    'Snipper',
    Callable[[Waveform], Snips],
    aka=['snipper'],
    doc='The function that gets you from a stream of samples (Waveform) to '
    'a stream of snips (Snips)',
)

# --------------- STORES ---------------------------------------------------------------------------
