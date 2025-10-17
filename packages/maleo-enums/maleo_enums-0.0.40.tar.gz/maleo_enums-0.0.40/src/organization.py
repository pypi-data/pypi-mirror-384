from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Sequence, TypeVar
from maleo.types.string import ListOfStrs


class OrganizationType(StrEnum):
    APPLICATION = "application"
    BRANCH = "branch"
    CLIENT = "client"
    CLINIC = "clinic"
    CORPORATION = "corporation"
    DEPARTMENT = "department"
    DIVISION = "division"
    GOVERNMENT = "government"
    HOSPITAL_SYSTEM = "hospital_system"
    HOSPITAL = "hospital"
    INSURANCE_PROVIDER = "insurance_provider"
    INTERNAL = "internal"
    LABORATORY = "laboratory"
    MEDICAL_GROUP = "organization_group"
    NETWORK = "network"
    PARTNER = "partner"
    PHARMACY = "pharmacy"
    PRIMARY_HEALTH_CARE = "primary_health_care"
    PUBLIC_HEALTH_AGENCY = "public_health_agency"
    REGIONAL_OFFICE = "regional_office"
    REGULAR = "regular"
    RESEARCH_INSTITUTE = "research_institute"
    SUBSIDIARY = "subsidiary"
    THIRD_PARTY_ADMINISTRATOR = "third_party_administrator"
    UNIT = "unit"
    VENDOR = "vendor"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OrganizationTypeT = TypeVar("OrganizationTypeT", bound=OrganizationType)
OptOrganizationType = OrganizationType | None
OptOrganizationTypeT = TypeVar("OptOrganizationTypeT", bound=OptOrganizationType)


class SimpleOrganizationTypeMixin(BaseModel, Generic[OptOrganizationTypeT]):
    type: Annotated[OptOrganizationTypeT, Field(..., description="Organization Type")]


class FullOrganizationTypeMixin(BaseModel, Generic[OptOrganizationTypeT]):
    organization_type: Annotated[
        OptOrganizationTypeT, Field(..., description="Organization Type")
    ]


ListOfOrganizationTypes = list[OrganizationType]
ListOfOrganizationTypesT = TypeVar(
    "ListOfOrganizationTypesT", bound=ListOfOrganizationTypes
)
OptListOfOrganizationTypes = ListOfOrganizationTypes | None
OptListOfOrganizationTypesT = TypeVar(
    "OptListOfOrganizationTypesT", bound=OptListOfOrganizationTypes
)


class SimpleOrganizationTypesMixin(BaseModel, Generic[OptListOfOrganizationTypesT]):
    types: Annotated[
        OptListOfOrganizationTypesT, Field(..., description="Organization Types")
    ]


class FullOrganizationTypesMixin(BaseModel, Generic[OptListOfOrganizationTypesT]):
    organization_types: Annotated[
        OptListOfOrganizationTypesT, Field(..., description="Organization Types")
    ]


SeqOfOrganizationTypes = Sequence[OrganizationType]
SeqOfOrganizationTypesT = TypeVar(
    "SeqOfOrganizationTypesT", bound=SeqOfOrganizationTypes
)
OptSeqOfOrganizationTypes = SeqOfOrganizationTypes | None
OptSeqOfOrganizationTypesT = TypeVar(
    "OptSeqOfOrganizationTypesT", bound=OptSeqOfOrganizationTypes
)


class OrganizationRelation(StrEnum):
    AFFILIATE = "affiliate"
    APPLICATION = "application"
    BRANCH = "branch"
    CLIENT = "client"
    DEPARTMENT = "department"
    DIVISION = "division"
    NETWORK_MEMBER = "network_member"
    PARENT = "parent"
    PARTNER = "partner"
    SUBSIDIARY = "subsidiary"
    VENDOR = "vendor"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OrganizationRelationT = TypeVar("OrganizationRelationT", bound=OrganizationRelation)
OptOrganizationRelation = OrganizationRelation | None
OptOrganizationRelationT = TypeVar(
    "OptOrganizationRelationT", bound=OptOrganizationRelation
)


class SimpleOrganizationRelationMixin(BaseModel, Generic[OptOrganizationRelationT]):
    relation: Annotated[
        OptOrganizationRelationT, Field(..., description="Organization Relation")
    ]


class FullOrganizationRelationMixin(BaseModel, Generic[OptOrganizationRelationT]):
    organization_relation: Annotated[
        OptOrganizationRelationT, Field(..., description="Organization Relation")
    ]


ListOfOrganizationRelations = list[OrganizationRelation]
ListOfOrganizationRelationsT = TypeVar(
    "ListOfOrganizationRelationsT", bound=ListOfOrganizationRelations
)
OptListOfOrganizationRelations = ListOfOrganizationRelations | None
OptListOfOrganizationRelationsT = TypeVar(
    "OptListOfOrganizationRelationsT", bound=OptListOfOrganizationRelations
)


class SimpleOrganizationRelationsMixin(
    BaseModel, Generic[OptListOfOrganizationRelationsT]
):
    relations: Annotated[
        OptListOfOrganizationRelationsT,
        Field(..., description="Organization Relations"),
    ]


class FullOrganizationRelationsMixin(
    BaseModel, Generic[OptListOfOrganizationRelationsT]
):
    organization_relations: Annotated[
        OptListOfOrganizationRelationsT,
        Field(..., description="Organization Relations"),
    ]


SeqOfOrganizationRelations = Sequence[OrganizationRelation]
SeqOfOrganizationRelationsT = TypeVar(
    "SeqOfOrganizationRelationsT", bound=SeqOfOrganizationRelations
)
OptSeqOfOrganizationRelations = SeqOfOrganizationRelations | None
OptSeqOfOrganizationRelationsT = TypeVar(
    "OptSeqOfOrganizationRelationsT", bound=OptSeqOfOrganizationRelations
)


class OrganizationRole(StrEnum):
    OWNER = "owner"
    ADMINISTRATOR = "administrator"
    USER = "user"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OrganizationRoleT = TypeVar("OrganizationRoleT", bound=OrganizationRole)
OptOrganizationRole = OrganizationRole | None
OptOrganizationRoleT = TypeVar("OptOrganizationRoleT", bound=OptOrganizationRole)


class SimpleOrganizationRoleMixin(BaseModel, Generic[OptOrganizationRoleT]):
    role: Annotated[OptOrganizationRoleT, Field(..., description="Organization Role")]


class FullOrganizationRoleMixin(BaseModel, Generic[OptOrganizationRoleT]):
    organization_role: Annotated[
        OptOrganizationRoleT, Field(..., description="Organization Role")
    ]


ListOfOrganizationRoles = list[OrganizationRole]
ListOfOrganizationRolesT = TypeVar(
    "ListOfOrganizationRolesT", bound=ListOfOrganizationRoles
)
OptListOfOrganizationRoles = ListOfOrganizationRoles | None
OptListOfOrganizationRolesT = TypeVar(
    "OptListOfOrganizationRolesT", bound=OptListOfOrganizationRoles
)


class SimpleOrganizationRolesMixin(BaseModel, Generic[OptListOfOrganizationRolesT]):
    roles: Annotated[
        OptListOfOrganizationRolesT, Field(..., description="Organization Roles")
    ]


class FullOrganizationRolesMixin(BaseModel, Generic[OptListOfOrganizationRolesT]):
    organization_roles: Annotated[
        OptListOfOrganizationRolesT, Field(..., description="Organization Roles")
    ]


SeqOfOrganizationRoles = Sequence[OrganizationRole]
SeqOfOrganizationRolesT = TypeVar(
    "SeqOfOrganizationRolesT", bound=SeqOfOrganizationRoles
)
OptSeqOfOrganizationRoles = SeqOfOrganizationRoles | None
OptSeqOfOrganizationRolesT = TypeVar(
    "OptSeqOfOrganizationRolesT", bound=OptSeqOfOrganizationRoles
)
