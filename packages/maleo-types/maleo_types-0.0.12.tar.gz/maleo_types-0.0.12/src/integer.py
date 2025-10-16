from typing import List, Sequence, Tuple, TypeVar


IntT = TypeVar("IntT", bound=int)

OptInt = int | None
OptIntT = TypeVar("OptIntT", bound=OptInt)

ListOfInts = List[int]
ListOfIntsT = TypeVar("ListOfIntsT", bound=ListOfInts)

OptListOfInts = ListOfInts | None
OptListOfIntsT = TypeVar("OptListOfIntsT", bound=OptListOfInts)

SeqOfInts = Sequence[int]
SeqOfIntsT = TypeVar("SeqOfIntsT", bound=SeqOfInts)

OptSeqOfInts = SeqOfInts | None
OptSeqOfIntsT = TypeVar("OptSeqOfIntsT", bound=OptSeqOfInts)

# Ints Tuple
DoubleInts = Tuple[int, int]
ListOfDoubleInts = list[DoubleInts]
SeqOfDoubleInts = Sequence[DoubleInts]

TripleInts = Tuple[int, int, int]
ListOfTripleInts = list[TripleInts]
SeqOfTripleInts = Sequence[TripleInts]

QuadrupleInts = Tuple[int, int, int, int]
ListOfQuadrupleInts = list[QuadrupleInts]
SeqOfQuadrupleInts = Sequence[QuadrupleInts]

ManyInts = Tuple[int, ...]
ListOfManyInts = list[ManyInts]
SeqOfManyInts = Sequence[ManyInts]

# Opt Ints Tuple
DoubleOptInts = Tuple[OptInt, OptInt]
ListOfDoubleOptInts = list[DoubleOptInts]
SeqOfDoubleOptInts = Sequence[DoubleOptInts]

TripleOptInts = Tuple[OptInt, OptInt, OptInt]
ListOfTripleOptInts = list[TripleOptInts]
SeqOfTripleOptInts = Sequence[TripleOptInts]

QuadrupleOptInts = Tuple[OptInt, OptInt, OptInt, OptInt]
ListOfQuadrupleOptInts = list[QuadrupleOptInts]
SeqOfQuadrupleOptInts = Sequence[QuadrupleOptInts]

ManyOptInts = Tuple[OptInt, ...]
ListOfManyOptInts = list[ManyOptInts]
SeqOfManyOptInts = Sequence[ManyOptInts]
