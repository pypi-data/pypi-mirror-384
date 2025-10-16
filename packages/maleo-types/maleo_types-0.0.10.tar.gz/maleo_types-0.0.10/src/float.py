from typing import List, Optional, Sequence, TypeVar


FloatT = TypeVar("FloatT", bound=float)

OptionalFloat = Optional[float]
OptionalFloatT = TypeVar("OptionalFloatT", bound=OptionalFloat)

ListOfFloats = List[float]
ListOfFloatsT = TypeVar("ListOfFloatsT", bound=ListOfFloats)

OptionalListOfFloats = Optional[ListOfFloats]
OptionalListOfFloatsT = TypeVar("OptionalListOfFloatsT", bound=OptionalListOfFloats)

SequenceOfFloats = Sequence[float]
SequenceOfFloatsT = TypeVar("SequenceOfFloatsT", bound=SequenceOfFloats)

OptionalSequenceOfFloats = Optional[SequenceOfFloats]
OptionalSequenceOfFloatsT = TypeVar(
    "OptionalSequenceOfFloatsT", bound=OptionalSequenceOfFloats
)
