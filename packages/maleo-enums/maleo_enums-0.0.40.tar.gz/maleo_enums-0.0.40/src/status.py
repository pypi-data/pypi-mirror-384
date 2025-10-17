from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Sequence, TypeVar
from maleo.types.string import ListOfStrs


class DataStatus(StrEnum):
    DELETED = "deleted"
    INACTIVE = "inactive"
    ACTIVE = "active"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


DataStatusT = TypeVar("DataStatusT", bound=DataStatus)
OptDataStatus = DataStatus | None
OptDataStatusT = TypeVar("OptDataStatusT", bound=OptDataStatus)


class SimpleDataStatusMixin(BaseModel, Generic[OptDataStatusT]):
    status: Annotated[OptDataStatusT, Field(..., description="Status")]


class FullDataStatusMixin(BaseModel, Generic[OptDataStatusT]):
    data_status: Annotated[OptDataStatusT, Field(..., description="Status")]


ListOfDataStatuses = list[DataStatus]
ListOfDataStatusesT = TypeVar("ListOfDataStatusesT", bound=ListOfDataStatuses)
OptListOfDataStatuses = ListOfDataStatuses | None
OptListOfDataStatusesT = TypeVar("OptListOfDataStatusesT", bound=OptListOfDataStatuses)


class SimpleDataStatusesMixin(BaseModel, Generic[OptListOfDataStatusesT]):
    statuses: Annotated[OptListOfDataStatusesT, Field(..., description="Statuses")]


class FullDataStatusesMixin(BaseModel, Generic[OptListOfDataStatusesT]):
    data_statuses: Annotated[OptListOfDataStatusesT, Field(..., description="Statuses")]


SeqOfDataStatuses = Sequence[DataStatus]
SeqOfDataStatusesT = TypeVar("SeqOfDataStatusesT", bound=SeqOfDataStatuses)
OptSeqOfDataStatuses = SeqOfDataStatuses | None
OptSeqOfDataStatusesT = TypeVar("OptSeqOfDataStatusesT", bound=OptSeqOfDataStatuses)


FULL_DATA_STATUSES: ListOfDataStatuses = [
    DataStatus.ACTIVE,
    DataStatus.INACTIVE,
    DataStatus.DELETED,
]

BASIC_DATA_STATUSES: ListOfDataStatuses = [
    DataStatus.ACTIVE,
    DataStatus.INACTIVE,
]
