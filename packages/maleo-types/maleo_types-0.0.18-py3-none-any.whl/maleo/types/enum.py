from enum import IntEnum, StrEnum
from typing import Sequence, TypeVar


# Int Enum
IntEnumT = TypeVar("IntEnumT", bound=IntEnum)

OptIntEnum = IntEnum | None
OptIntEnumT = TypeVar("OptIntEnumT", bound=OptIntEnum)

ListOfIntEnums = list[IntEnum]
ListOfIntEnumsT = TypeVar("ListOfIntEnumsT", bound=ListOfIntEnums)

OptListOfIntEnums = ListOfIntEnums | None
OptListOfIntEnumsT = TypeVar("OptListOfIntEnumsT", bound=OptListOfIntEnums)

SeqOfIntEnums = Sequence[IntEnum]
SeqOfIntEnumsT = TypeVar("SeqOfIntEnumsT", bound=SeqOfIntEnums)

OptSeqOfIntEnums = SeqOfIntEnums | None
OptSeqOfIntEnumsT = TypeVar("OptSeqOfIntEnumsT", bound=OptSeqOfIntEnums)

# Str Enum
StrEnumT = TypeVar("StrEnumT", bound=StrEnum)

OptStrEnum = StrEnum | None
OptStrEnumT = TypeVar("OptStrEnumT", bound=OptStrEnum)

ListOfStrEnums = list[StrEnum]
ListOfStrEnumsT = TypeVar("ListOfStrEnumsT", bound=ListOfStrEnums)

OptListOfStrEnums = ListOfStrEnums | None
OptListOfStrEnumsT = TypeVar("OptListOfStrEnumsT", bound=OptListOfStrEnums)

SeqOfStrEnums = Sequence[StrEnum]
SeqOfStrEnumsT = TypeVar("SeqOfStrEnumsT", bound=SeqOfStrEnums)

OptSeqOfStrEnums = SeqOfStrEnums | None
OptSeqOfStrEnumsT = TypeVar("OptSeqOfStrEnumsT", bound=OptSeqOfStrEnums)
