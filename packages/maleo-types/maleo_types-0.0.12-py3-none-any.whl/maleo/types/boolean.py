from typing import Literal, Sequence, TypeVar


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
