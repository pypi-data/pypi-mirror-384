from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Sequence, TypeVar
from maleo.types.string import ListOfStrs


class UserType(StrEnum):
    PROXY = "proxy"
    REGULAR = "regular"
    SERVICE = "service"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


UserTypeT = TypeVar("UserTypeT", bound=UserType)
OptUserType = UserType | None
OptUserTypeT = TypeVar("OptUserTypeT", bound=OptUserType)


class SimpleUserTypeMixin(BaseModel, Generic[OptUserTypeT]):
    type: Annotated[OptUserTypeT, Field(..., description="User Type")]


class FullUserTypeMixin(BaseModel, Generic[OptUserTypeT]):
    user_type: Annotated[OptUserTypeT, Field(..., description="User Type")]


ListOfUserTypes = list[UserType]
ListOfUserTypesT = TypeVar("ListOfUserTypesT", bound=ListOfUserTypes)
OptListOfUserTypes = ListOfUserTypes | None
OptListOfUserTypesT = TypeVar("OptListOfUserTypesT", bound=OptListOfUserTypes)


class SimpleUserTypesMixin(BaseModel, Generic[OptListOfUserTypesT]):
    types: Annotated[OptListOfUserTypesT, Field(..., description="User Types")]


class FullUserTypesMixin(BaseModel, Generic[OptListOfUserTypesT]):
    user_types: Annotated[OptListOfUserTypesT, Field(..., description="User Types")]


SeqOfUserTypes = Sequence[UserType]
SeqOfUserTypesT = TypeVar("SeqOfUserTypesT", bound=SeqOfUserTypes)
OptSeqOfUserTypes = SeqOfUserTypes | None
OptSeqOfUserTypesT = TypeVar("OptSeqOfUserTypesT", bound=OptSeqOfUserTypes)
