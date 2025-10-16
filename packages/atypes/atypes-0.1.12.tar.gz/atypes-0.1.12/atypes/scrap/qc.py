"""
Types used in qc
"""
from typing import Sequence, Union, Any, Iterable, Callable
from numbers import Number

PlcSample = Union[Number, str]
Sample = Number
Waveform = Sequence[Sample]
Plc = Sequence[PlcSample]
Chunk = Waveform  # TODO: How to express "fixed size"
ChkStat = Number
ChkStatFunc = Callable[[Chunk], Number]
Segment = Waveform  # + fixed size
Segments = Iterable[Segment]

# Consider ChunkFilterFunc (and using FilterFunc to indicated funcs used in filter(filter_func, ...)
BoolChunkFunc = Callable[[Chunk], bool]

# Series = Sequence[Union[int, float, complex, np.number, str]]
SeriesElement = Any
Series = Iterable[
    SeriesElement
]  # TODO: How to express that the type of elements should be fixed

SignalInputElement = Any
Signal = Iterable[SignalInputElement]

BoolFilterOutput = Iterable[bool]
