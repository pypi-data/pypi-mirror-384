from typing import Sequence, Tuple, TypeVar


FloatT = TypeVar("FloatT", bound=float)

OptFloat = float | None
OptFloatT = TypeVar("OptFloatT", bound=OptFloat)

ListOfFloats = list[float]
ListOfFloatsT = TypeVar("ListOfFloatsT", bound=ListOfFloats)

OptListOfFloats = ListOfFloats | None
OptListOfFloatsT = TypeVar("OptListOfFloatsT", bound=OptListOfFloats)

SeqOfFloats = Sequence[float]
SeqOfFloatsT = TypeVar("SeqOfFloatsT", bound=SeqOfFloats)

OptSeqOfFloats = SeqOfFloats | None
OptSeqOfFloatsT = TypeVar("OptSeqOfFloatsT", bound=OptSeqOfFloats)

# Floats Tuple
DoubleFloats = Tuple[float, float]
OptDoubleFloats = DoubleFloats | None
ListOfDoubleFloats = list[DoubleFloats]
OptListOfDoubleFloats = ListOfDoubleFloats | None
SeqOfDoubleFloats = Sequence[DoubleFloats]
OptSeqOfDoubleFloats = SeqOfDoubleFloats | None

TripleFloats = Tuple[float, float, float]
OptTripleFloats = TripleFloats | None
ListOfTripleFloats = list[TripleFloats]
OptListOfTripleFloats = ListOfTripleFloats | None
SeqOfTripleFloats = Sequence[TripleFloats]
OptSeqOfTripleFloats = SeqOfTripleFloats | None

QuadrupleFloats = Tuple[float, float, float, float]
OptQuadrupleFloats = QuadrupleFloats | None
ListOfQuadrupleFloats = list[QuadrupleFloats]
OptListOfQuadrupleFloats = ListOfQuadrupleFloats | None
SeqOfQuadrupleFloats = Sequence[QuadrupleFloats]
OptSeqOfQuadrupleFloats = SeqOfQuadrupleFloats | None

QuintupleFloats = Tuple[float, float, float, float, float]
OptQuintupleFloats = QuintupleFloats | None
ListOfQuintupleFloats = list[QuintupleFloats]
OptListOfQuintupleFloats = ListOfQuintupleFloats | None
SeqOfQuintupleFloats = Sequence[QuintupleFloats]
OptSeqOfQuintupleFloats = SeqOfQuintupleFloats | None

ManyFloats = Tuple[float, ...]
OptManyFloats = ManyFloats | None
ListOfManyFloats = list[ManyFloats]
OptListOfManyFloats = ListOfManyFloats | None
SeqOfManyFloats = Sequence[ManyFloats]
OptSeqOfManyFloats = SeqOfManyFloats | None

# Opt Floats Tuple
DoubleOptFloats = Tuple[OptFloat, OptFloat]
OptDoubleOptFloats = DoubleOptFloats | None
ListOfDoubleOptFloats = list[DoubleOptFloats]
OptListOfDoubleOptFloats = ListOfDoubleOptFloats | None
SeqOfDoubleOptFloats = Sequence[DoubleOptFloats]
OptSeqOfDoubleOptFloats = SeqOfDoubleOptFloats | None

TripleOptFloats = Tuple[OptFloat, OptFloat, OptFloat]
OptTripleOptFloats = TripleOptFloats | None
ListOfTripleOptFloats = list[TripleOptFloats]
OptListOfTripleOptFloats = ListOfTripleOptFloats | None
SeqOfTripleOptFloats = Sequence[TripleOptFloats]
OptSeqOfTripleOptFloats = SeqOfTripleOptFloats | None

QuadrupleOptFloats = Tuple[OptFloat, OptFloat, OptFloat, OptFloat]
OptQuadrupleOptFloats = QuadrupleOptFloats | None
ListOfQuadrupleOptFloats = list[QuadrupleOptFloats]
OptListOfQuadrupleOptFloats = ListOfQuadrupleOptFloats | None
SeqOfQuadrupleOptFloats = Sequence[QuadrupleOptFloats]
OptSeqOfQuadrupleOptFloats = SeqOfQuadrupleOptFloats | None

QuintupleOptFloats = Tuple[OptFloat, OptFloat, OptFloat, OptFloat, OptFloat]
OptQuintupleOptFloats = QuintupleOptFloats | None
ListOfQuintupleOptFloats = list[QuintupleOptFloats]
OptListOfQuintupleOptFloats = ListOfQuintupleOptFloats | None
SeqOfQuintupleOptFloats = Sequence[QuintupleOptFloats]
OptSeqOfQuintupleOptFloats = SeqOfQuintupleOptFloats | None

ManyOptFloats = Tuple[OptFloat, ...]
OptManyOptFloats = ManyOptFloats | None
ListOfManyOptFloats = list[ManyOptFloats]
OptListOfManyOptFloats = ListOfManyOptFloats | None
SeqOfManyOptFloats = Sequence[ManyOptFloats]
OptSeqOfManyOptFloats = SeqOfManyOptFloats | None
