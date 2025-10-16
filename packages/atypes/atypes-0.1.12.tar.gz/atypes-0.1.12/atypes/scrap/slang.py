"""
Types for sound recognition.
"""
from typing import Callable, Union, Any, List, Tuple, Iterable, Sequence
from numbers import Number

# from numpy import ndarray, int16, int32, float32, float64

# Note I'm using Tuple to denote fixed sized sequences and List to denote a sliceable
#  unbounded sized iterator and
# tuple as a fixed

from atypes.util import MyType

# This would have been convenient, but pycharm doesn't see the globals created by NT!
# from functools import partial
# NT = partial(new_type, assign_to_globals=True)


FixedSizeSeq = MyType('FixedSizeSeq', Tuple, List)

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
    doc='The component that generates Chunks from a Waveform',
)

Feature = MyType(
    'Feature',
    Number,
    doc='A number that represents a characteristic of something. '
    'Usually appears as an item of an FV (a sequence of Features)',
)
# FV = FixedSizeSeq[Feature]

FV = MyType(
    'FV',
    Sequence[Feature],
    doc='Feature Vector. The informational fingerprint of something.',
)
FVs = MyType('FVs', Iterable[FV], aka=['fvs'])
Featurizer = MyType(
    'Featurizer',
    Callable[[Any], FV],
    doc='A function that makes FVs (out of Chunks, other FVs, or anything really. '
    '(This is a declaration that the output will be FVs, not what the input should be.)',
)
ChkFeaturizer = MyType(
    'ChkFeaturizer',
    Callable[[Chunk], FV],
    aka=['featurizer', 'chk_to_fv'],
    doc='A function that makes FVs specifically from Chunks.',
)
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
