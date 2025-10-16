from typing import Sequence, Tuple, TypeVar
from uuid import UUID


UUIDT = TypeVar("UUIDT", bound=UUID)

OptUUID = UUID | None
OptUUIDT = TypeVar("OptUUIDT", bound=OptUUID)

ListOfUUIDs = list[UUID]
ListOfUUIDsT = TypeVar("ListOfUUIDsT", bound=ListOfUUIDs)

OptListOfUUIDs = ListOfUUIDs | None
OptListOfUUIDsT = TypeVar("OptListOfUUIDsT", bound=OptListOfUUIDs)

SeqOfUUIDs = Sequence[UUID]
SeqOfUUIDsT = TypeVar("SeqOfUUIDsT", bound=SeqOfUUIDs)

OptSeqOfUUIDs = SeqOfUUIDs | None
OptSeqOfUUIDsT = TypeVar("OptSeqOfUUIDsT", bound=OptSeqOfUUIDs)

# UUIDs Tuple
DoubleUUIDs = Tuple[UUID, UUID]
OptDoubleUUIDs = DoubleUUIDs | None
ListOfDoubleUUIDs = list[DoubleUUIDs]
OptListOfDoubleUUIDs = ListOfDoubleUUIDs | None
SeqOfDoubleUUIDs = Sequence[DoubleUUIDs]
OptSeqOfDoubleUUIDs = SeqOfDoubleUUIDs | None

TripleUUIDs = Tuple[UUID, UUID, UUID]
OptTripleUUIDs = TripleUUIDs | None
ListOfTripleUUIDs = list[TripleUUIDs]
OptListOfTripleUUIDs = ListOfTripleUUIDs | None
SeqOfTripleUUIDs = Sequence[TripleUUIDs]
OptSeqOfTripleUUIDs = SeqOfTripleUUIDs | None

QuadrupleUUIDs = Tuple[UUID, UUID, UUID, UUID]
OptQuadrupleUUIDs = QuadrupleUUIDs | None
ListOfQuadrupleUUIDs = list[QuadrupleUUIDs]
OptListOfQuadrupleUUIDs = ListOfQuadrupleUUIDs | None
SeqOfQuadrupleUUIDs = Sequence[QuadrupleUUIDs]
OptSeqOfQuadrupleUUIDs = SeqOfQuadrupleUUIDs | None

QuintupleUUIDs = Tuple[UUID, UUID, UUID, UUID]
OptQuintupleUUIDs = QuintupleUUIDs | None
ListOfQuintupleUUIDs = list[QuintupleUUIDs]
OptListOfQuintupleUUIDs = ListOfQuintupleUUIDs | None
SeqOfQuintupleUUIDs = Sequence[QuintupleUUIDs]
OptSeqOfQuintupleUUIDs = SeqOfQuintupleUUIDs | None

ManyUUIDs = Tuple[UUID, ...]
OptManyUUIDs = ManyUUIDs | None
ListOfManyUUIDs = list[ManyUUIDs]
OptListOfManyUUIDs = ListOfManyUUIDs | None
SeqOfManyUUIDs = Sequence[ManyUUIDs]
OptSeqOfManyUUIDs = SeqOfManyUUIDs | None

# Opt UUIDs Tuple
DoubleOptUUIDs = Tuple[OptUUID, OptUUID]
OptDoubleOptUUIDs = DoubleOptUUIDs | None
ListOfDoubleOptUUIDs = list[DoubleOptUUIDs]
OptListOfDoubleOptUUIDs = ListOfDoubleOptUUIDs | None
SeqOfDoubleOptUUIDs = Sequence[DoubleOptUUIDs]
OptSeqOfDoubleOptUUIDs = SeqOfDoubleOptUUIDs | None

TripleOptUUIDs = Tuple[OptUUID, OptUUID, OptUUID]
OptTripleOptUUIDs = TripleOptUUIDs | None
ListOfTripleOptUUIDs = list[TripleOptUUIDs]
OptListOfTripleOptUUIDs = ListOfTripleOptUUIDs | None
SeqOfTripleOptUUIDs = Sequence[TripleOptUUIDs]
OptSeqOfTripleOptUUIDs = SeqOfTripleOptUUIDs | None

QuadrupleOptUUIDs = Tuple[OptUUID, OptUUID, OptUUID, OptUUID]
OptQuadrupleOptUUIDs = QuadrupleOptUUIDs | None
ListOfQuadrupleOptUUIDs = list[QuadrupleOptUUIDs]
OptListOfQuadrupleOptUUIDs = ListOfQuadrupleOptUUIDs | None
SeqOfQuadrupleOptUUIDs = Sequence[QuadrupleOptUUIDs]
OptSeqOfQuadrupleOptUUIDs = SeqOfQuadrupleOptUUIDs | None

QuintupleOptUUIDs = Tuple[OptUUID, OptUUID, OptUUID, OptUUID, OptUUID]
OptQuintupleOptUUIDs = QuintupleOptUUIDs | None
ListOfQuintupleOptUUIDs = list[QuintupleOptUUIDs]
OptListOfQuintupleOptUUIDs = ListOfQuintupleOptUUIDs | None
SeqOfQuintupleOptUUIDs = Sequence[QuintupleOptUUIDs]
OptSeqOfQuintupleOptUUIDs = SeqOfQuintupleOptUUIDs | None

ManyOptUUIDs = Tuple[OptUUID, ...]
OptManyOptUUIDs = ManyOptUUIDs | None
ListOfManyOptUUIDs = list[ManyOptUUIDs]
OptListOfManyOptUUIDs = ListOfManyOptUUIDs | None
SeqOfManyOptUUIDs = Sequence[ManyOptUUIDs]
OptSeqOfManyOptUUIDs = SeqOfManyOptUUIDs | None
