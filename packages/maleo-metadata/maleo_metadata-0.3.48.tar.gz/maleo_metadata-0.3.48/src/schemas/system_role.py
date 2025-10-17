from pydantic import BaseModel, Field
from typing import Generic, Literal, Sequence, Type, TypeVar, overload
from uuid import UUID
from maleo.enums.system import SystemRole, ListOfSystemRoles
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
from ..enums.system_role import IdentifierType
from ..mixins.system_role import Key, Name
from ..types.system_role import IdentifierValueType


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


class BaseSystemRoleSchema(
    Name[str],
    Key,
    Order[OptInt],
):
    pass


class StandardSystemRoleSchema(
    BaseSystemRoleSchema,
    SimpleDataStatusMixin[DataStatus],
    LifecycleTimestamp,
    DataIdentifier,
):
    pass


OptStandardSystemRoleSchema = StandardSystemRoleSchema | None
ListOfStandardSystemRoleSchemas = list[StandardSystemRoleSchema]
SeqOfStandardSystemRoleSchemas = Sequence[StandardSystemRoleSchema]

KeyOrStandardSchema = SystemRole | StandardSystemRoleSchema
OptKeyOrStandardSchema = KeyOrStandardSchema | None


class FullSystemRoleSchema(
    BaseSystemRoleSchema,
    SimpleDataStatusMixin[DataStatus],
    DataTimestamp,
    DataIdentifier,
):
    pass


OptFullSystemRoleSchema = FullSystemRoleSchema | None
ListOfFullSystemRoleSchemas = list[FullSystemRoleSchema]
SeqOfFullSystemRoleSchemas = Sequence[FullSystemRoleSchema]

KeyOrFullSchema = SystemRole | FullSystemRoleSchema
OptKeyOrFullSchema = KeyOrFullSchema | None


AnySystemRoleSchemaType = Type[StandardSystemRoleSchema] | Type[FullSystemRoleSchema]


# User Type Schemas
AnySystemRoleSchema = StandardSystemRoleSchema | FullSystemRoleSchema
SystemRoleSchemaT = TypeVar("SystemRoleSchemaT", bound=AnySystemRoleSchema)

OptAnySystemRoleSchema = AnySystemRoleSchema | None
OptSystemRoleSchemaT = TypeVar("OptSystemRoleSchemaT", bound=OptAnySystemRoleSchema)

ListOfAnySystemRoleSchemas = (
    ListOfStandardSystemRoleSchemas | ListOfFullSystemRoleSchemas
)
ListOfAnySystemRoleSchemasT = TypeVar(
    "ListOfAnySystemRoleSchemasT", bound=ListOfAnySystemRoleSchemas
)

OptListOfAnySystemRoleSchemas = ListOfAnySystemRoleSchemas | None
OptListOfAnySystemRoleSchemasT = TypeVar(
    "OptListOfAnySystemRoleSchemasT", bound=OptListOfAnySystemRoleSchemas
)


# User Type key and Schemas
AnySystemRole = SystemRole | AnySystemRoleSchema
AnySystemRoleT = TypeVar("AnySystemRoleT", bound=AnySystemRole)

OptAnySystemRole = AnySystemRole | None
OptAnySystemRoleT = TypeVar("OptAnySystemRoleT", bound=OptAnySystemRole)

ListOfAnySystemRoles = ListOfSystemRoles | ListOfAnySystemRoleSchemas
ListOfAnySystemRolesT = TypeVar("ListOfAnySystemRolesT", bound=ListOfAnySystemRoles)

OptListOfAnySystemRoles = ListOfAnySystemRoles | None
OptListOfAnySystemRolesT = TypeVar(
    "OptListOfAnySystemRolesT", bound=OptListOfAnySystemRoles
)


class SimpleSystemRoleMixin(BaseModel, Generic[OptAnySystemRoleT]):
    role: OptAnySystemRoleT = Field(..., description="System role")


class FullSystemRoleMixin(BaseModel, Generic[OptAnySystemRoleT]):
    system_role: OptAnySystemRoleT = Field(..., description="System role")


class SimpleSystemRolesMixin(BaseModel, Generic[OptListOfAnySystemRolesT]):
    roles: OptListOfAnySystemRolesT = Field(..., description="System roles")


class FullSystemRolesMixin(BaseModel, Generic[OptListOfAnySystemRolesT]):
    system_roles: OptListOfAnySystemRolesT = Field(..., description="System roles")
