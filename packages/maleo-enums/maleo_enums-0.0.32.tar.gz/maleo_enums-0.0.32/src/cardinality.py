from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Sequence, TypeVar
from maleo.types.string import ListOfStrs


class Cardinality(StrEnum):
    MULTIPLE = "multiple"
    SINGLE = "single"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


CardinalityT = TypeVar("CardinalityT", bound=Cardinality)
OptCardinality = Cardinality | None
OptCardinalityT = TypeVar("OptCardinalityT", bound=OptCardinality)


class CardinalityMixin(BaseModel, Generic[OptCardinalityT]):
    cardinality: Annotated[OptCardinalityT, Field(..., description="Cardinality")]


ListOfCardinalities = list[Cardinality]
ListOfCardinalitiesT = TypeVar("ListOfCardinalitiesT", bound=ListOfCardinalities)
OptListOfCardinalities = ListOfCardinalities | None
OptListOfCardinalitiesT = TypeVar(
    "OptListOfCardinalitiesT", bound=OptListOfCardinalities
)


class CardinalitiesMixin(BaseModel, Generic[OptListOfCardinalitiesT]):
    cardinalities: Annotated[
        OptListOfCardinalitiesT, Field(..., description="Cardinalities")
    ]


SeqOfCardinalities = Sequence[Cardinality]
SeqOfCardinalitiesT = TypeVar("SeqOfCardinalitiesT", bound=SeqOfCardinalities)
OptSeqOfCardinalities = SeqOfCardinalities | None
OptSeqOfCardinalitiesT = TypeVar("OptSeqOfCardinalitiesT", bound=OptSeqOfCardinalities)


class Relationship(StrEnum):
    # One origin
    ONE_TO_ONE = "one_to_one"
    ONE_TO_OPTIONAL_ONE = "one_to_optional_one"
    ONE_TO_MANY = "one_to_many"
    ONE_TO_OPTIONAL_MANY = "one_to_optional_many"
    # Opt one origin
    OPTIONAL_ONE_TO_ONE = "optional_one_to_one"
    OPTIONAL_ONE_TO_OPTIONAL_ONE = "optional_one_to_optional_one"
    OPTIONAL_ONE_TO_MANY = "optional_one_to_many"
    OPTIONAL_ONE_TO_OPTIONAL_MANY = "optional_one_to_optional_many"
    # Many origin
    MANY_TO_ONE = "many_to_one"
    MANY_TO_OPTIONAL_ONE = "many_to_optional_one"
    MANY_TO_MANY = "many_to_many"
    MANY_TO_OPTIONAL_MANY = "many_to_optional_many"
    # Opt many origin
    OPTIONAL_MANY_TO_ONE = "optional_many_to_one"
    OPTIONAL_MANY_TO_OPTIONAL_ONE = "optional_many_to_optional_one"
    OPTIONAL_MANY_TO_MANY = "optional_many_to_many"
    OPTIONAL_MANY_TO_OPTIONAL_MANY = "optional_many_to_optional_many"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


RelationshipT = TypeVar("RelationshipT", bound=Relationship)
OptRelationship = Relationship | None
OptRelationshipT = TypeVar("OptRelationshipT", bound=OptRelationship)


class RelationshipMixin(BaseModel, Generic[OptRelationshipT]):
    relationship: Annotated[OptRelationshipT, Field(..., description="Relationship")]


ListOfRelationships = list[Relationship]
ListOfRelationshipsT = TypeVar("ListOfRelationshipsT", bound=ListOfRelationships)
OptListOfRelationships = ListOfRelationships | None
OptListOfRelationshipsT = TypeVar(
    "OptListOfRelationshipsT", bound=OptListOfRelationships
)


class RelationshipsMixin(BaseModel, Generic[OptListOfRelationshipsT]):
    relationships: Annotated[
        OptListOfRelationshipsT, Field(..., description="Relationships")
    ]


SeqOfRelationships = Sequence[Relationship]
SeqOfRelationshipsT = TypeVar("SeqOfRelationshipsT", bound=SeqOfRelationships)
OptSeqOfRelationships = SeqOfRelationships | None
OptSeqOfRelationshipsT = TypeVar("OptSeqOfRelationshipsT", bound=OptSeqOfRelationships)
