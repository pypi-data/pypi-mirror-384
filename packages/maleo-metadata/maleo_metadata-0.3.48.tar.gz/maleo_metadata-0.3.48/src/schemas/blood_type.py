from pydantic import BaseModel, Field
from typing import Generic, Literal, Sequence, Type, TypeVar, overload
from uuid import UUID
from maleo.enums.identity import BloodType, ListOfBloodTypes
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
from maleo.types.integer import OptListOfInts, OptInt
from maleo.types.string import OptListOfStrs, OptStr
from maleo.types.uuid import OptListOfUUIDs
from ..enums.blood_type import IdentifierType
from ..mixins.blood_type import Key, Name
from ..types.blood_type import IdentifierValueType


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


class BaseBloodTypeSchema(
    Name[str],
    Key,
    Order[OptInt],
):
    pass


class StandardBloodTypeSchema(
    BaseBloodTypeSchema,
    SimpleDataStatusMixin[DataStatus],
    LifecycleTimestamp,
    DataIdentifier,
):
    pass


OptStandardBloodTypeSchema = StandardBloodTypeSchema | None
ListOfStandardBloodTypeSchemas = list[StandardBloodTypeSchema]
SeqOfStandardBloodTypeSchemas = Sequence[StandardBloodTypeSchema]

KeyOrStandardSchema = BloodType | StandardBloodTypeSchema
OptKeyOrStandardSchema = KeyOrStandardSchema | None


class FullBloodTypeSchema(
    BaseBloodTypeSchema,
    SimpleDataStatusMixin[DataStatus],
    DataTimestamp,
    DataIdentifier,
):
    pass


OptFullBloodTypeSchema = FullBloodTypeSchema | None
ListOfFullBloodTypeSchemas = list[FullBloodTypeSchema]
SeqOfFullBloodTypeSchemas = Sequence[FullBloodTypeSchema]

KeyOrFullSchema = BloodType | FullBloodTypeSchema
OptKeyOrFullSchema = KeyOrFullSchema | None


AnyBloodTypeSchemaType = Type[StandardBloodTypeSchema] | Type[FullBloodTypeSchema]


# Blood Type Schemas
AnyBloodTypeSchema = StandardBloodTypeSchema | FullBloodTypeSchema
BloodTypeSchemaT = TypeVar("BloodTypeSchemaT", bound=AnyBloodTypeSchema)

OptAnyBloodTypeSchema = AnyBloodTypeSchema | None
OptBloodTypeSchemaT = TypeVar("OptBloodTypeSchemaT", bound=OptAnyBloodTypeSchema)

ListOfAnyBloodTypeSchemas = ListOfStandardBloodTypeSchemas | ListOfFullBloodTypeSchemas
ListOfAnyBloodTypeSchemasT = TypeVar(
    "ListOfAnyBloodTypeSchemasT", bound=ListOfAnyBloodTypeSchemas
)

OptListOfAnyBloodTypeSchemas = ListOfAnyBloodTypeSchemas | None
OptListOfAnyBloodTypeSchemasT = TypeVar(
    "OptListOfAnyBloodTypeSchemasT", bound=OptListOfAnyBloodTypeSchemas
)


# Blood Type key and Schemas
AnyBloodType = BloodType | AnyBloodTypeSchema
AnyBloodTypeT = TypeVar("AnyBloodTypeT", bound=AnyBloodType)

OptAnyBloodType = AnyBloodType | None
OptAnyBloodTypeT = TypeVar("OptAnyBloodTypeT", bound=OptAnyBloodType)

ListOfAnyBloodTypes = ListOfBloodTypes | ListOfAnyBloodTypeSchemas
ListOfAnyBloodTypesT = TypeVar("ListOfAnyBloodTypesT", bound=ListOfAnyBloodTypes)

OptListOfAnyBloodTypes = ListOfAnyBloodTypes | None
OptListOfAnyBloodTypesT = TypeVar(
    "OptListOfAnyBloodTypesT", bound=OptListOfAnyBloodTypes
)


class SimpleBloodTypeMixin(BaseModel, Generic[OptAnyBloodTypeT]):
    type: OptAnyBloodTypeT = Field(..., description="Blood type")


class FullBloodTypeMixin(BaseModel, Generic[OptAnyBloodTypeT]):
    blood_type: OptAnyBloodTypeT = Field(..., description="Blood type")


class SimpleBloodTypesMixin(BaseModel, Generic[OptListOfAnyBloodTypesT]):
    types: OptListOfAnyBloodTypesT = Field(..., description="Blood types")


class FullBloodTypesMixin(BaseModel, Generic[OptListOfAnyBloodTypesT]):
    blood_types: OptListOfAnyBloodTypesT = Field(..., description="Blood types")
