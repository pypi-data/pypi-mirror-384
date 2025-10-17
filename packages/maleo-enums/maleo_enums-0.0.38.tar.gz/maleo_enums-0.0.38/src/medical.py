from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Sequence, TypeVar
from maleo.types.string import ListOfStrs


class MedicalRole(StrEnum):
    # Level 1: Director category
    DIRECTOR = "director"
    PRESIDENT = "president"
    VICE_PRESIDENT = "vice_president"
    SECRETARY = "secretary"
    TREASURER = "treasurer"
    # Level 1: Management category
    HEAD = "head"
    CEO = "ceo"
    COO = "coo"
    CFO = "cfo"
    CCO = "cco"
    # Level 1: Administration category
    ADMINISTRATOR = "administrator"
    ADMISSION = "admission"
    CASHIER = "cashier"
    CASEMIX = "casemix"
    MEDICAL_RECORD = "medical_record"
    # Level 1: Medical category
    DOCTOR = "doctor"
    NURSE = "nurse"
    MIDWIFE = "midwife"
    # Level 2: Doctor's specialization
    INTERNIST = "internist"
    PEDIATRICIAN = "pediatrician"
    OBSTETRICIAN = "obstetrician"
    GYNECOLOGIST = "gynecologist"
    OBGYN = "obgyn"
    PSYCHIATRIST = "psychiatrist"
    DERMATOLOGIST = "dermatologist"
    NEUROLOGIST = "neurologist"
    CARDIOLOGIST = "cardiologist"
    OPHTHALMOLOGIST = "ophthalmologist"
    RADIOLOGIST = "radiologist"
    ANESTHESIOLOGIST = "anesthesiologist"
    HEMATOLOGIST = "hematologist"
    ENDOCRINOLOGIST = "endocrinologist"
    GASTROENTEROLOGIST = "gastroenterologist"
    NEPHROLOGIST = "nephrologist"
    UROLOGIST = "urologist"
    PULMONOLOGIST = "pulmonologist"
    RHEUMATOLOGIST = "rheumatologist"
    SURGEON = "surgeon"
    # Level 3: Surgeon's specialization
    ORTHOPEDIC_SURGEON = "orthopedic_surgeon"
    # Level 2: Nurse's specialization
    SCRUB_NURSE = "scrub_nurse"
    TRIAGE_NURSE = "triage_nurse"
    ICU_NURSE = "icu_nurse"
    NICU_NURSE = "nicu_nurse"
    OR_NURSE = "or_nurse"
    ER_NURSE = "er_nurse"
    # Level 1: Technical category
    TECHNICIAN = "technician"
    LABORATORY_TECHNICIAN = "laboratory_technician"
    RADIOGRAPHER = "radiographer"
    SONOGRAPHER = "sonographer"
    # Level 1: Therapeutic category
    THERAPIST = "therapist"
    PHYSIOTHERAPIST = "physiotherapist"
    OCCUPATIONAL_THERAPIST = "occupational_therapist"
    SPEECH_THERAPIST = "speech_therapist"
    PSYCHOLOGIST = "psychologist"
    # Level 1: Support category
    PHARMACIST = "pharmacist"
    NUTRITIONIST = "nutritionist"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


MedicalRoleT = TypeVar("MedicalRoleT", bound=MedicalRole)
OptMedicalRole = MedicalRole | None
OptMedicalRoleT = TypeVar("OptMedicalRoleT", bound=OptMedicalRole)


class SimpleMedicalRoleMixin(BaseModel, Generic[OptMedicalRoleT]):
    role: Annotated[OptMedicalRoleT, Field(..., description="Medical Role")]


class FullMedicalRoleMixin(BaseModel, Generic[OptMedicalRoleT]):
    medical_role: Annotated[OptMedicalRoleT, Field(..., description="Medical Role")]


ListOfMedicalRoles = list[MedicalRole]
ListOfMedicalRolesT = TypeVar("ListOfMedicalRolesT", bound=ListOfMedicalRoles)
OptListOfMedicalRoles = ListOfMedicalRoles | None
OptListOfMedicalRolesT = TypeVar("OptListOfMedicalRolesT", bound=OptListOfMedicalRoles)


class SimpleMedicalRolesMixin(BaseModel, Generic[OptListOfMedicalRolesT]):
    roles: Annotated[OptListOfMedicalRolesT, Field(..., description="Medical Roles")]


class FullMedicalRolesMixin(BaseModel, Generic[OptListOfMedicalRolesT]):
    medical_roles: Annotated[
        OptListOfMedicalRolesT, Field(..., description="Medical Roles")
    ]


SeqOfMedicalRoles = Sequence[MedicalRole]
SeqOfMedicalRolesT = TypeVar("SeqOfMedicalRolesT", bound=SeqOfMedicalRoles)
OptSeqOfMedicalRoles = SeqOfMedicalRoles | None
OptSeqOfMedicalRolesT = TypeVar("OptSeqOfMedicalRolesT", bound=OptSeqOfMedicalRoles)


class MedicalService(StrEnum):
    EMERGENCY = "emergency"
    INPATIENT = "inpatient"
    INTENSIVE = "intensive"
    OUTPATIENT = "outpatient"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


MedicalServiceT = TypeVar("MedicalServiceT", bound=MedicalService)
OptMedicalService = MedicalService | None
OptMedicalServiceT = TypeVar("OptMedicalServiceT", bound=OptMedicalService)


class SimpleMedicalServiceMixin(BaseModel, Generic[OptMedicalServiceT]):
    service: Annotated[OptMedicalServiceT, Field(..., description="Medical Service")]


class FullMedicalServiceMixin(BaseModel, Generic[OptMedicalServiceT]):
    medical_service: Annotated[
        OptMedicalServiceT, Field(..., description="Medical Service")
    ]


ListOfMedicalServices = list[MedicalService]
ListOfMedicalServicesT = TypeVar("ListOfMedicalServicesT", bound=ListOfMedicalServices)
OptListOfMedicalServices = ListOfMedicalServices | None
OptListOfMedicalServicesT = TypeVar(
    "OptListOfMedicalServicesT", bound=OptListOfMedicalServices
)


class SimpleMedicalServicesMixin(BaseModel, Generic[OptListOfMedicalServicesT]):
    services: Annotated[
        OptListOfMedicalServicesT, Field(..., description="Medical Services")
    ]


class FullMedicalServicesMixin(BaseModel, Generic[OptListOfMedicalServicesT]):
    medical_services: Annotated[
        OptListOfMedicalServicesT, Field(..., description="Medical Services")
    ]


SeqOfMedicalServices = Sequence[MedicalService]
SeqOfMedicalServicesT = TypeVar("SeqOfMedicalServicesT", bound=SeqOfMedicalServices)
OptSeqOfMedicalServices = SeqOfMedicalServices | None
OptSeqOfMedicalServicesT = TypeVar(
    "OptSeqOfMedicalServicesT", bound=OptSeqOfMedicalServices
)
