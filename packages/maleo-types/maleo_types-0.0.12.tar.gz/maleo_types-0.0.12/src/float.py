from typing import List, Sequence, Tuple, TypeVar


FloatT = TypeVar("FloatT", bound=float)

OptFloat = float | None
OptFloatT = TypeVar("OptFloatT", bound=OptFloat)

ListOfFloats = List[float]
ListOfFloatsT = TypeVar("ListOfFloatsT", bound=ListOfFloats)

OptListOfFloats = ListOfFloats | None
OptListOfFloatsT = TypeVar("OptListOfFloatsT", bound=OptListOfFloats)

SeqOfFloats = Sequence[float]
SeqOfFloatsT = TypeVar("SeqOfFloatsT", bound=SeqOfFloats)

OptSeqOfFloats = SeqOfFloats | None
OptSeqOfFloatsT = TypeVar("OptSeqOfFloatsT", bound=OptSeqOfFloats)

# Floats Tuple
DoubleFloats = Tuple[float, float]
ListOfDoubleFloats = list[DoubleFloats]
SeqOfDoubleFloats = Sequence[DoubleFloats]

TripleFloats = Tuple[float, float, float]
ListOfTripleFloats = list[TripleFloats]
SeqOfTripleFloats = Sequence[TripleFloats]

QuadrupleFloats = Tuple[float, float, float, float]
ListOfQuadrupleFloats = list[QuadrupleFloats]
SeqOfQuadrupleFloats = Sequence[QuadrupleFloats]

ManyFloats = Tuple[float, ...]
ListOfManyFloats = list[ManyFloats]
SeqOfManyFloats = Sequence[ManyFloats]

# Opt Floats Tuple
DoubleOptFloats = Tuple[OptFloat, OptFloat]
ListOfDoubleOptFloats = list[DoubleOptFloats]
SeqOfDoubleOptFloats = Sequence[DoubleOptFloats]

TripleOptFloats = Tuple[OptFloat, OptFloat, OptFloat]
ListOfTripleOptFloats = list[TripleOptFloats]
SeqOfTripleOptFloats = Sequence[TripleOptFloats]

QuadrupleOptFloats = Tuple[OptFloat, OptFloat, OptFloat, OptFloat]
ListOfQuadrupleOptFloats = list[QuadrupleOptFloats]
SeqOfQuadrupleOptFloats = Sequence[QuadrupleOptFloats]

ManyOptFloats = Tuple[OptFloat, ...]
ListOfManyOptFloats = list[ManyOptFloats]
SeqOfManyOptFloats = Sequence[ManyOptFloats]
