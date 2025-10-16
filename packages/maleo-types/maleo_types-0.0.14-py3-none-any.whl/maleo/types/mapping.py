from typing import Any, Mapping, Sequence, TypeVar
from .integer import ListOfInts, SeqOfInts
from .string import ListOfStrs, SeqOfStrs


_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


# Generic
OptMapping = Mapping[_KT, _VT] | None
ListOfMappings = list[Mapping[_KT, _VT]]
OptListOfMappings = ListOfMappings[_KT, _VT] | None
SeqOfMappings = Sequence[Mapping[_KT, _VT]]
OptSeqOfMappings = SeqOfMappings[_KT, _VT] | None


# Bytes Key Value
BytesToBytesMapping = Mapping[bytes, bytes]
OptBytesToBytesMapping = BytesToBytesMapping | None
ListOfBytesToBytesMapping = list[BytesToBytesMapping]
OptListOfBytesToBytesMapping = ListOfBytesToBytesMapping | None
SeqOfBytesToBytesMapping = Sequence[BytesToBytesMapping]
OptSeqOfBytesToBytesMapping = SeqOfBytesToBytesMapping | None


# Str key
# Any value
StrToAnyMapping = Mapping[str, Any]
OptStrToAnyMapping = StrToAnyMapping | None
ListOfStrToAnyMapping = list[StrToAnyMapping]
OptListOfStrToAnyMapping = ListOfStrToAnyMapping | None
SeqOfStrToAnyMapping = Sequence[StrToAnyMapping]
OptSeqOfStrToAnyMapping = SeqOfStrToAnyMapping | None


# Object value
StrToObjectMapping = Mapping[str, object]
OptStrToObjectMapping = StrToObjectMapping | None
ListOfStrToObjectMapping = list[StrToObjectMapping]
OptListOfStrToObjectMapping = ListOfStrToObjectMapping | None
SeqOfStrToObjectMapping = Sequence[StrToObjectMapping]
OptSeqOfStrToObjectMapping = SeqOfStrToObjectMapping | None


# Str value
StrToStrMapping = Mapping[str, str]
OptStrToStrMapping = StrToStrMapping | None
ListOfStrToStrMapping = list[StrToStrMapping]
OptListOfStrToStrMapping = ListOfStrToStrMapping | None
SeqOfStrToStrMapping = Sequence[StrToStrMapping]
OptSeqOfStrToStrMapping = SeqOfStrToStrMapping | None


# Multi-Str value
StrToListOfStrsMapping = Mapping[str, ListOfStrs]
OptStrToListOfStrsMapping = StrToListOfStrsMapping | None
StrToSeqOfStrsMapping = Mapping[str, SeqOfStrs]
OptStrToSeqOfStrsMapping = StrToSeqOfStrsMapping | None


# Int value
StrToIntMapping = Mapping[str, str]
OptStrToIntMapping = StrToIntMapping | None
ListOfStrToIntMapping = list[StrToIntMapping]
OptListOfStrToIntMapping = ListOfStrToIntMapping | None
SeqOfStrToIntMapping = Sequence[StrToIntMapping]
OptSeqOfStrToIntMapping = SeqOfStrToIntMapping | None


# Multi-Int value
StrToListOfIntsMapping = Mapping[str, ListOfInts]
OptStrToListOfIntsMapping = StrToListOfIntsMapping | None
StrToSeqOfStrsMapping = Mapping[str, SeqOfStrs]
OptStrToSeqOfStrsMapping = StrToSeqOfStrsMapping | None


# Int key
# Any value
IntToAnyMapping = Mapping[int, Any]
OptIntToAnyMapping = IntToAnyMapping | None
ListOfIntToAnyMapping = list[IntToAnyMapping]
OptListOfIntToAnyMapping = ListOfIntToAnyMapping | None
SeqOfIntToAnyMapping = Sequence[IntToAnyMapping]
OptSeqOfIntToAnyMapping = SeqOfIntToAnyMapping | None


# Object value
IntToObjectMapping = Mapping[int, object]
OptIntToObjectMapping = IntToObjectMapping | None
ListOfIntToObjectMapping = list[IntToObjectMapping]
OptListOfIntToObjectMapping = ListOfIntToObjectMapping | None
SeqOfIntToObjectMapping = Sequence[IntToObjectMapping]
OptSeqOfIntToObjectMapping = SeqOfIntToObjectMapping | None


# Str value
IntToStrMapping = Mapping[int, str]
OptIntToStrMapping = IntToStrMapping | None
ListOfIntToStrMapping = list[IntToStrMapping]
OptListOfIntToStrMapping = ListOfIntToStrMapping | None
SeqOfIntToStrMapping = Sequence[IntToStrMapping]
OptSeqOfIntToStrMapping = SeqOfIntToStrMapping | None


# Multi-Str value
IntToListOfStrsMapping = Mapping[int, ListOfStrs]
OptIntToListOfStrsMapping = IntToListOfStrsMapping | None
IntToSeqOfStrsMapping = Mapping[int, SeqOfStrs]
OptIntToSeqOfStrsMapping = IntToSeqOfStrsMapping | None


# Int value
IntToIntMapping = Mapping[int, int]
OptIntToIntMapping = IntToIntMapping | None
ListOfIntToIntMapping = list[IntToIntMapping]
OptListOfIntToIntMapping = ListOfIntToIntMapping | None
SeqOfIntToIntMapping = Sequence[IntToIntMapping]
OptSeqOfIntToIntMapping = SeqOfIntToIntMapping | None


# Multi-Int value
IntToListOfIntsMapping = Mapping[int, ListOfInts]
OptIntToListOfIntsMapping = IntToListOfIntsMapping | None
IntToSeqOfIntsMapping = Mapping[int, SeqOfInts]
OptIntToSeqOfIntsMapping = IntToSeqOfIntsMapping | None
