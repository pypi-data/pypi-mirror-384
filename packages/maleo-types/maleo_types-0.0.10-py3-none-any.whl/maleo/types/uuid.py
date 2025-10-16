from typing import List, Optional, Sequence, TypeVar
from uuid import UUID


UUIDT = TypeVar("UUIDT", bound=UUID)

OptionalUUID = Optional[UUID]
OptionalUUIDT = TypeVar("OptionalUUIDT", bound=OptionalUUID)

ListOfUUIDs = List[UUID]
ListOfUUIDsT = TypeVar("ListOfUUIDsT", bound=ListOfUUIDs)

OptionalListOfUUIDs = Optional[ListOfUUIDs]
OptionalListOfUUIDsT = TypeVar("OptionalListOfUUIDsT", bound=OptionalListOfUUIDs)

SequenceOfUUIDs = Sequence[UUID]
SequenceOfUUIDsT = TypeVar("SequenceOfUUIDsT", bound=SequenceOfUUIDs)

OptionalSequenceOfUUIDs = Optional[SequenceOfUUIDs]
OptionalSequenceOfUUIDsT = TypeVar(
    "OptionalSequenceOfUUIDsT", bound=OptionalSequenceOfUUIDs
)
