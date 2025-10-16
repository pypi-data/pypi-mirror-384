from datetime import date, datetime
from typing import Sequence, TypeVar


# Date
OptDate = date | None
OptDateT = TypeVar("OptDateT", bound=OptDate)

ListOfDates = list[date]
ListOfDatesT = TypeVar("ListOfDatesT", bound=ListOfDates)

OptListOfDates = ListOfDates | None
OptListOfDatesT = TypeVar("OptListOfDatesT", bound=OptListOfDates)

SeqOfDates = Sequence[date]
SeqOfDatesT = TypeVar("SeqOfDatesT", bound=SeqOfDates)

OptSeqOfDates = SeqOfDates | None
OptSeqOfDatesT = TypeVar("OptSeqOfDatesT", bound=OptSeqOfDates)


# Datetime
OptDatetime = datetime | None
OptDatetimeT = TypeVar("OptDatetimeT", bound=OptDatetime)

ListOfDatetimes = list[datetime]
ListOfDatetimesT = TypeVar("ListOfDatetimesT", bound=ListOfDatetimes)

OptListOfDatetimes = ListOfDatetimes | None
OptListOfDatetimesT = TypeVar("OptListOfDatetimesT", bound=OptListOfDatetimes)

SeqOfDatetimes = Sequence[datetime]
SeqOfDatetimesT = TypeVar("SeqOfDatetimesT", bound=SeqOfDatetimes)

OptSeqOfDatetimes = SeqOfDatetimes | None
OptSeqOfDatetimesT = TypeVar("OptSeqOfDatetimesT", bound=OptSeqOfDatetimes)
