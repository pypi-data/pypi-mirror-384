from enum import IntEnum, StrEnum
from typing import List, Optional, Sequence, TypeVar


# Integer Enum
IntegerEnumT = TypeVar("IntegerEnumT", bound=IntEnum)

OptionalIntegerEnum = Optional[IntEnum]
OptionalIntegerEnumT = TypeVar("OptionalIntegerEnumT", bound=OptionalIntegerEnum)

ListOfIntegerEnums = List[IntEnum]
ListOfIntegerEnumsT = TypeVar("ListOfIntegerEnumsT", bound=ListOfIntegerEnums)

OptionalListOfIntegerEnums = Optional[ListOfIntegerEnums]
OptionalListOfIntegerEnumsT = TypeVar(
    "OptionalListOfIntegerEnumsT", bound=OptionalListOfIntegerEnums
)

SequenceOfIntegerEnums = Sequence[IntEnum]
SequenceOfIntegerEnumsT = TypeVar(
    "SequenceOfIntegerEnumsT", bound=SequenceOfIntegerEnums
)

OptionalSequenceOfIntegerEnums = Optional[SequenceOfIntegerEnums]
OptionalSequenceOfIntegerEnumsT = TypeVar(
    "OptionalSequenceOfIntegerEnumsT", bound=OptionalSequenceOfIntegerEnums
)

# String Enum
StringEnumT = TypeVar("StringEnumT", bound=StrEnum)

OptionalStringEnum = Optional[StrEnum]
OptionalStringEnumT = TypeVar("OptionalStringEnumT", bound=OptionalStringEnum)

ListOfStringEnums = List[StrEnum]
ListOfStringEnumsT = TypeVar("ListOfStringEnumsT", bound=ListOfStringEnums)

OptionalListOfStringEnums = Optional[ListOfStringEnums]
OptionalListOfStringEnumsT = TypeVar(
    "OptionalListOfStringEnumsT", bound=OptionalListOfStringEnums
)

SequenceOfStringEnums = Sequence[StrEnum]
SequenceOfStringEnumsT = TypeVar("SequenceOfStringEnumsT", bound=SequenceOfStringEnums)

OptionalSequenceOfStringEnums = Optional[SequenceOfStringEnums]
OptionalSequenceOfStringEnumsT = TypeVar(
    "OptionalSequenceOfStringEnumsT", bound=OptionalSequenceOfStringEnums
)
