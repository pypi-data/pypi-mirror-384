from enum import IntEnum, StrEnum
from pathlib import Path
from typing import TypeVar
from uuid import UUID
from .any import ListOfAny, SeqOfAny
from .dict import StrToAnyDict
from .enum import ListOfIntEnums, SeqOfIntEnums, ListOfStrEnums, SeqOfStrEnums
from .float import ListOfFloats, SeqOfFloats
from .integer import ListOfInts, SeqOfInts
from .mapping import StrToAnyMapping
from .string import ListOfStrs, SeqOfStrs
from .uuid import ListOfUUIDs, SeqOfUUIDs


# Bytes x Memoryview
BytesOrMemoryview = bytes | memoryview
OptBytesOrMemoryview = BytesOrMemoryview | None


# Path x Str
PathOrStr = Path | str
OptPathOrStr = PathOrStr | None


# Bytes x Str
BytesOrStr = bytes | str
BytesOrStrT = TypeVar("BytesOrStrT", bound=BytesOrStr)

OptBytesOrStr = BytesOrStr | None
OptBytesOrStrT = TypeVar("OptBytesOrStrT", bound=OptBytesOrStr)


# Float x Int
FloatOrInt = float | int
FloatOrIntT = TypeVar("FloatOrIntT", bound=FloatOrInt)

OptFloatOrInt = FloatOrInt | None
OptFloatOrIntT = TypeVar("OptFloatOrIntT", bound=OptFloatOrInt)

ListOfFloatsOrInts = ListOfFloats | ListOfInts
ListOfFloatsOrIntsT = TypeVar("ListOfFloatsOrIntsT", bound=ListOfFloatsOrInts)

OptListOfFloatsOrInts = ListOfFloatsOrInts | None
OptListOfFloatsOrIntsT = TypeVar("OptListOfFloatsOrIntsT", bound=OptListOfFloatsOrInts)

SeqOfFloatsOrInts = SeqOfFloats | SeqOfInts
SeqOfFloatsOrIntsT = TypeVar("SeqOfFloatsOrIntsT", bound=SeqOfFloatsOrInts)

OptSeqOfFloatsOrInts = SeqOfFloatsOrInts | None
OptSeqOfFloatsOrIntsT = TypeVar("OptSeqOfFloatsOrIntsT", bound=OptSeqOfFloatsOrInts)


# Int x Str
IntOrStr = int | str
IntOrStrT = TypeVar("IntOrStrT", bound=IntOrStr)

OptIntOrStr = IntOrStr | None
OptIntOrStrT = TypeVar("OptIntOrStrT", bound=OptIntOrStr)

ListOfIntsOrStrs = ListOfInts | ListOfStrs
ListOfIntsOrStrsT = TypeVar("ListOfIntsOrStrsT", bound=ListOfIntsOrStrs)

OptListOfIntsOrStrs = ListOfIntsOrStrs | None
OptListOfIntsOrStrsT = TypeVar("OptListOfIntsOrStrsT", bound=OptListOfIntsOrStrs)

SeqOfIntsOrStrs = SeqOfInts | SeqOfStrs
SeqOfIntsOrStrsT = TypeVar("SeqOfIntsOrStrsT", bound=SeqOfIntsOrStrs)

OptSeqOfIntsOrStrs = SeqOfIntsOrStrs | None
OptSeqOfIntsOrStrsT = TypeVar("OptSeqOfIntsOrStrsT", bound=OptSeqOfIntsOrStrs)


# Int x IntEnum
IntOrIntEnum = int | IntEnum
IntOrIntEnumT = TypeVar("IntOrIntEnumT", bound=IntOrIntEnum)

OptIntOrIntEnum = IntOrIntEnum | None
OptIntOrIntEnumT = TypeVar("OptIntOrIntEnumT", bound=OptIntOrIntEnum)

ListOfIntsOrIntEnums = ListOfInts | ListOfIntEnums
ListOfIntsOrIntEnumsT = TypeVar("ListOfIntsOrIntEnumsT", bound=ListOfIntsOrIntEnums)

OptListOfIntsOrIntEnums = ListOfIntsOrIntEnums | None
OptListOfIntsOrIntEnumsT = TypeVar(
    "OptListOfIntsOrIntEnumsT", bound=OptListOfIntsOrIntEnums
)

SeqOfIntsOrIntEnums = SeqOfInts | SeqOfIntEnums
SeqOfIntsOrIntEnumsT = TypeVar("SeqOfIntsOrIntEnumsT", bound=SeqOfIntsOrIntEnums)

OptSeqOfIntsOrIntEnums = SeqOfIntsOrIntEnums | None
OptSeqOfIntsOrIntEnumsT = TypeVar(
    "OptSeqOfIntsOrIntEnumsT", bound=OptSeqOfIntsOrIntEnums
)


# Int x StrEnum
IntOrStrEnum = int | StrEnum
IntOrStrEnumT = TypeVar("IntOrStrEnumT", bound=IntOrStrEnum)

OptIntOrStrEnum = IntOrStrEnum | None
OptIntOrStrEnumT = TypeVar("OptIntOrStrEnumT", bound=OptIntOrStrEnum)

ListOfIntsOrStrEnums = ListOfInts | ListOfStrEnums
ListOfIntsOrStrEnumsT = TypeVar("ListOfIntsOrStrEnumsT", bound=ListOfIntsOrStrEnums)

OptListOfIntsOrStrEnums = ListOfIntsOrStrEnums | None
OptListOfIntsOrStrEnumsT = TypeVar(
    "OptListOfIntsOrStrEnumsT", bound=OptListOfIntsOrStrEnums
)

SeqOfIntsOrStrEnums = SeqOfInts | SeqOfStrEnums
SeqOfIntsOrStrEnumsT = TypeVar("SeqOfIntsOrStrEnumsT", bound=SeqOfIntsOrStrEnums)

OptSeqOfIntsOrStrEnums = SeqOfIntsOrStrEnums | None
OptSeqOfIntsOrStrEnumsT = TypeVar(
    "OptSeqOfIntsOrStrEnumsT", bound=OptSeqOfIntsOrStrEnums
)


# Int x UUID
IntOrUUID = int | UUID
IntOrUUIDT = TypeVar("IntOrUUIDT", bound=IntOrUUID)

OptIntOrUUID = IntOrUUID | None
OptIntOrUUIDT = TypeVar("OptIntOrUUIDT", bound=OptIntOrUUID)

ListOfIntsOrUUIDs = ListOfInts | ListOfUUIDs
ListOfIntsOrUUIDsT = TypeVar("ListOfIntsOrUUIDsT", bound=ListOfIntsOrUUIDs)

OptListOfIntsOrUUIDs = ListOfIntsOrUUIDs | None
OptListOfIntsOrUUIDsT = TypeVar("OptListOfIntsOrUUIDsT", bound=OptListOfIntsOrUUIDs)

SeqOfIntsOrUUIDs = SeqOfInts | SeqOfUUIDs
SeqOfIntsOrUUIDsT = TypeVar("SeqOfIntsOrUUIDsT", bound=SeqOfIntsOrUUIDs)
OptSeqOfIntsOrUUIDs = SeqOfIntsOrUUIDs | None
OptSeqOfIntsOrUUIDsT = TypeVar("OptSeqOfIntsOrUUIDsT", bound=OptSeqOfIntsOrUUIDs)


# Int x IntEnum
StrOrIntEnum = int | IntEnum
StrOrIntEnumT = TypeVar("StrOrIntEnumT", bound=StrOrIntEnum)

OptStrOrIntEnum = StrOrIntEnum | None
OptStrOrIntEnumT = TypeVar("OptStrOrIntEnumT", bound=OptStrOrIntEnum)

ListOfStrsOrIntEnums = ListOfInts | ListOfIntEnums
ListOfStrsOrIntEnumsT = TypeVar("ListOfStrsOrIntEnumsT", bound=ListOfStrsOrIntEnums)

OptListOfStrsOrIntEnums = ListOfStrsOrIntEnums | None
OptListOfStrsOrIntEnumsT = TypeVar(
    "OptListOfStrsOrIntEnumsT", bound=OptListOfStrsOrIntEnums
)

SeqOfStrsOrIntEnums = SeqOfInts | SeqOfIntEnums
SeqOfStrsOrIntEnumsT = TypeVar("SeqOfStrsOrIntEnumsT", bound=SeqOfStrsOrIntEnums)

OptSeqOfStrsOrIntEnums = SeqOfStrsOrIntEnums | None
OptSeqOfStrsOrIntEnumsT = TypeVar(
    "OptSeqOfStrsOrIntEnumsT", bound=OptSeqOfStrsOrIntEnums
)


# Str x StrEnum
StrOrStrEnum = str | StrEnum
StrOrStrEnumT = TypeVar("StrOrStrEnumT", bound=StrOrStrEnum)

OptStrOrStrEnum = StrOrStrEnum | None
OptStrOrStrEnumT = TypeVar("OptStrOrStrEnumT", bound=OptStrOrStrEnum)

ListOfStrsOrStrEnums = ListOfStrs | ListOfStrEnums
ListOfStrsOrStrEnumsT = TypeVar("ListOfStrsOrStrEnumsT", bound=ListOfStrsOrStrEnums)

OptListOfStrsOrStrEnums = ListOfStrsOrStrEnums | None
OptListOfStrsOrStrEnumsT = TypeVar(
    "OptListOfStrsOrStrEnumsT", bound=OptListOfStrsOrStrEnums
)

SeqOfStrsOrStrEnums = SeqOfStrs | SeqOfStrEnums
SeqOfStrsOrStrEnumsT = TypeVar("SeqOfStrsOrStrEnumsT", bound=SeqOfStrsOrStrEnums)

OptSeqOfStrsOrStrEnums = SeqOfStrsOrStrEnums | None
OptSeqOfStrsOrStrEnumsT = TypeVar(
    "OptSeqOfStrsOrStrEnumsT", bound=OptSeqOfStrsOrStrEnums
)


# Str x UUID
StrOrUUID = int | UUID
StrOrUUIDT = TypeVar("StrOrUUIDT", bound=StrOrUUID)

OptStrOrUUID = StrOrUUID | None
OptStrOrUUIDT = TypeVar("OptStrOrUUIDT", bound=OptStrOrUUID)

ListOfStrsOrUUIDs = ListOfStrs | ListOfUUIDs
ListOfStrsOrUUIDsT = TypeVar("ListOfStrsOrUUIDsT", bound=ListOfStrsOrUUIDs)

OptListOfStrsOrUUIDs = ListOfStrsOrUUIDs | None
OptListOfStrsOrUUIDsT = TypeVar("OptListOfStrsOrUUIDsT", bound=OptListOfStrsOrUUIDs)

SeqOfStrsOrUUIDs = SeqOfStrs | SeqOfUUIDs
SeqOfStrsOrUUIDsT = TypeVar("SeqOfStrsOrUUIDsT", bound=SeqOfStrsOrUUIDs)
OptSeqOfStrsOrUUIDs = SeqOfStrsOrUUIDs | None
OptSeqOfStrsOrUUIDsT = TypeVar("OptSeqOfStrsOrUUIDsT", bound=OptSeqOfStrsOrUUIDs)


# Any
ListOfAnyOrStrToAnyDict = ListOfAny | StrToAnyDict
ListOfAnyOrStrToAnyDictT = TypeVar(
    "ListOfAnyOrStrToAnyDictT", bound=ListOfAnyOrStrToAnyDict
)

OptListOfAnyOrStrToAnyDict = ListOfAnyOrStrToAnyDict | None
OptListOfAnyOrStrToAnyDictT = TypeVar(
    "OptListOfAnyOrStrToAnyDictT", bound=OptListOfAnyOrStrToAnyDict
)

ListOfAnyOrStrToAnyMapping = ListOfAny | StrToAnyMapping
ListOfAnyOrStrToAnyMappingT = TypeVar(
    "ListOfAnyOrStrToAnyMappingT", bound=ListOfAnyOrStrToAnyMapping
)

OptListOfAnyOrStrToAnyMapping = ListOfAnyOrStrToAnyMapping | None
OptListOfAnyOrStrToAnyMappingT = TypeVar(
    "OptListOfAnyOrStrToAnyMappingT", bound=OptListOfAnyOrStrToAnyMapping
)

SeqOfAnyOrStrToAnyDict = SeqOfAny | StrToAnyDict
SeqOfAnyOrStrToAnyDictT = TypeVar(
    "SeqOfAnyOrStrToAnyDictT", bound=SeqOfAnyOrStrToAnyDict
)

OptSeqOfAnyOrStrToAnyDict = SeqOfAnyOrStrToAnyDict | None
OptSeqOfAnyOrStrToAnyDictT = TypeVar(
    "OptSeqOfAnyOrStrToAnyDictT", bound=OptSeqOfAnyOrStrToAnyDict
)

SeqOfAnyOrStrToAnyMapping = SeqOfAny | StrToAnyMapping
SeqOfAnyOrStrToAnyMappingT = TypeVar(
    "SeqOfAnyOrStrToAnyMappingT", bound=SeqOfAnyOrStrToAnyMapping
)

OptSeqOfAnyOrStrToAnyMapping = SeqOfAnyOrStrToAnyMapping | None
OptSeqOfAnyOrStrToAnyMappingT = TypeVar(
    "OptSeqOfAnyOrStrToAnyMappingT", bound=OptSeqOfAnyOrStrToAnyMapping
)
