from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Sequence, TypeVar
from maleo.types.string import ListOfStrs


class Environment(StrEnum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


EnvironmentT = TypeVar("EnvironmentT", bound=Environment)
OptEnvironment = Environment | None
OptEnvironmentT = TypeVar("OptEnvironmentT", bound=OptEnvironment)


class EnvironmentMixin(BaseModel, Generic[OptEnvironmentT]):
    environment: Annotated[OptEnvironmentT, Field(..., description="Environment")]


ListOfEnvironments = list[Environment]
ListOfEnvironmentsT = TypeVar("ListOfEnvironmentsT", bound=ListOfEnvironments)
OptListOfEnvironments = ListOfEnvironments | None
OptListOfEnvironmentsT = TypeVar("OptListOfEnvironmentsT", bound=OptListOfEnvironments)


class EnvironmentsMixin(BaseModel, Generic[OptListOfEnvironmentsT]):
    environments: Annotated[
        OptListOfEnvironmentsT, Field(..., description="Environments")
    ]


SeqOfEnvironments = Sequence[Environment]
SeqOfEnvironmentsT = TypeVar("SeqOfEnvironmentsT", bound=SeqOfEnvironments)
OptSeqOfEnvironments = SeqOfEnvironments | None
OptSeqOfEnvironmentsT = TypeVar("OptSeqOfEnvironmentsT", bound=OptSeqOfEnvironments)
