from typing import List, Optional, Sequence, TypeVar


StringT = TypeVar("StringT", bound=str)

OptionalString = Optional[str]
OptionalStringT = TypeVar("OptionalStringT", bound=OptionalString)

ListOfStrings = List[str]
ListOfStringsT = TypeVar("ListOfStringsT", bound=ListOfStrings)

OptionalListOfStrings = Optional[ListOfStrings]
OptionalListOfStringsT = TypeVar("OptionalListOfStringsT", bound=OptionalListOfStrings)

SequenceOfStrings = Sequence[str]
SequenceOfStringsT = TypeVar("SequenceOfStringsT", bound=SequenceOfStrings)

OptionalSequenceOfStrings = Optional[SequenceOfStrings]
OptionalSequenceOfStringsT = TypeVar(
    "OptionalSequenceOfStringsT", bound=OptionalSequenceOfStrings
)
