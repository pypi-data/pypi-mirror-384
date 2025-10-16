from typing import Literal, List, Optional, Sequence, TypeVar


LiteralFalse = Literal[False]
LiteralTrue = Literal[True]

BooleanT = TypeVar("BooleanT", bound=bool)

OptionalBoolean = Optional[bool]
OptionalBooleanT = TypeVar("OptionalBooleanT", bound=OptionalBoolean)

ListOfBooleans = List[bool]
ListOfBooleansT = TypeVar("ListOfBooleansT", bound=ListOfBooleans)

OptionalListOfBooleans = Optional[ListOfBooleans]
OptionalListOfBooleansT = TypeVar(
    "OptionalListOfBooleansT", bound=OptionalListOfBooleans
)

SequenceOfBooleans = Sequence[bool]
SequenceOfBooleansT = TypeVar("SequenceOfBooleansT", bound=SequenceOfBooleans)

OptionalSequenceOfBooleans = Optional[SequenceOfBooleans]
OptionalSequenceOfBooleansT = TypeVar(
    "OptionalSequenceOfBooleansT", bound=OptionalSequenceOfBooleans
)
