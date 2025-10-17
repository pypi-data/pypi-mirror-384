from pydantic import BaseModel, Field
from typing import Generic, Literal, Sequence, Type, TypeVar, overload
from uuid import UUID
from maleo.enums.medical import MedicalService, ListOfMedicalServices
from maleo.enums.status import (
    DataStatus,
    ListOfDataStatuses,
    SimpleDataStatusMixin,
    FULL_DATA_STATUSES,
)
from maleo.schemas.mixins.filter import convert as convert_filter
from maleo.schemas.mixins.general import Order
from maleo.schemas.mixins.identity import (
    DataIdentifier,
    IdentifierTypeValue,
    Ids,
    UUIDs,
    Keys,
    Names,
)
from maleo.schemas.mixins.sort import convert as convert_sort
from maleo.schemas.mixins.timestamp import LifecycleTimestamp, DataTimestamp
from maleo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
    StatusUpdateParameter as BaseStatusUpdateParameter,
    DeleteSingleParameter as BaseDeleteSingleParameter,
)
from maleo.types.dict import StrToAnyDict
from maleo.types.integer import OptInt, OptListOfInts
from maleo.types.string import OptListOfStrs, OptStr
from maleo.types.uuid import OptListOfUUIDs
from ..enums.medical_service import IdentifierType
from ..mixins.medical_service import Key, Name
from ..types.medical_service import IdentifierValueType


class CreateData(Name[str], Key, Order[OptInt]):
    pass


class CreateDataMixin(BaseModel):
    data: CreateData = Field(..., description="Create data")


class CreateParameter(
    CreateDataMixin,
):
    pass


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    Names[OptListOfStrs],
    Keys[OptListOfStrs],
    UUIDs[OptListOfUUIDs],
    Ids[OptListOfInts],
):
    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "ids",
            "uuids",
            "statuses",
            "keys",
            "names",
            "search",
            "page",
            "limit",
            "granularity",
            "use_cache",
        }

    def to_query_params(self) -> StrToAnyDict:
        params = self.model_dump(
            mode="json", include=self._query_param_fields, exclude_none=True
        )
        params["filters"] = convert_filter(self.date_filters)
        params["sorts"] = convert_sort(self.sort_columns)
        params = {k: v for k, v in params.items()}
        return params


class ReadSingleParameter(BaseReadSingleParameter[IdentifierType, IdentifierValueType]):
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.KEY, IdentifierType.NAME],
        identifier_value: str,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter":
        return cls(
            identifier_type=identifier_type,
            identifier_value=identifier_value,
            statuses=statuses,
            use_cache=use_cache,
        )

    def to_query_params(self) -> StrToAnyDict:
        return self.model_dump(
            mode="json", include={"statuses", "use_cache"}, exclude_none=True
        )


class FullUpdateData(Name[str], Order[OptInt]):
    pass


class PartialUpdateData(Name[OptStr], Order[OptInt]):
    pass


UpdateDataT = TypeVar("UpdateDataT", FullUpdateData, PartialUpdateData)


class UpdateDataMixin(BaseModel, Generic[UpdateDataT]):
    data: UpdateDataT = Field(..., description="Update data")


class UpdateParameter(
    UpdateDataMixin[UpdateDataT],
    IdentifierTypeValue[
        IdentifierType,
        IdentifierValueType,
    ],
    Generic[UpdateDataT],
):
    pass


class StatusUpdateParameter(
    BaseStatusUpdateParameter[IdentifierType, IdentifierValueType],
):
    pass


class DeleteSingleParameter(
    BaseDeleteSingleParameter[IdentifierType, IdentifierValueType]
):
    pass


class BaseMedicalServiceSchema(
    Name[str],
    Key,
    Order[OptInt],
):
    pass


class StandardMedicalServiceSchema(
    BaseMedicalServiceSchema,
    SimpleDataStatusMixin[DataStatus],
    LifecycleTimestamp,
    DataIdentifier,
):
    pass


OptStandardMedicalServiceSchema = StandardMedicalServiceSchema | None
ListOfStandardMedicalServiceSchemas = list[StandardMedicalServiceSchema]
SeqOfStandardMedicalServiceSchemas = Sequence[StandardMedicalServiceSchema]

KeyOrStandardSchema = MedicalService | StandardMedicalServiceSchema
OptKeyOrStandardSchema = KeyOrStandardSchema | None


class FullMedicalServiceSchema(
    BaseMedicalServiceSchema,
    SimpleDataStatusMixin[DataStatus],
    DataTimestamp,
    DataIdentifier,
):
    pass


OptFullMedicalServiceSchema = FullMedicalServiceSchema | None
ListOfFullMedicalServiceSchemas = list[FullMedicalServiceSchema]
SeqOfFullMedicalServiceSchemas = Sequence[FullMedicalServiceSchema]

KeyOrFullSchema = MedicalService | FullMedicalServiceSchema
OptKeyOrFullSchema = KeyOrFullSchema | None


AnyMedicalServiceSchemaType = (
    Type[StandardMedicalServiceSchema] | Type[FullMedicalServiceSchema]
)


# User Type Schemas
AnyMedicalServiceSchema = StandardMedicalServiceSchema | FullMedicalServiceSchema
MedicalServiceSchemaT = TypeVar("MedicalServiceSchemaT", bound=AnyMedicalServiceSchema)

OptAnyMedicalServiceSchema = AnyMedicalServiceSchema | None
OptMedicalServiceSchemaT = TypeVar(
    "OptMedicalServiceSchemaT", bound=OptAnyMedicalServiceSchema
)

ListOfAnyMedicalServiceSchemas = (
    ListOfStandardMedicalServiceSchemas | ListOfFullMedicalServiceSchemas
)
ListOfAnyMedicalServiceSchemasT = TypeVar(
    "ListOfAnyMedicalServiceSchemasT", bound=ListOfAnyMedicalServiceSchemas
)

OptListOfAnyMedicalServiceSchemas = ListOfAnyMedicalServiceSchemas | None
OptListOfAnyMedicalServiceSchemasT = TypeVar(
    "OptListOfAnyMedicalServiceSchemasT", bound=OptListOfAnyMedicalServiceSchemas
)


# User Type key and Schemas
AnyMedicalService = MedicalService | AnyMedicalServiceSchema
AnyMedicalServiceT = TypeVar("AnyMedicalServiceT", bound=AnyMedicalService)

OptAnyMedicalService = AnyMedicalService | None
OptAnyMedicalServiceT = TypeVar("OptAnyMedicalServiceT", bound=OptAnyMedicalService)

ListOfAnyMedicalServices = ListOfMedicalServices | ListOfAnyMedicalServiceSchemas
ListOfAnyMedicalServicesT = TypeVar(
    "ListOfAnyMedicalServicesT", bound=ListOfAnyMedicalServices
)

OptListOfAnyMedicalServices = ListOfAnyMedicalServices | None
OptListOfAnyMedicalServicesT = TypeVar(
    "OptListOfAnyMedicalServicesT", bound=OptListOfAnyMedicalServices
)


class SimpleMedicalServiceMixin(BaseModel, Generic[OptAnyMedicalServiceT]):
    service: OptAnyMedicalServiceT = Field(..., description="Medical service")


class FullMedicalServiceMixin(BaseModel, Generic[OptAnyMedicalServiceT]):
    medical_service: OptAnyMedicalServiceT = Field(..., description="Medical service")


class SimpleMedicalServicesMixin(BaseModel, Generic[OptListOfAnyMedicalServicesT]):
    services: OptListOfAnyMedicalServicesT = Field(..., description="Medical services")


class FullMedicalServicesMixin(BaseModel, Generic[OptListOfAnyMedicalServicesT]):
    medical_services: OptListOfAnyMedicalServicesT = Field(
        ..., description="Medical services"
    )
