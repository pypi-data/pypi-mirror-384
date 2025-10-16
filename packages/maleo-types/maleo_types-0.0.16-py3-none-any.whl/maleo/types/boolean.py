from typing import Literal, Sequence, Tuple, TypeVar


LiteralFalse = Literal[False]
LiteralTrue = Literal[True]

BoolT = TypeVar("BoolT", bound=bool)

OptBool = bool | None
OptBoolT = TypeVar("OptBoolT", bound=OptBool)

ListOfBools = list[bool]
ListOfBoolsT = TypeVar("ListOfBoolsT", bound=ListOfBools)

OptListOfBools = ListOfBools | None
OptListOfBoolsT = TypeVar("OptListOfBoolsT", bound=OptListOfBools)

SeqOfBools = Sequence[bool]
SeqOfBoolsT = TypeVar("SeqOfBoolsT", bound=SeqOfBools)

OptSeqOfBools = SeqOfBools | None
OptSeqOfBoolsT = TypeVar("OptSeqOfBoolsT", bound=OptSeqOfBools)

# Bools Tuple
DoubleBools = Tuple[bool, bool]
OptDoubleBools = DoubleBools | None
ListOfDoubleBools = list[DoubleBools]
OptListOfDoubleBools = ListOfDoubleBools | None
SeqOfDoubleBools = Sequence[DoubleBools]
OptSeqOfDoubleBools = SeqOfDoubleBools | None

TripleBools = Tuple[bool, bool, bool]
OptTripleBools = TripleBools | None
ListOfTripleBools = list[TripleBools]
OptListOfTripleBools = ListOfTripleBools | None
SeqOfTripleBools = Sequence[TripleBools]
OptSeqOfTripleBools = SeqOfTripleBools | None

QuadrupleBools = Tuple[bool, bool, bool, bool]
OptQuadrupleBools = QuadrupleBools | None
ListOfQuadrupleBools = list[QuadrupleBools]
OptListOfQuadrupleBools = ListOfQuadrupleBools | None
SeqOfQuadrupleBools = Sequence[QuadrupleBools]
OptSeqOfQuadrupleBools = SeqOfQuadrupleBools | None

QuintupleBools = Tuple[bool, bool, bool, bool, bool]
OptQuintupleBools = QuintupleBools | None
ListOfQuintupleBools = list[QuintupleBools]
OptListOfQuintupleBools = ListOfQuintupleBools | None
SeqOfQuintupleBools = Sequence[QuintupleBools]
OptSeqOfQuintupleBools = SeqOfQuintupleBools | None

ManyBools = Tuple[bool, ...]
OptManyBools = ManyBools | None
ListOfManyBools = list[ManyBools]
OptListOfManyBools = ListOfManyBools | None
SeqOfManyBools = Sequence[ManyBools]
OptSeqOfManyBools = SeqOfManyBools | None

# Opt Bools Tuple
DoubleOptBools = Tuple[OptBool, OptBool]
OptDoubleOptBools = DoubleOptBools | None
ListOfDoubleOptBools = list[DoubleOptBools]
OptListOfDoubleOptBools = ListOfDoubleOptBools | None
SeqOfDoubleOptBools = Sequence[DoubleOptBools]
OptSeqOfDoubleOptBools = SeqOfDoubleOptBools | None

TripleOptBools = Tuple[OptBool, OptBool, OptBool]
OptTripleOptBools = TripleOptBools | None
ListOfTripleOptBools = list[TripleOptBools]
OptListOfTripleOptBools = ListOfTripleOptBools | None
SeqOfTripleOptBools = Sequence[TripleOptBools]
OptSeqOfTripleOptBools = SeqOfTripleOptBools | None

QuadrupleOptBools = Tuple[OptBool, OptBool, OptBool, OptBool]
OptQuadrupleOptBools = QuadrupleOptBools | None
ListOfQuadrupleOptBools = list[QuadrupleOptBools]
OptListOfQuadrupleOptBools = ListOfQuadrupleOptBools | None
SeqOfQuadrupleOptBools = Sequence[QuadrupleOptBools]
OptSeqOfQuadrupleOptBools = SeqOfQuadrupleOptBools | None

QuintupleOptBools = Tuple[OptBool, OptBool, OptBool, OptBool, OptBool]
OptQuintupleOptBools = QuintupleOptBools | None
ListOfQuintupleOptBools = list[QuintupleOptBools]
OptListOfQuintupleOptBools = ListOfQuintupleOptBools | None
SeqOfQuintupleOptBools = Sequence[QuintupleOptBools]
OptSeqOfQuintupleOptBools = SeqOfQuintupleOptBools | None

ManyOptBools = Tuple[OptBool, ...]
OptManyOptBools = ManyOptBools | None
ListOfManyOptBools = list[ManyOptBools]
OptListOfManyOptBools = ListOfManyOptBools | None
SeqOfManyOptBools = Sequence[ManyOptBools]
OptSeqOfManyOptBools = SeqOfManyOptBools | None
