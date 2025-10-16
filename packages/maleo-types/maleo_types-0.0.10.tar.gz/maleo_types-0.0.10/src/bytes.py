from typing import Optional, List, Sequence, TypeVar


OptionalBytes = Optional[bytes]
OptionalBytesT = TypeVar("OptionalBytesT", bound=OptionalBytes)

ListOfBytes = List[bytes]
ListOfBytesT = TypeVar("ListOfBytesT", bound=ListOfBytes)

OptionalListOfBytes = Optional[ListOfBytes]
OptionalListOfBytesT = TypeVar("OptionalListOfBytesT", bound=OptionalListOfBytes)

SequenceOfBytes = Sequence[bytes]
SequenceOfBytesT = TypeVar("SequenceOfBytesT", bound=SequenceOfBytes)

OptionalSequenceOfBytes = Optional[SequenceOfBytes]
OptionalSequenceOfBytesT = TypeVar(
    "OptionalSequenceOfBytesT", bound=OptionalSequenceOfBytes
)
