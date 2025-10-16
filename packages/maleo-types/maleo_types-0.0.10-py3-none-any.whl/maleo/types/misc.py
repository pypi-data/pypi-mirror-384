from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Optional, Union, TypeVar
from uuid import UUID
from .any import ListOfAny, SequenceOfAny
from .dict import StringToAnyDict
from .enum import ListOfStringEnums, OptionalStringEnum, OptionalListOfStringEnums
from .integer import (
    ListOfIntegers,
    OptionalInteger,
    OptionalListOfIntegers,
    SequenceOfIntegers,
)
from .mapping import StringToAnyMapping
from .string import ListOfStrings, OptionalListOfStrings
from .uuid import ListOfUUIDs, OptionalUUID, OptionalListOfUUIDs, SequenceOfUUIDs


BytesOrMemoryview = Union[bytes, memoryview]
OptionalBytesOrMemoryview = Optional[BytesOrMemoryview]

BytesOrString = Union[bytes, str]
BytesOrStringT = TypeVar("BytesOrStringT", bound=BytesOrString)
OptionalBytesOrString = Optional[BytesOrString]
OptionalBytesOrStringT = TypeVar("OptionalBytesOrStringT", bound=OptionalBytesOrString)

FloatOrInteger = Union[float, int]
FloatOrIntegerT = TypeVar("FloatOrIntegerT", bound=FloatOrInteger)
OptionalFloatOrInteger = Optional[FloatOrInteger]
OptionalFloatOrIntegerT = TypeVar(
    "OptionalFloatOrIntegerT", bound=OptionalFloatOrInteger
)

IntegerOrString = Union[int, str]
IntegerOrStringT = TypeVar("IntegerOrStringT", bound=IntegerOrString)
OptionalIntegerOrString = Optional[IntegerOrString]
OptionalIntegerOrStringT = TypeVar(
    "OptionalIntegerOrStringT", bound=OptionalIntegerOrString
)

IntegerOrStringEnum = Union[int, StrEnum]
IntegerOrStringEnumT = TypeVar("IntegerOrStringEnumT", bound=IntegerOrStringEnum)
OptionalIntegerOrOptionalStringEnum = Union[OptionalInteger, OptionalStringEnum]
OptionalIntegerOrOptionalStringEnumT = TypeVar(
    "OptionalIntegerOrOptionalStringEnumT", bound=OptionalIntegerOrOptionalStringEnum
)

IntegerOrUUID = Union[int, UUID]
IntegerOrUUIDT = TypeVar("IntegerOrUUIDT", bound=IntegerOrUUID)
OptionalIntegerOrOptionalUUID = Union[OptionalInteger, OptionalUUID]
OptionalIntegerOrOptionalUUIDT = TypeVar(
    "OptionalIntegerOrOptionalUUIDT", bound=OptionalIntegerOrOptionalUUID
)
OptionalIntegerOrUUID = Optional[IntegerOrUUID]
OptionalIntegerOrUUIDT = TypeVar("OptionalIntegerOrUUIDT", bound=OptionalIntegerOrUUID)

IntegersOrUUIDs = Union[ListOfIntegers, ListOfUUIDs]
IntegersOrUUIDsT = TypeVar("IntegersOrUUIDsT", bound=IntegersOrUUIDs)

OptionalIntegersOrOptionalUUIDs = Union[OptionalListOfIntegers, OptionalListOfUUIDs]
OptionalIntegersOrOptionalUUIDsT = TypeVar(
    "OptionalIntegersOrOptionalUUIDsT", bound=OptionalIntegersOrOptionalUUIDs
)

ListOfIntegersOrUUIDs = Union[ListOfIntegers, ListOfUUIDs]
ListOfIntegersOrUUIDsT = TypeVar("ListOfIntegersOrUUIDsT", bound=ListOfIntegersOrUUIDs)
OptionalListOfIntegersOrUUIDs = Optional[ListOfIntegersOrUUIDs]
OptionalListOfIntegersOrUUIDsT = TypeVar(
    "OptionalListOfIntegersOrUUIDsT", bound=OptionalListOfIntegersOrUUIDs
)

SequenceOfIntegersOrUUIDs = Union[SequenceOfIntegers, SequenceOfUUIDs]
SequenceOfIntegersOrUUIDsT = TypeVar(
    "SequenceOfIntegersOrUUIDsT", bound=SequenceOfIntegersOrUUIDs
)
OptionalSequenceOfIntegersOrUUIDs = Optional[SequenceOfIntegersOrUUIDs]
OptionalSequenceOfIntegersOrUUIDsT = TypeVar(
    "OptionalSequenceOfIntegersOrUUIDsT", bound=OptionalSequenceOfIntegersOrUUIDs
)

PathOrString = Union[Path, str]
OptionalPathOrString = Optional[PathOrString]

IntegerOrIntegerEnum = Union[int, IntEnum]
IntegerOrIntegerEnumT = TypeVar("IntegerOrIntegerEnumT", bound=IntegerOrIntegerEnum)
OptionalIntegerOrIntegerEnum = Optional[IntegerOrIntegerEnum]
OptionalIntegerOrIntegerEnumT = TypeVar(
    "OptionalIntegerOrIntegerEnumT", bound=OptionalIntegerOrIntegerEnum
)

StringOrStringEnum = Union[str, StrEnum]
StringOrStringEnumT = TypeVar("StringOrStringEnumT", bound=StringOrStringEnum)
OptionalStringOrStringEnum = Optional[StringOrStringEnum]
OptionalStringOrStringEnumT = TypeVar(
    "OptionalStringOrStringEnumT", bound=OptionalStringOrStringEnum
)

StringsOrStringEnums = Union[ListOfStrings, ListOfStringEnums]
StringsOrStringEnumsT = TypeVar("StringsOrStringEnumsT", bound=StringsOrStringEnums)
OptionalStringsOrOptionalStringEnums = Union[
    OptionalListOfStrings, OptionalListOfStringEnums
]
OptionalStringsOrOptionalStringEnumsT = TypeVar(
    "OptionalStringsOrOptionalStringEnumsT", bound=OptionalStringsOrOptionalStringEnums
)

ListOfAnyOrStringToAnyDict = Union[ListOfAny, StringToAnyDict]
OptionalListOfAnyOrStringToAnyDict = Optional[ListOfAnyOrStringToAnyDict]
SequenceOfAnyOrStringToAnyDict = Union[SequenceOfAny, StringToAnyDict]
OptionalSequenceOfAnyOrStringToAnyDict = Optional[SequenceOfAnyOrStringToAnyDict]

ListOfAnyOrStringToAnyMapping = Union[ListOfAny, StringToAnyMapping]
OptionalListOfAnyOrStringToAnyMapping = Optional[ListOfAnyOrStringToAnyMapping]
SequenceOfAnyOrStringToAnyMapping = Union[SequenceOfAny, StringToAnyMapping]
OptionalSequenceOfAnyOrStringToAnyMapping = Optional[SequenceOfAnyOrStringToAnyMapping]
