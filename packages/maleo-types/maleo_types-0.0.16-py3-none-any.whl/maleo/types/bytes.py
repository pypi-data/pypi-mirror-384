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
OptDoubleBytes = DoubleBytes | None
ListOfDoubleBytes = list[DoubleBytes]
OptListOfDoubleBytes = ListOfDoubleBytes | None
SeqOfDoubleBytes = Sequence[DoubleBytes]
OptSeqOfDoubleBytes = SeqOfDoubleBytes | None

TripleBytes = Tuple[bytes, bytes, bytes]
OptTripleBytes = TripleBytes | None
ListOfTripleBytes = list[TripleBytes]
OptListOfTripleBytes = ListOfTripleBytes | None
SeqOfTripleBytes = Sequence[TripleBytes]
OptSeqOfTripleBytes = SeqOfTripleBytes | None

QuintupleBytes = Tuple[bytes, bytes, bytes, bytes]
OptQuintupleBytes = QuintupleBytes | None
ListOfQuintupleBytes = list[QuintupleBytes]
OptListOfQuintupleBytes = ListOfQuintupleBytes | None
SeqOfQuintupleBytes = Sequence[QuintupleBytes]
OptSeqOfQuintupleBytes = SeqOfQuintupleBytes | None

QuintupleBytes = Tuple[bytes, bytes, bytes, bytes, bytes]
OptQuintupleBytes = QuintupleBytes | None
ListOfQuintupleBytes = list[QuintupleBytes]
OptListOfQuintupleBytes = ListOfQuintupleBytes | None
SeqOfQuintupleBytes = Sequence[QuintupleBytes]
OptSeqOfQuintupleBytes = SeqOfQuintupleBytes | None

ManyBytes = Tuple[bytes, ...]
OptManyBytes = ManyBytes | None
ListOfManyBytes = list[ManyBytes]
OptListOfManyBytes = ListOfManyBytes | None
SeqOfManyBytes = Sequence[ManyBytes]
OptSeqOfManyBytes = SeqOfManyBytes | None

# Opt Bytes Tuple
DoubleOptBytes = Tuple[OptBytes, OptBytes]
OptDoubleOptBytes = DoubleOptBytes | None
ListOfDoubleOptBytes = list[DoubleOptBytes]
OptListOfDoubleOptBytes = ListOfDoubleOptBytes | None
SeqOfDoubleOptBytes = Sequence[DoubleOptBytes]
OptSeqOfDoubleOptBytes = SeqOfDoubleOptBytes | None

TripleOptBytes = Tuple[OptBytes, OptBytes, OptBytes]
OptTripleOptBytes = TripleOptBytes | None
ListOfTripleOptBytes = list[TripleOptBytes]
OptListOfTripleOptBytes = ListOfTripleOptBytes | None
SeqOfTripleOptBytes = Sequence[TripleOptBytes]
OptSeqOfTripleOptBytes = SeqOfTripleOptBytes | None

QuintupleOptBytes = Tuple[OptBytes, OptBytes, OptBytes, OptBytes]
OptQuintupleOptBytes = QuintupleOptBytes | None
ListOfQuintupleOptBytes = list[QuintupleOptBytes]
OptListOfQuintupleOptBytes = ListOfQuintupleOptBytes | None
SeqOfQuintupleOptBytes = Sequence[QuintupleOptBytes]
OptSeqOfQuintupleOptBytes = SeqOfQuintupleOptBytes | None

QuintupleOptBytes = Tuple[OptBytes, OptBytes, OptBytes, OptBytes, OptBytes]
OptQuintupleOptBytes = QuintupleOptBytes | None
ListOfQuintupleOptBytes = list[QuintupleOptBytes]
OptListOfQuintupleOptBytes = ListOfQuintupleOptBytes | None
SeqOfQuintupleOptBytes = Sequence[QuintupleOptBytes]
OptSeqOfQuintupleOptBytes = SeqOfQuintupleOptBytes | None

ManyOptBytes = Tuple[OptBytes, ...]
OptManyOptBytes = ManyOptBytes | None
ListOfManyOptBytes = list[ManyOptBytes]
OptListOfManyOptBytes = ListOfManyOptBytes | None
SeqOfManyOptBytes = Sequence[ManyOptBytes]
OptSeqOfManyOptBytes = SeqOfManyOptBytes | None
