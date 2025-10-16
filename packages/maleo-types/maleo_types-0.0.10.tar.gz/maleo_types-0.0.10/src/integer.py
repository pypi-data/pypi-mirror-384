from typing import List, Optional, Sequence, TypeVar


IntegerT = TypeVar("IntegerT", bound=int)

OptionalInteger = Optional[int]
OptionalIntegerT = TypeVar("OptionalIntegerT", bound=OptionalInteger)

ListOfIntegers = List[int]
ListOfIntegersT = TypeVar("ListOfIntegersT", bound=ListOfIntegers)

OptionalListOfIntegers = Optional[ListOfIntegers]
OptionalListOfIntegersT = TypeVar(
    "OptionalListOfIntegersT", bound=OptionalListOfIntegers
)

SequenceOfIntegers = Sequence[int]
SequenceOfIntegersT = TypeVar("SequenceOfIntegersT", bound=SequenceOfIntegers)

OptionalSequenceOfIntegers = Optional[SequenceOfIntegers]
OptionalSequenceOfIntegersT = TypeVar(
    "OptionalSequenceOfIntegersT", bound=OptionalSequenceOfIntegers
)
