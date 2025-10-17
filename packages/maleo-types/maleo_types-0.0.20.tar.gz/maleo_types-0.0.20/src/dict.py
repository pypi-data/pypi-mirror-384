from typing import Any, Sequence, TypeVar
from .integer import ListOfInts, SeqOfInts
from .string import ListOfStrs, SeqOfStrs


_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


# Generic
OptDict = dict[_KT, _VT] | None
ListOfDicts = list[dict[_KT, _VT]]
OptListOfDicts = ListOfDicts[_KT, _VT] | None
SeqOfDicts = Sequence[dict[_KT, _VT]]
OptSeqOfDicts = SeqOfDicts[_KT, _VT] | None


# Bytes Key Value
BytesToBytesdict = dict[bytes, bytes]
OptBytesToBytesdict = BytesToBytesdict | None
ListOfBytesToBytesdict = list[BytesToBytesdict]
OptListOfBytesToBytesdict = ListOfBytesToBytesdict | None
SeqOfBytesToBytesdict = Sequence[BytesToBytesdict]
OptSeqOfBytesToBytesdict = SeqOfBytesToBytesdict | None


# Str key
# Any value
StrToAnyDict = dict[str, Any]
OptStrToAnyDict = StrToAnyDict | None
ListOfStrToAnyDict = list[StrToAnyDict]
OptListOfStrToAnyDict = ListOfStrToAnyDict | None
SeqOfStrToAnyDict = Sequence[StrToAnyDict]
OptSeqOfStrToAnyDict = SeqOfStrToAnyDict | None


# Object value
StrToObjectDict = dict[str, object]
OptStrToObjectDict = StrToObjectDict | None
ListOfStrToObjectDict = list[StrToObjectDict]
OptListOfStrToObjectDict = ListOfStrToObjectDict | None
SeqOfStrToObjectDict = Sequence[StrToObjectDict]
OptSeqOfStrToObjectDict = SeqOfStrToObjectDict | None


# Str value
StrToStrDict = dict[str, str]
OptStrToStrDict = StrToStrDict | None
ListOfStrToStrDict = list[StrToStrDict]
OptListOfStrToStrDict = ListOfStrToStrDict | None
SeqOfStrToStrDict = Sequence[StrToStrDict]
OptSeqOfStrToStrDict = SeqOfStrToStrDict | None


# Multi-Str value
StrToListOfStrsDict = dict[str, ListOfStrs]
OptStrToListOfStrsDict = StrToListOfStrsDict | None
StrToSeqOfStrsDict = dict[str, SeqOfStrs]
OptStrToSeqOfStrsDict = StrToSeqOfStrsDict | None


# Int value
StrToIntDict = dict[str, str]
OptStrToIntDict = StrToIntDict | None
ListOfStrToIntDict = list[StrToIntDict]
OptListOfStrToIntDict = ListOfStrToIntDict | None
SeqOfStrToIntDict = Sequence[StrToIntDict]
OptSeqOfStrToIntDict = SeqOfStrToIntDict | None


# Multi-Int value
StrToListOfIntsDict = dict[str, ListOfInts]
OptStrToListOfIntsDict = StrToListOfIntsDict | None
StrToSeqOfStrsDict = dict[str, SeqOfStrs]
OptStrToSeqOfStrsDict = StrToSeqOfStrsDict | None


# Int key
# Any value
IntToAnyDict = dict[int, Any]
OptIntToAnyDict = IntToAnyDict | None
ListOfIntToAnyDict = list[IntToAnyDict]
OptListOfIntToAnyDict = ListOfIntToAnyDict | None
SeqOfIntToAnyDict = Sequence[IntToAnyDict]
OptSeqOfIntToAnyDict = SeqOfIntToAnyDict | None


# Object value
IntToObjectDict = dict[int, object]
OptIntToObjectDict = IntToObjectDict | None
ListOfIntToObjectDict = list[IntToObjectDict]
OptListOfIntToObjectDict = ListOfIntToObjectDict | None
SeqOfIntToObjectDict = Sequence[IntToObjectDict]
OptSeqOfIntToObjectDict = SeqOfIntToObjectDict | None


# Str value
IntToStrDict = dict[int, str]
OptIntToStrDict = IntToStrDict | None
ListOfIntToStrDict = list[IntToStrDict]
OptListOfIntToStrDict = ListOfIntToStrDict | None
SeqOfIntToStrDict = Sequence[IntToStrDict]
OptSeqOfIntToStrDict = SeqOfIntToStrDict | None


# Multi-Str value
IntToListOfStrsDict = dict[int, ListOfStrs]
OptIntToListOfStrsDict = IntToListOfStrsDict | None
IntToSeqOfStrsDict = dict[int, SeqOfStrs]
OptIntToSeqOfStrsDict = IntToSeqOfStrsDict | None


# Int value
IntToIntDict = dict[int, int]
OptIntToIntDict = IntToIntDict | None
ListOfIntToIntDict = list[IntToIntDict]
OptListOfIntToIntDict = ListOfIntToIntDict | None
SeqOfIntToIntDict = Sequence[IntToIntDict]
OptSeqOfIntToIntDict = SeqOfIntToIntDict | None


# Multi-Int value
IntToListOfIntsDict = dict[int, ListOfInts]
OptIntToListOfIntsDict = IntToListOfIntsDict | None
IntToSeqOfIntsDict = dict[int, SeqOfInts]
OptIntToSeqOfIntsDict = IntToSeqOfIntsDict | None
