from typing import Sequence, Tuple, TypeVar


OptBytes = bytes | None
OptBytesT = TypeVar("OptBytesT", bound=OptBytes)

ListOfBytes = list[bytes]
ListOfBytesT = TypeVar("ListOfBytesT", bound=ListOfBytes)

OptListOfBytes = ListOfBytes | None
OptListOfBytesT = TypeVar("OptListOfBytesT", bound=OptListOfBytes)

SeqOfBytes = Sequence[bytes]
SeqOfBytesT = TypeVar("SeqOfBytesT", bound=SeqOfBytes)

OptSeqOfBytes = SeqOfBytes | None
OptSeqOfBytesT = TypeVar("OptSeqOfBytesT", bound=OptSeqOfBytes)

# Bytes Tuple
DoubleBytes = Tuple[bytes, bytes]
ListOfDoubleBytes = list[DoubleBytes]
SeqOfDoubleBytes = Sequence[DoubleBytes]

TripleBytes = Tuple[bytes, bytes, bytes]
ListOfTripleBytes = list[TripleBytes]
SeqOfTripleBytes = Sequence[TripleBytes]

QuadrupleBytes = Tuple[bytes, bytes, bytes, bytes]
ListOfQuadrupleBytes = list[QuadrupleBytes]
SeqOfQuadrupleBytes = Sequence[QuadrupleBytes]

ManyBytes = Tuple[bytes, ...]
ListOfManyBytes = list[ManyBytes]
SeqOfManyBytes = Sequence[ManyBytes]

# Opt Bytes Tuple
DoubleOptBytes = Tuple[OptBytes, OptBytes]
ListOfDoubleOptBytes = list[DoubleOptBytes]
SeqOfDoubleOptBytes = Sequence[DoubleOptBytes]

TripleOptBytes = Tuple[OptBytes, OptBytes, OptBytes]
ListOfTripleOptBytes = list[TripleOptBytes]
SeqOfTripleOptBytes = Sequence[TripleOptBytes]

QuadrupleOptBytes = Tuple[OptBytes, OptBytes, OptBytes, OptBytes]
ListOfQuadrupleOptBytes = list[QuadrupleOptBytes]
SeqOfQuadrupleOptBytes = Sequence[QuadrupleOptBytes]

ManyOptBytes = Tuple[OptBytes, ...]
ListOfManyOptBytes = list[ManyOptBytes]
SeqOfManyOptBytes = Sequence[ManyOptBytes]
