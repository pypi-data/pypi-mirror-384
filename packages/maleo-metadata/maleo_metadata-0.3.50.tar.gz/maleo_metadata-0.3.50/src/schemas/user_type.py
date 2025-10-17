from pydantic import BaseModel, Field
from typing import Generic, Literal, Sequence, Type, TypeVar, overload
from uuid import UUID
from maleo.enums.user import UserType, ListOfUserTypes
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
from ..enums.user_type import IdentifierType
from ..mixins.user_type import Key, Name
from ..types.user_type import IdentifierValueType


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


class BaseUserTypeSchema(
    Name[str],
    Key,
    Order[OptInt],
):
    pass


class StandardUserTypeSchema(
    BaseUserTypeSchema,
    SimpleDataStatusMixin[DataStatus],
    LifecycleTimestamp,
    DataIdentifier,
):
    pass


OptStandardUserTypeSchema = StandardUserTypeSchema | None
ListOfStandardUserTypeSchemas = list[StandardUserTypeSchema]
SeqOfStandardUserTypeSchemas = Sequence[StandardUserTypeSchema]

KeyOrStandardSchema = UserType | StandardUserTypeSchema
OptKeyOrStandardSchema = KeyOrStandardSchema | None


class FullUserTypeSchema(
    BaseUserTypeSchema,
    SimpleDataStatusMixin[DataStatus],
    DataTimestamp,
    DataIdentifier,
):
    pass


OptFullUserTypeSchema = FullUserTypeSchema | None
ListOfFullUserTypeSchemas = list[FullUserTypeSchema]
SeqOfFullUserTypeSchemas = Sequence[FullUserTypeSchema]

KeyOrFullSchema = UserType | FullUserTypeSchema
OptKeyOrFullSchema = KeyOrFullSchema | None


AnyUserTypeSchemaType = Type[StandardUserTypeSchema] | Type[FullUserTypeSchema]


# User Type Schemas
AnyUserTypeSchema = StandardUserTypeSchema | FullUserTypeSchema
UserTypeSchemaT = TypeVar("UserTypeSchemaT", bound=AnyUserTypeSchema)

OptAnyUserTypeSchema = AnyUserTypeSchema | None
OptUserTypeSchemaT = TypeVar("OptUserTypeSchemaT", bound=OptAnyUserTypeSchema)

ListOfAnyUserTypeSchemas = ListOfStandardUserTypeSchemas | ListOfFullUserTypeSchemas
ListOfAnyUserTypeSchemasT = TypeVar(
    "ListOfAnyUserTypeSchemasT", bound=ListOfAnyUserTypeSchemas
)

OptListOfAnyUserTypeSchemas = ListOfAnyUserTypeSchemas | None
OptListOfAnyUserTypeSchemasT = TypeVar(
    "OptListOfAnyUserTypeSchemasT", bound=OptListOfAnyUserTypeSchemas
)


# User Type key and Schemas
AnyUserType = UserType | AnyUserTypeSchema
AnyUserTypeT = TypeVar("AnyUserTypeT", bound=AnyUserType)

OptAnyUserType = AnyUserType | None
OptAnyUserTypeT = TypeVar("OptAnyUserTypeT", bound=OptAnyUserType)

ListOfAnyUserTypes = ListOfUserTypes | ListOfAnyUserTypeSchemas
ListOfAnyUserTypesT = TypeVar("ListOfAnyUserTypesT", bound=ListOfAnyUserTypes)

OptListOfAnyUserTypes = ListOfAnyUserTypes | None
OptListOfAnyUserTypesT = TypeVar("OptListOfAnyUserTypesT", bound=OptListOfAnyUserTypes)


class SimpleUserTypeMixin(BaseModel, Generic[OptAnyUserTypeT]):
    type: OptAnyUserTypeT = Field(..., description="User type")


class FullUserTypeMixin(BaseModel, Generic[OptAnyUserTypeT]):
    user_type: OptAnyUserTypeT = Field(..., description="User type")


class SimpleUserTypesMixin(BaseModel, Generic[OptListOfAnyUserTypesT]):
    types: OptListOfAnyUserTypesT = Field(..., description="User types")


class FullUserTypesMixin(BaseModel, Generic[OptListOfAnyUserTypesT]):
    user_types: OptListOfAnyUserTypesT = Field(..., description="User types")
