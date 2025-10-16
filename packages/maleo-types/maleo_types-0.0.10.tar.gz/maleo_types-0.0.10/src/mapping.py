from typing import Any, List, Mapping, Optional, Sequence, TypeVar
from .string import ListOfStrings, SequenceOfStrings


_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


# Generic
OptionalMapping = Optional[Mapping[_KT, _VT]]
ListOfMappings = List[Mapping[_KT, _VT]]
OptionalListOfMappings = Optional[ListOfMappings[_KT, _VT]]
SequenceOfMappings = Sequence[Mapping[_KT, _VT]]
OptionalSequenceOfMappings = Optional[SequenceOfMappings[_KT, _VT]]


# String key
# Any value
StringToAnyMapping = Mapping[str, Any]
OptionalStringToAnyMapping = Optional[StringToAnyMapping]
ListOfStringToAnyMapping = List[StringToAnyMapping]
OptionalListOfStringToAnyMapping = Optional[ListOfStringToAnyMapping]
SequenceOfStringToAnyMapping = Sequence[StringToAnyMapping]
OptionalSequenceOfStringToAnyMapping = Optional[SequenceOfStringToAnyMapping]

# Object value
StringToObjectMapping = Mapping[str, object]
OptionalStringToObjectMapping = Optional[StringToObjectMapping]
ListOfStringToObjectMapping = List[StringToObjectMapping]
OptionalListOfStringToObjectMapping = Optional[ListOfStringToObjectMapping]
SequenceOfStringToObjectMapping = Sequence[StringToObjectMapping]
OptionalSequenceOfStringToObjectMapping = Optional[SequenceOfStringToObjectMapping]

# String value
StringToStringMapping = Mapping[str, str]
OptionalStringToStringMapping = Optional[StringToStringMapping]
ListOfStringToStringMapping = List[StringToStringMapping]
OptionalListOfStringToStringMapping = Optional[ListOfStringToStringMapping]
SequenceOfStringToStringMapping = Sequence[StringToStringMapping]
OptionalSequenceOfStringToStringMapping = Optional[SequenceOfStringToStringMapping]

# Multi-String value
StringToListOfStringsMapping = Mapping[str, ListOfStrings]
OptionalStringToListOfStringsMapping = Optional[StringToListOfStringsMapping]
StringToSequenceOfStringsMapping = Mapping[str, SequenceOfStrings]
OptionalStringToSequenceOfStringsMapping = Optional[StringToSequenceOfStringsMapping]

# Integer key
# Any value
IntToAnyMapping = Mapping[int, Any]
OptionalIntToAnyMapping = Optional[IntToAnyMapping]
ListOfIntToAnyMapping = List[IntToAnyMapping]
OptionalListOfIntToAnyMapping = Optional[ListOfIntToAnyMapping]
SequenceOfIntToAnyMapping = Sequence[IntToAnyMapping]
OptionalSequenceOfIntToAnyMapping = Optional[SequenceOfIntToAnyMapping]

# String value
IntToStringMapping = Mapping[int, str]
OptionalIntToStringMapping = Optional[IntToStringMapping]
ListOfIntToStringMapping = List[IntToStringMapping]
OptionalListOfIntToStringMapping = Optional[ListOfIntToStringMapping]
SequenceOfIntToStringMapping = Sequence[IntToStringMapping]
OptionalSequenceOfIntToStringMapping = Optional[SequenceOfIntToStringMapping]
