from typing import List, Sequence, Tuple, TypeVar
from uuid import UUID


UUIDT = TypeVar("UUIDT", bound=UUID)

OptUUID = UUID | None
OptUUIDT = TypeVar("OptUUIDT", bound=OptUUID)

ListOfUUIDs = List[UUID]
ListOfUUIDsT = TypeVar("ListOfUUIDsT", bound=ListOfUUIDs)

OptListOfUUIDs = ListOfUUIDs | None
OptListOfUUIDsT = TypeVar("OptListOfUUIDsT", bound=OptListOfUUIDs)

SeqOfUUIDs = Sequence[UUID]
SeqOfUUIDsT = TypeVar("SeqOfUUIDsT", bound=SeqOfUUIDs)

OptSeqOfUUIDs = SeqOfUUIDs | None
OptSeqOfUUIDsT = TypeVar("OptSeqOfUUIDsT", bound=OptSeqOfUUIDs)

# UUIDs Tuple
DoubleUUIDs = Tuple[UUID, UUID]
ListOfDoubleUUIDs = list[DoubleUUIDs]
SeqOfDoubleUUIDs = Sequence[DoubleUUIDs]

TripleUUIDs = Tuple[UUID, UUID, UUID]
ListOfTripleUUIDs = list[TripleUUIDs]
SeqOfTripleUUIDs = Sequence[TripleUUIDs]

QuadrupleUUIDs = Tuple[UUID, UUID, UUID, UUID]
ListOfQuadrupleUUIDs = list[QuadrupleUUIDs]
SeqOfQuadrupleUUIDs = Sequence[QuadrupleUUIDs]

ManyUUIDs = Tuple[UUID, ...]
ListOfManyUUIDs = list[ManyUUIDs]
SeqOfManyUUIDs = Sequence[ManyUUIDs]

# Opt UUIDs Tuple
DoubleOptUUIDs = Tuple[OptUUID, OptUUID]
ListOfDoubleOptUUIDs = list[DoubleOptUUIDs]
SeqOfDoubleOptUUIDs = Sequence[DoubleOptUUIDs]

TripleOptUUIDs = Tuple[OptUUID, OptUUID, OptUUID]
ListOfTripleOptUUIDs = list[TripleOptUUIDs]
SeqOfTripleOptUUIDs = Sequence[TripleOptUUIDs]

QuadrupleOptUUIDs = Tuple[OptUUID, OptUUID, OptUUID, OptUUID]
ListOfQuadrupleOptUUIDs = list[QuadrupleOptUUIDs]
SeqOfQuadrupleOptUUIDs = Sequence[QuadrupleOptUUIDs]

ManyOptUUIDs = Tuple[OptUUID, ...]
ListOfManyOptUUIDs = list[ManyOptUUIDs]
SeqOfManyOptUUIDs = Sequence[ManyOptUUIDs]
