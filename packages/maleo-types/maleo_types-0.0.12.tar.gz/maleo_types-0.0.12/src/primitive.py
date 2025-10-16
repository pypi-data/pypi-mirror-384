from typing import Mapping, Sequence, Tuple, TypeVar

Primitive = bool | float | int | str | None
PrimitiveT = TypeVar("PrimitiveT", bound=Primitive)


ListOfPrimitives = list[Primitive]
ListOfPrimitivesT = TypeVar("ListOfPrimitivesT", bound=ListOfPrimitives)


PrimitiveOrListOfPrimitives = Primitive | ListOfPrimitives
PrimitiveOrListOfPrimitivesT = TypeVar(
    "PrimitiveOrListOfPrimitivesT", bound=PrimitiveOrListOfPrimitives
)


SeqOfPrimitives = Sequence[ListOfPrimitives]
SeqOfPrimitivesT = TypeVar("SeqOfPrimitivesT", bound=SeqOfPrimitives)


PrimitiveOrSeqOfPrimitives = Primitive | SeqOfPrimitives
PrimitiveOrSeqOfPrimitivesT = TypeVar(
    "PrimitiveOrSeqOfPrimitivesT", bound=PrimitiveOrSeqOfPrimitives
)


StrPrimitiveTuple = Tuple[str, Primitive]
ListOfStrPrimitiveTuples = list[StrPrimitiveTuple]
SeqOfStrPrimitiveTuples = Sequence[StrPrimitiveTuple]
ManyStrPrimitiveTuplesTuple = Tuple[StrPrimitiveTuple, ...]
StrToPrimitiveOrSeqOfPrimitivesDict = dict[str, PrimitiveOrSeqOfPrimitives]
StrToPrimitiveOrSeqOfPrimitivesMapping = Mapping[str, PrimitiveOrSeqOfPrimitives]
