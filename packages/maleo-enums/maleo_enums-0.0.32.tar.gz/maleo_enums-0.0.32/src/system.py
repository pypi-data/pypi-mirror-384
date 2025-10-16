from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Sequence, TypeVar
from maleo.types.string import ListOfStrs


class SystemRole(StrEnum):
    ADMINISTRATOR = "administrator"
    ANALYST = "analyst"
    ENGINEER = "engineer"
    GUEST = "guest"
    MANAGER = "manager"
    OFFICER = "officer"
    OPERATIONS = "operations"
    SECURITY = "security"
    SUPPORT = "support"
    TESTER = "tester"
    USER = "user"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


SystemRoleT = TypeVar("SystemRoleT", bound=SystemRole)
OptSystemRole = SystemRole | None
OptSystemRoleT = TypeVar("OptSystemRoleT", bound=OptSystemRole)


class SimpleSystemRoleMixin(BaseModel, Generic[OptSystemRoleT]):
    role: Annotated[OptSystemRoleT, Field(..., description="System Role")]


class FullSystemRoleMixin(BaseModel, Generic[OptSystemRoleT]):
    system_role: Annotated[OptSystemRoleT, Field(..., description="System Role")]


ListOfSystemRoles = list[SystemRole]
ListOfSystemRolesT = TypeVar("ListOfSystemRolesT", bound=ListOfSystemRoles)
OptListOfSystemRoles = ListOfSystemRoles | None
OptListOfSystemRolesT = TypeVar("OptListOfSystemRolesT", bound=OptListOfSystemRoles)


class SimpleSystemRolesMixin(BaseModel, Generic[OptListOfSystemRolesT]):
    roles: Annotated[OptListOfSystemRolesT, Field(..., description="System Roles")]


class FullSystemRolesMixin(BaseModel, Generic[OptListOfSystemRolesT]):
    system_roles: Annotated[
        OptListOfSystemRolesT, Field(..., description="System Roles")
    ]


SeqOfSystemRoles = Sequence[SystemRole]
SeqOfSystemRolesT = TypeVar("SeqOfSystemRolesT", bound=SeqOfSystemRoles)
OptSeqOfSystemRoles = SeqOfSystemRoles | None
OptSeqOfSystemRolesT = TypeVar("OptSeqOfSystemRolesT", bound=OptSeqOfSystemRoles)
