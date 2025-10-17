from typing import Sequence, Tuple, TypeVar


IntT = TypeVar("IntT", bound=int)

OptInt = int | None
OptIntT = TypeVar("OptIntT", bound=OptInt)

ListOfInts = list[int]
ListOfIntsT = TypeVar("ListOfIntsT", bound=ListOfInts)

OptListOfInts = ListOfInts | None
OptListOfIntsT = TypeVar("OptListOfIntsT", bound=OptListOfInts)

SeqOfInts = Sequence[int]
SeqOfIntsT = TypeVar("SeqOfIntsT", bound=SeqOfInts)

OptSeqOfInts = SeqOfInts | None
OptSeqOfIntsT = TypeVar("OptSeqOfIntsT", bound=OptSeqOfInts)

# Ints Tuple
DoubleInts = Tuple[int, int]
OptDoubleInts = DoubleInts | None
ListOfDoubleInts = list[DoubleInts]
OptListOfDoubleInts = ListOfDoubleInts | None
SeqOfDoubleInts = Sequence[DoubleInts]
OptSeqOfDoubleInts = SeqOfDoubleInts | None

TripleInts = Tuple[int, int, int]
OptTripleInts = TripleInts | None
ListOfTripleInts = list[TripleInts]
OptListOfTripleInts = ListOfTripleInts | None
SeqOfTripleInts = Sequence[TripleInts]
OptSeqOfTripleInts = SeqOfTripleInts | None

QuadrupleInts = Tuple[int, int, int, int]
OptQuadrupleInts = QuadrupleInts | None
ListOfQuadrupleInts = list[QuadrupleInts]
OptListOfQuadrupleInts = ListOfQuadrupleInts | None
SeqOfQuadrupleInts = Sequence[QuadrupleInts]
OptSeqOfQuadrupleInts = SeqOfQuadrupleInts | None

QuintupleInts = Tuple[int, int, int, int, int]
OptQuintupleInts = QuintupleInts | None
ListOfQuintupleInts = list[QuintupleInts]
OptListOfQuintupleInts = ListOfQuintupleInts | None
SeqOfQuintupleInts = Sequence[QuintupleInts]
OptSeqOfQuintupleInts = SeqOfQuintupleInts | None

ManyInts = Tuple[int, ...]
OptManyInts = ManyInts | None
ListOfManyInts = list[ManyInts]
OptListOfManyInts = ListOfManyInts | None
SeqOfManyInts = Sequence[ManyInts]
OptSeqOfManyInts = SeqOfManyInts | None

# Opt Ints Tuple
DoubleOptInts = Tuple[OptInt, OptInt]
OptDoubleOptInts = DoubleOptInts | None
ListOfDoubleOptInts = list[DoubleOptInts]
OptListOfDoubleOptInts = ListOfDoubleOptInts | None
SeqOfDoubleOptInts = Sequence[DoubleOptInts]
OptSeqOfDoubleOptInts = SeqOfDoubleOptInts | None

TripleOptInts = Tuple[OptInt, OptInt, OptInt]
OptTripleOptInts = TripleOptInts | None
ListOfTripleOptInts = list[TripleOptInts]
OptListOfTripleOptInts = ListOfTripleOptInts | None
SeqOfTripleOptInts = Sequence[TripleOptInts]
OptSeqOfTripleOptInts = SeqOfTripleOptInts | None

QuadrupleOptInts = Tuple[OptInt, OptInt, OptInt, OptInt]
OptQuadrupleOptInts = QuadrupleOptInts | None
ListOfQuadrupleOptInts = list[QuadrupleOptInts]
OptListOfQuadrupleOptInts = ListOfQuadrupleOptInts | None
SeqOfQuadrupleOptInts = Sequence[QuadrupleOptInts]
OptSeqOfQuadrupleOptInts = SeqOfQuadrupleOptInts | None

QuintupleOptInts = Tuple[OptInt, OptInt, OptInt, OptInt, OptInt]
OptQuintupleOptInts = QuintupleOptInts | None
ListOfQuintupleOptInts = list[QuintupleOptInts]
OptListOfQuintupleOptInts = ListOfQuintupleOptInts | None
SeqOfQuintupleOptInts = Sequence[QuintupleOptInts]
OptSeqOfQuintupleOptInts = SeqOfQuintupleOptInts | None

ManyOptInts = Tuple[OptInt, ...]
OptManyOptInts = ManyOptInts | None
ListOfManyOptInts = list[ManyOptInts]
OptListOfManyOptInts = ListOfManyOptInts | None
SeqOfManyOptInts = Sequence[ManyOptInts]
OptSeqOfManyOptInts = SeqOfManyOptInts | None
