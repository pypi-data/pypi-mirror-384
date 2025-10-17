from pydantic import BaseModel, Field
from typing import Generic, Literal, Sequence, Type, TypeVar, overload
from uuid import UUID
from maleo.enums.service import (
    ServiceType as ServiceTypeEnum,
    OptServiceType,
    ServiceCategory as ServiceCategoryEnum,
    OptServiceCategory,
    ServiceKey,
    ListOfServiceKeys,
)
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
from ..enums.service import IdentifierType
from ..mixins.service import ServiceType, Category, Key, Name, Secret
from ..types.service import IdentifierValueType


class CreateData(
    Name[str],
    Key,
    ServiceType[ServiceTypeEnum],
    Category[ServiceCategoryEnum],
    Order[OptInt],
):
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


class FullUpdateData(
    Name[str],
    ServiceType[ServiceTypeEnum],
    Category[ServiceCategoryEnum],
    Order[OptInt],
):
    pass


class PartialUpdateData(
    Name[OptStr],
    ServiceType[OptServiceType],
    Category[OptServiceCategory],
    Order[OptInt],
):
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


class BaseServiceSchema(
    Name[str],
    Key,
    ServiceType[ServiceTypeEnum],
    Category[ServiceCategoryEnum],
    Order[OptInt],
):
    pass


class StandardServiceSchema(
    BaseServiceSchema,
    SimpleDataStatusMixin[DataStatus],
    LifecycleTimestamp,
    DataIdentifier,
):
    pass


OptStandardServiceSchema = StandardServiceSchema | None
ListOfStandardServiceSchemas = list[StandardServiceSchema]
SeqOfStandardServiceSchemas = Sequence[StandardServiceSchema]

KeyOrStandardSchema = ServiceKey | StandardServiceSchema
OptKeyOrStandardSchema = KeyOrStandardSchema | None


class FullServiceSchema(
    Secret,
    BaseServiceSchema,
    SimpleDataStatusMixin[DataStatus],
    DataTimestamp,
    DataIdentifier,
):
    pass


OptFullServiceSchema = FullServiceSchema | None
ListOfFullServiceSchemas = list[FullServiceSchema]
SeqOfFullServiceSchemas = Sequence[FullServiceSchema]

KeyOrFullSchema = ServiceKey | FullServiceSchema
OptKeyOrFullSchema = KeyOrFullSchema | None


AnyServiceSchemaType = Type[StandardServiceSchema] | Type[FullServiceSchema]


# User Type Schemas
AnyServiceSchema = StandardServiceSchema | FullServiceSchema
ServiceSchemaT = TypeVar("ServiceSchemaT", bound=AnyServiceSchema)

OptAnyServiceSchema = AnyServiceSchema | None
OptServiceSchemaT = TypeVar("OptServiceSchemaT", bound=OptAnyServiceSchema)

ListOfAnyServiceSchemas = ListOfStandardServiceSchemas | ListOfFullServiceSchemas
ListOfAnyServiceSchemasT = TypeVar(
    "ListOfAnyServiceSchemasT", bound=ListOfAnyServiceSchemas
)

OptListOfAnyServiceSchemas = ListOfAnyServiceSchemas | None
OptListOfAnyServiceSchemasT = TypeVar(
    "OptListOfAnyServiceSchemasT", bound=OptListOfAnyServiceSchemas
)


# User Type key and Schemas
AnyService = ServiceKey | AnyServiceSchema
AnyServiceT = TypeVar("AnyServiceT", bound=AnyService)

OptAnyService = AnyService | None
OptAnyServiceT = TypeVar("OptAnyServiceT", bound=OptAnyService)

ListOfAnyServices = ListOfServiceKeys | ListOfAnyServiceSchemas
ListOfAnyServicesT = TypeVar("ListOfAnyServicesT", bound=ListOfAnyServices)

OptListOfAnyServices = ListOfAnyServices | None
OptListOfAnyServicesT = TypeVar("OptListOfAnyServicesT", bound=OptListOfAnyServices)


class FullServiceMixin(BaseModel, Generic[OptAnyServiceT]):
    service: OptAnyServiceT = Field(..., description="Service")


class FullServicesMixin(BaseModel, Generic[OptListOfAnyServicesT]):
    services: OptListOfAnyServicesT = Field(..., description="Services")
