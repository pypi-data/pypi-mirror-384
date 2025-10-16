from datetime import date, datetime
from typing import Optional, List, Sequence, TypeVar


OptionalDate = Optional[date]
OptionalDateT = TypeVar("OptionalDateT", bound=OptionalDate)

ListOfDates = List[date]
ListOfDatesT = TypeVar("ListOfDatesT", bound=ListOfDates)

OptionalListOfDates = Optional[ListOfDates]
OptionalListOfDatesT = TypeVar("OptionalListOfDatesT", bound=OptionalListOfDates)

SequenceOfDates = Sequence[date]
SequenceOfDatesT = TypeVar("SequenceOfDatesT", bound=SequenceOfDates)

OptionalSequenceOfDates = Optional[SequenceOfDates]
OptionalSequenceOfDatesT = TypeVar(
    "OptionalSequenceOfDatesT", bound=OptionalSequenceOfDates
)

OptionalDatetime = Optional[datetime]
OptionalDatetimeT = TypeVar("OptionalDatetimeT", bound=OptionalDatetime)

ListOfDatetimes = List[datetime]
ListOfDatetimesT = TypeVar("ListOfDatetimesT", bound=ListOfDatetimes)

OptionalListOfDatetimes = Optional[ListOfDatetimes]
OptionalListOfDatetimesT = TypeVar(
    "OptionalListOfDatetimesT", bound=OptionalListOfDatetimes
)

SequenceOfDatetimes = Sequence[datetime]
SequenceOfDatetimesT = TypeVar("SequenceOfDatetimesT", bound=SequenceOfDatetimes)

OptionalSequenceOfDatetimes = Optional[SequenceOfDatetimes]
OptionalSequenceOfDatetimesT = TypeVar(
    "OptionalSequenceOfDatetimesT", bound=OptionalSequenceOfDatetimes
)
