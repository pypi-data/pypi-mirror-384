from pydantic import BaseModel, Field
from typing import Generic, Literal, Sequence, Type, TypeVar, overload
from uuid import UUID
from maleo.enums.organization import OrganizationType, ListOfOrganizationTypes
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
from ..enums.organization_type import IdentifierType
from ..mixins.organization_type import Key, Name
from ..types.organization_type import IdentifierValueType


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


class BaseOrganizationTypeSchema(
    Name[str],
    Key,
    Order[OptInt],
):
    pass


class StandardOrganizationTypeSchema(
    BaseOrganizationTypeSchema,
    SimpleDataStatusMixin[DataStatus],
    LifecycleTimestamp,
    DataIdentifier,
):
    pass


OptStandardOrganizationTypeSchema = StandardOrganizationTypeSchema | None
ListOfStandardOrganizationTypeSchemas = list[StandardOrganizationTypeSchema]
SeqOfStandardOrganizationTypeSchemas = Sequence[StandardOrganizationTypeSchema]

KeyOrStandardSchema = OrganizationType | StandardOrganizationTypeSchema
OptKeyOrStandardSchema = KeyOrStandardSchema | None


class FullOrganizationTypeSchema(
    BaseOrganizationTypeSchema,
    SimpleDataStatusMixin[DataStatus],
    DataTimestamp,
    DataIdentifier,
):
    pass


OptFullOrganizationTypeSchema = FullOrganizationTypeSchema | None
ListOfFullOrganizationTypeSchemas = list[FullOrganizationTypeSchema]
SeqOfFullOrganizationTypeSchemas = Sequence[FullOrganizationTypeSchema]

KeyOrFullSchema = OrganizationType | FullOrganizationTypeSchema
OptKeyOrFullSchema = KeyOrFullSchema | None


AnyOrganizationTypeSchemaType = (
    Type[StandardOrganizationTypeSchema] | Type[FullOrganizationTypeSchema]
)


# Organization Type Schemas
AnyOrganizationTypeSchema = StandardOrganizationTypeSchema | FullOrganizationTypeSchema
OrganizationTypeSchemaT = TypeVar(
    "OrganizationTypeSchemaT", bound=AnyOrganizationTypeSchema
)

OptAnyOrganizationTypeSchema = AnyOrganizationTypeSchema | None
OptOrganizationTypeSchemaT = TypeVar(
    "OptOrganizationTypeSchemaT", bound=OptAnyOrganizationTypeSchema
)

ListOfAnyOrganizationTypeSchemas = (
    ListOfStandardOrganizationTypeSchemas | ListOfFullOrganizationTypeSchemas
)
ListOfAnyOrganizationTypeSchemasT = TypeVar(
    "ListOfAnyOrganizationTypeSchemasT", bound=ListOfAnyOrganizationTypeSchemas
)

OptListOfAnyOrganizationTypeSchemas = ListOfAnyOrganizationTypeSchemas | None
OptListOfAnyOrganizationTypeSchemasT = TypeVar(
    "OptListOfAnyOrganizationTypeSchemasT", bound=OptListOfAnyOrganizationTypeSchemas
)


# Organization Type key and Schemas
AnyOrganizationType = OrganizationType | AnyOrganizationTypeSchema
AnyOrganizationTypeT = TypeVar("AnyOrganizationTypeT", bound=AnyOrganizationType)

OptAnyOrganizationType = AnyOrganizationType | None
OptAnyOrganizationTypeT = TypeVar(
    "OptAnyOrganizationTypeT", bound=OptAnyOrganizationType
)

ListOfAnyOrganizationTypes = ListOfOrganizationTypes | ListOfAnyOrganizationTypeSchemas
ListOfAnyOrganizationTypesT = TypeVar(
    "ListOfAnyOrganizationTypesT", bound=ListOfAnyOrganizationTypes
)

OptListOfAnyOrganizationTypes = ListOfAnyOrganizationTypes | None
OptListOfAnyOrganizationTypesT = TypeVar(
    "OptListOfAnyOrganizationTypesT", bound=OptListOfAnyOrganizationTypes
)


class SimpleOrganizationTypeMixin(BaseModel, Generic[OptAnyOrganizationTypeT]):
    type: OptAnyOrganizationTypeT = Field(..., description="Organization type")


class FullOrganizationTypeMixin(BaseModel, Generic[OptAnyOrganizationTypeT]):
    organization_type: OptAnyOrganizationTypeT = Field(
        ..., description="Organization type"
    )


class SimpleOrganizationTypesMixin(BaseModel, Generic[OptListOfAnyOrganizationTypesT]):
    types: OptListOfAnyOrganizationTypesT = Field(..., description="Organization types")


class FullOrganizationTypesMixin(BaseModel, Generic[OptListOfAnyOrganizationTypesT]):
    organization_types: OptListOfAnyOrganizationTypesT = Field(
        ..., description="Organization types"
    )
