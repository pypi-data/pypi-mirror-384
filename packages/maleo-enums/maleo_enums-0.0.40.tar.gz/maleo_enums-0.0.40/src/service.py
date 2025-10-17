from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Annotated, Generic, Sequence, TypeVar
from maleo.types.string import ListOfStrs


class ServiceType(StrEnum):
    BACKEND = "backend"
    FRONTEND = "frontend"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


ServiceTypeT = TypeVar("ServiceTypeT", bound=ServiceType)
OptServiceType = ServiceType | None
OptServiceTypeT = TypeVar("OptServiceTypeT", bound=OptServiceType)


class SimpleServiceTypeMixin(BaseModel, Generic[OptServiceTypeT]):
    type: Annotated[OptServiceTypeT, Field(..., description="Service Type")]


class FullServiceTypeMixin(BaseModel, Generic[OptServiceTypeT]):
    service_type: Annotated[OptServiceTypeT, Field(..., description="Service Type")]


ListOfServiceTypes = list[ServiceType]
ListOfServiceTypesT = TypeVar("ListOfServiceTypesT", bound=ListOfServiceTypes)
OptListOfServiceTypes = ListOfServiceTypes | None
OptListOfServiceTypesT = TypeVar("OptListOfServiceTypesT", bound=OptListOfServiceTypes)


class SimpleServiceTypesMixin(BaseModel, Generic[OptListOfServiceTypesT]):
    types: Annotated[OptListOfServiceTypesT, Field(..., description="Service Types")]


class FullServiceTypesMixin(BaseModel, Generic[OptListOfServiceTypesT]):
    service_types: Annotated[
        OptListOfServiceTypesT, Field(..., description="Service Types")
    ]


SeqOfServiceTypes = Sequence[ServiceType]
SeqOfServiceTypesT = TypeVar("SeqOfServiceTypesT", bound=SeqOfServiceTypes)
OptSeqOfServiceTypes = SeqOfServiceTypes | None
OptSeqOfServiceTypesT = TypeVar("OptSeqOfServiceTypesT", bound=OptSeqOfServiceTypes)


class ServiceCategory(StrEnum):
    CORE = "core"
    AI = "ai"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


ServiceCategoryT = TypeVar("ServiceCategoryT", bound=ServiceCategory)
OptServiceCategory = ServiceCategory | None
OptServiceCategoryT = TypeVar("OptServiceCategoryT", bound=OptServiceCategory)


class SimpleServiceCategoryMixin(BaseModel, Generic[OptServiceCategoryT]):
    category: Annotated[OptServiceCategoryT, Field(..., description="Service Category")]


class FullServiceCategoryMixin(BaseModel, Generic[OptServiceCategoryT]):
    service_category: Annotated[
        OptServiceCategoryT, Field(..., description="Service Category")
    ]


ListOfServiceCategories = list[ServiceCategory]
ListOfServiceCategoriesT = TypeVar(
    "ListOfServiceCategoriesT", bound=ListOfServiceCategories
)
OptListOfServiceCategories = ListOfServiceCategories | None
OptListOfServiceCategoriesT = TypeVar(
    "OptListOfServiceCategoriesT", bound=OptListOfServiceCategories
)


class SimpleServiceCategoriesMixin(BaseModel, Generic[OptListOfServiceCategoriesT]):
    categories: Annotated[
        OptListOfServiceCategoriesT, Field(..., description="Service Categories")
    ]


class FullServiceCategoriesMixin(BaseModel, Generic[OptListOfServiceCategoriesT]):
    service_categories: Annotated[
        OptListOfServiceCategoriesT, Field(..., description="Service Categories")
    ]


SeqOfServiceCategories = Sequence[ServiceCategory]
SeqOfServiceCategoriesT = TypeVar(
    "SeqOfServiceCategoriesT", bound=SeqOfServiceCategories
)
OptSeqOfServiceCategories = SeqOfServiceCategories | None
OptSeqOfServiceCategoriesT = TypeVar(
    "OptSeqOfServiceCategoriesT", bound=OptSeqOfServiceCategories
)


class ShortServiceKey(StrEnum):
    STUDIO = "studio"
    NEXUS = "nexus"
    TELEMETRY = "telemetry"
    METADATA = "metadata"
    IDENTITY = "identity"
    ACCESS = "access"
    WORKSHOP = "workshop"
    RESEARCH = "research"
    REGISTRY = "registry"
    SOAPIE = "soapie"
    MEDIX = "medix"
    DICOM = "dicom"
    SCRIBE = "scribe"
    CDS = "cds"
    IMAGING = "imaging"
    MCU = "mcu"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


ShortServiceKeyT = TypeVar("ShortServiceKeyT", bound=ShortServiceKey)
OptShortServiceKey = ShortServiceKey | None
OptShortServiceKeyT = TypeVar("OptShortServiceKeyT", bound=OptShortServiceKey)


class SimpleShortServiceKeyMixin(BaseModel, Generic[OptShortServiceKeyT]):
    key: Annotated[OptShortServiceKeyT, Field(..., description="Service Key")]


class FullShortServiceKeyMixin(BaseModel, Generic[OptShortServiceKeyT]):
    service_key: Annotated[OptShortServiceKeyT, Field(..., description="Service Key")]


ListOfShortServiceKeys = list[ShortServiceKey]
ListOfShortServiceKeysT = TypeVar(
    "ListOfShortServiceKeysT", bound=ListOfShortServiceKeys
)
OptListOfShortServiceKeys = ListOfShortServiceKeys | None
OptListOfShortServiceKeysT = TypeVar(
    "OptListOfShortServiceKeysT", bound=OptListOfShortServiceKeys
)


class SimpleShortServiceKeysMixin(BaseModel, Generic[OptListOfShortServiceKeysT]):
    keys: Annotated[OptListOfShortServiceKeysT, Field(..., description="Service Keys")]


class FullShortServiceKeysMixin(BaseModel, Generic[OptListOfShortServiceKeysT]):
    service_keys: Annotated[
        OptListOfShortServiceKeysT, Field(..., description="Service Keys")
    ]


SeqOfShortServiceKeys = Sequence[ShortServiceKey]
SeqOfShortServiceKeysT = TypeVar("SeqOfShortServiceKeysT", bound=SeqOfShortServiceKeys)
OptSeqOfShortServiceKeys = SeqOfShortServiceKeys | None
OptSeqOfShortServiceKeysT = TypeVar(
    "OptSeqOfShortServiceKeysT", bound=OptSeqOfShortServiceKeys
)


class ServiceKey(StrEnum):
    STUDIO = "maleo-studio"
    NEXUS = "maleo-nexus"
    TELEMETRY = "maleo-telemetry"
    METADATA = "maleo-metadata"
    IDENTITY = "maleo-identity"
    ACCESS = "maleo-access"
    WORKSHOP = "maleo-workshop"
    RESEARCH = "maleo-research"
    REGISTRY = "maleo-registry"
    SOAPIE = "maleo-soapie"
    MEDIX = "maleo-medix"
    DICOM = "maleo-dicom"
    SCRIBE = "maleo-scribe"
    CDS = "maleo-cds"
    IMAGING = "maleo-imaging"
    MCU = "maleo-mcu"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


ServiceKeyT = TypeVar("ServiceKeyT", bound=ServiceKey)
OptServiceKey = ServiceKey | None
OptServiceKeyT = TypeVar("OptServiceKeyT", bound=OptServiceKey)


class SimpleServiceKeyMixin(BaseModel, Generic[OptServiceKeyT]):
    key: Annotated[OptServiceKeyT, Field(..., description="Service Key")]


class FullServiceKeyMixin(BaseModel, Generic[OptServiceKeyT]):
    service_key: Annotated[OptServiceKeyT, Field(..., description="Service Key")]


ListOfServiceKeys = list[ServiceKey]
ListOfServiceKeysT = TypeVar("ListOfServiceKeysT", bound=ListOfServiceKeys)
OptListOfServiceKeys = ListOfServiceKeys | None
OptListOfServiceKeysT = TypeVar("OptListOfServiceKeysT", bound=OptListOfServiceKeys)


class SimpleServiceKeysMixin(BaseModel, Generic[OptListOfServiceKeysT]):
    keys: Annotated[OptListOfServiceKeysT, Field(..., description="Service Keys")]


class FullServiceKeysMixin(BaseModel, Generic[OptListOfServiceKeysT]):
    service_keys: Annotated[
        OptListOfServiceKeysT, Field(..., description="Service Keys")
    ]


SeqOfServiceKeys = Sequence[ServiceKey]
SeqOfServiceKeysT = TypeVar("SeqOfServiceKeysT", bound=SeqOfServiceKeys)
OptSeqOfServiceKeys = SeqOfServiceKeys | None
OptSeqOfServiceKeysT = TypeVar("OptSeqOfServiceKeysT", bound=OptSeqOfServiceKeys)


class ShortServiceName(StrEnum):
    STUDIO = "Studio"
    NEXUS = "Nexus"
    TELEMETRY = "Telemetry"
    METADATA = "Metadata"
    IDENTITY = "Identity"
    ACCESS = "Access"
    WORKSHOP = "Workshop"
    RESEARCH = "Research"
    REGISTRY = "Registry"
    SOAPIE = "SOAPIE"
    MEDIX = "Medix"
    DICOM = "DICON"
    SCRIBE = "Scribe"
    CDS = "CDS"
    IMAGING = "Imaging"
    MCU = "MCU"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


ShortServiceNameT = TypeVar("ShortServiceNameT", bound=ShortServiceName)
OptShortServiceName = ShortServiceName | None
OptShortServiceNameT = TypeVar("OptShortServiceNameT", bound=OptShortServiceName)


class SimpleShortServiceNameMixin(BaseModel, Generic[OptShortServiceNameT]):
    name: Annotated[OptShortServiceNameT, Field(..., description="Service Name")]


class FullShortServiceNameMixin(BaseModel, Generic[OptShortServiceNameT]):
    service_name: Annotated[
        OptShortServiceNameT, Field(..., description="Service Name")
    ]


ListOfShortServiceNames = list[ShortServiceName]
ListOfShortServiceNamesT = TypeVar(
    "ListOfShortServiceNamesT", bound=ListOfShortServiceNames
)
OptListOfShortServiceNames = ListOfShortServiceNames | None
OptListOfShortServiceNamesT = TypeVar(
    "OptListOfShortServiceNamesT", bound=OptListOfShortServiceNames
)


class SimpleShortServiceNamesMixin(BaseModel, Generic[OptListOfShortServiceNamesT]):
    names: Annotated[
        OptListOfShortServiceNamesT, Field(..., description="Service Names")
    ]


class FullShortServiceNamesMixin(BaseModel, Generic[OptListOfShortServiceNamesT]):
    service_names: Annotated[
        OptListOfShortServiceNamesT, Field(..., description="Service Names")
    ]


SeqOfShortServiceNames = Sequence[ShortServiceName]
SeqOfShortServiceNamesT = TypeVar(
    "SeqOfShortServiceNamesT", bound=SeqOfShortServiceNames
)
OptSeqOfShortServiceNames = SeqOfShortServiceNames | None
OptSeqOfShortServiceNamesT = TypeVar(
    "OptSeqOfShortServiceNamesT", bound=OptSeqOfShortServiceNames
)


class ServiceName(StrEnum):
    STUDIO = "MaleoStudio"
    NEXUS = "MaleoNexus"
    TELEMETRY = "MaleoTelemetry"
    METADATA = "MaleoMetadata"
    IDENTITY = "MaleoIdentity"
    ACCESS = "MaleoAccess"
    WORKSHOP = "MaleoWorkshop"
    RESEARCH = "MaleoResearch"
    REGISTRY = "MaleoRegistry"
    SOAPIE = "MaleoSOAPIE"
    MEDIX = "MaleoMedix"
    DICOM = "MaleoDICON"
    SCRIBE = "MaleoScribe"
    CDS = "MaleoCDS"
    IMAGING = "MaleoImaging"
    MCU = "MaleoMCU"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


ServiceNameT = TypeVar("ServiceNameT", bound=ServiceName)
OptServiceName = ServiceName | None
OptServiceNameT = TypeVar("OptServiceNameT", bound=OptServiceName)


class SimpleServiceNameMixin(BaseModel, Generic[OptServiceNameT]):
    name: Annotated[OptServiceNameT, Field(..., description="Service Name")]


class FullServiceNameMixin(BaseModel, Generic[OptServiceNameT]):
    service_name: Annotated[OptServiceNameT, Field(..., description="Service Name")]


ListOfServiceNames = list[ServiceName]
ListOfServiceNamesT = TypeVar("ListOfServiceNamesT", bound=ListOfServiceNames)
OptListOfServiceNames = ListOfServiceNames | None
OptListOfServiceNamesT = TypeVar("OptListOfServiceNamesT", bound=OptListOfServiceNames)


class SimpleServiceNamesMixin(BaseModel, Generic[OptListOfServiceNamesT]):
    names: Annotated[OptListOfServiceNamesT, Field(..., description="Service Names")]


class FullServiceNamesMixin(BaseModel, Generic[OptListOfServiceNamesT]):
    service_names: Annotated[
        OptListOfServiceNamesT, Field(..., description="Service Names")
    ]


SeqOfServiceNames = Sequence[ServiceName]
SeqOfServiceNamesT = TypeVar("SeqOfServiceNamesT", bound=SeqOfServiceNames)
OptSeqOfServiceNames = SeqOfServiceNames | None
OptSeqOfServiceNamesT = TypeVar("OptSeqOfServiceNamesT", bound=OptSeqOfServiceNames)
