from typing import List, Sequence, Tuple, TypeVar


StrT = TypeVar("StrT", bound=str)

OptStr = str | None
OptStrT = TypeVar("OptStrT", bound=OptStr)

ListOfStrs = List[str]
ListOfStrsT = TypeVar("ListOfStrsT", bound=ListOfStrs)

OptListOfStrs = ListOfStrs | None
OptListOfStrsT = TypeVar("OptListOfStrsT", bound=OptListOfStrs)

SeqOfStrs = Sequence[str]
SeqOfStrsT = TypeVar("SeqOfStrsT", bound=SeqOfStrs)

OptSeqOfStrs = SeqOfStrs | None
OptSeqOfStrsT = TypeVar("OptSeqOfStrsT", bound=OptSeqOfStrs)

# Strs Tuple
DoubleStrs = Tuple[str, str]
ListOfDoubleStrs = list[DoubleStrs]
SeqOfDoubleStrs = Sequence[DoubleStrs]

TripleStrs = Tuple[str, str, str]
ListOfTripleStrs = list[TripleStrs]
SeqOfTripleStrs = Sequence[TripleStrs]

QuadrupleStrs = Tuple[str, str, str, str]
ListOfQuadrupleStrs = list[QuadrupleStrs]
SeqOfQuadrupleStrs = Sequence[QuadrupleStrs]

ManyStrs = Tuple[str, ...]
ListOfManyStrs = list[ManyStrs]
SeqOfManyStrs = Sequence[ManyStrs]

# Opt Strs Tuple
DoubleOptStrs = Tuple[OptStr, OptStr]
ListOfDoubleOptStrs = list[DoubleOptStrs]
SeqOfDoubleOptStrs = Sequence[DoubleOptStrs]

TripleOptStrs = Tuple[OptStr, OptStr, OptStr]
ListOfTripleOptStrs = list[TripleOptStrs]
SeqOfTripleOptStrs = Sequence[TripleOptStrs]

QuadrupleOptStrs = Tuple[OptStr, OptStr, OptStr, OptStr]
ListOfQuadrupleOptStrs = list[QuadrupleOptStrs]
SeqOfQuadrupleOptStrs = Sequence[QuadrupleOptStrs]

ManyOptStrs = Tuple[OptStr, ...]
ListOfManyOptStrs = list[ManyOptStrs]
SeqOfManyOptStrs = Sequence[ManyOptStrs]
