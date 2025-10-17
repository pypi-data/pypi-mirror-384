from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Sequence, TypeVar
from maleo.types.string import ListOfStrs


class BloodType(StrEnum):
    A = "a"
    B = "b"
    AB = "ab"
    O = "o"  # noqa: E741

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


BloodTypeT = TypeVar("BloodTypeT", bound=BloodType)
OptBloodType = BloodType | None
OptBloodTypeT = TypeVar("OptBloodTypeT", bound=OptBloodType)


class BloodTypeMixin(BaseModel, Generic[OptBloodTypeT]):
    blood_type: Annotated[OptBloodTypeT, Field(..., description="Blood Type")]


ListOfBloodTypes = list[BloodType]
ListOfBloodTypesT = TypeVar("ListOfBloodTypesT", bound=ListOfBloodTypes)
OptListOfBloodTypes = ListOfBloodTypes | None
OptListOfBloodTypesT = TypeVar("OptListOfBloodTypesT", bound=OptListOfBloodTypes)


class BloodTypesMixin(BaseModel, Generic[OptListOfBloodTypesT]):
    blood_types: Annotated[OptListOfBloodTypesT, Field(..., description="Blood Types")]


SeqOfBloodTypes = Sequence[BloodType]
SeqOfBloodTypesT = TypeVar("SeqOfBloodTypesT", bound=SeqOfBloodTypes)
OptSeqOfBloodTypes = SeqOfBloodTypes | None
OptSeqOfBloodTypesT = TypeVar("OptSeqOfBloodTypesT", bound=OptSeqOfBloodTypes)


class Gender(StrEnum):
    UNDISCLOSED = "undisclosed"
    FEMALE = "female"
    MALE = "male"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


GenderT = TypeVar("GenderT", bound=Gender)
OptGender = Gender | None
OptGenderT = TypeVar("OptGenderT", bound=OptGender)


class GenderMixin(BaseModel, Generic[OptGenderT]):
    gender: Annotated[OptGenderT, Field(..., description="Gender")]


ListOfGenders = list[Gender]
ListOfGendersT = TypeVar("ListOfGendersT", bound=ListOfGenders)
OptListOfGenders = ListOfGenders | None
OptListOfGendersT = TypeVar("OptListOfGendersT", bound=OptListOfGenders)


class GendersMixin(BaseModel, Generic[OptListOfGendersT]):
    genders: Annotated[OptListOfGendersT, Field(..., description="Genders")]


SeqOfGenders = Sequence[Gender]
SeqOfGendersT = TypeVar("SeqOfGendersT", bound=SeqOfGenders)
OptSeqOfGenders = SeqOfGenders | None
OptSeqOfGendersT = TypeVar("OptSeqOfGendersT", bound=OptSeqOfGenders)
