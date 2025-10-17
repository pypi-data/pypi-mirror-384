from pydantic import BaseModel, Field
from typing import Generic, Literal, Sequence, Type, TypeVar, overload
from uuid import UUID
from maleo.enums.medical import MedicalRole, ListOfMedicalRoles
from maleo.enums.status import (
    DataStatus,
    ListOfDataStatuses,
    SimpleDataStatusMixin,
    FULL_DATA_STATUSES,
)
from maleo.schemas.mixins.filter import convert as convert_filter
from maleo.schemas.mixins.general import Codes, Order
from maleo.schemas.mixins.hierarchy import IsRoot, IsParent, IsChild, IsLeaf
from maleo.schemas.mixins.identity import (
    DataIdentifier,
    IdentifierTypeValue,
    Ids,
    UUIDs,
    ParentId,
    ParentIds,
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
from maleo.types.boolean import OptBool
from maleo.types.dict import StrToAnyDict
from maleo.types.integer import OptInt, OptListOfInts
from maleo.types.string import OptListOfStrs, OptStr
from maleo.types.uuid import OptListOfUUIDs
from ..enums.medical_role import IdentifierType
from ..mixins.medical_role import Code, Key, Name
from ..types.medical_role import IdentifierValueType


class CreateData(
    Name[str],
    Key,
    Code[str],
    Order[OptInt],
    ParentId[OptInt],
):
    pass


class CreateDataMixin(BaseModel):
    data: CreateData = Field(..., description="Create data")


class CreateParameter(
    CreateDataMixin,
):
    pass


class ReadMultipleSpecializationsParameter(
    ReadPaginatedMultipleParameter,
    Names[OptListOfStrs],
    Keys[OptListOfStrs],
    Codes[OptListOfStrs],
    UUIDs[OptListOfUUIDs],
    Ids[OptListOfInts],
    ParentId[int],
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


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    Names[OptListOfStrs],
    Keys[OptListOfStrs],
    Codes[OptListOfStrs],
    IsLeaf[OptBool],
    IsChild[OptBool],
    IsParent[OptBool],
    IsRoot[OptBool],
    ParentIds[OptListOfInts],
    UUIDs[OptListOfUUIDs],
    Ids[OptListOfInts],
):
    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "ids",
            "uuids",
            "parent_ids",
            "is_root",
            "is_parent",
            "is_child",
            "is_leaf",
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
    Code[str],
    Order[OptInt],
    ParentId[OptInt],
):
    pass


class PartialUpdateData(
    Name[OptStr],
    Code[OptStr],
    Order[OptInt],
    ParentId[OptInt],
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


class BaseMedicalRoleSchema(
    Name[str],
    Key,
    Code[str],
    Order[OptInt],
    ParentId[OptInt],
):
    pass


class StandardMedicalRoleSchema(
    BaseMedicalRoleSchema,
    SimpleDataStatusMixin[DataStatus],
    LifecycleTimestamp,
    DataIdentifier,
):
    pass


OptStandardMedicalRoleSchema = StandardMedicalRoleSchema | None
ListOfStandardMedicalRoleSchemas = list[StandardMedicalRoleSchema]
SeqOfStandardMedicalRoleSchemas = Sequence[StandardMedicalRoleSchema]

KeyOrStandardSchema = MedicalRole | StandardMedicalRoleSchema
OptKeyOrStandardSchema = KeyOrStandardSchema | None


class FullMedicalRoleSchema(
    BaseMedicalRoleSchema,
    SimpleDataStatusMixin[DataStatus],
    DataTimestamp,
    DataIdentifier,
):
    pass


OptFullMedicalRoleSchema = FullMedicalRoleSchema | None
ListOfFullMedicalRoleSchemas = list[FullMedicalRoleSchema]
SeqOfFullMedicalRoleSchemas = Sequence[FullMedicalRoleSchema]

KeyOrFullSchema = MedicalRole | FullMedicalRoleSchema
OptKeyOrFullSchema = KeyOrFullSchema | None


AnyMedicalRoleSchemaType = Type[StandardMedicalRoleSchema] | Type[FullMedicalRoleSchema]


# User Type Schemas
AnyMedicalRoleSchema = StandardMedicalRoleSchema | FullMedicalRoleSchema
MedicalRoleSchemaT = TypeVar("MedicalRoleSchemaT", bound=AnyMedicalRoleSchema)

OptAnyMedicalRoleSchema = AnyMedicalRoleSchema | None
OptMedicalRoleSchemaT = TypeVar("OptMedicalRoleSchemaT", bound=OptAnyMedicalRoleSchema)

ListOfAnyMedicalRoleSchemas = (
    ListOfStandardMedicalRoleSchemas | ListOfFullMedicalRoleSchemas
)
ListOfAnyMedicalRoleSchemasT = TypeVar(
    "ListOfAnyMedicalRoleSchemasT", bound=ListOfAnyMedicalRoleSchemas
)

OptListOfAnyMedicalRoleSchemas = ListOfAnyMedicalRoleSchemas | None
OptListOfAnyMedicalRoleSchemasT = TypeVar(
    "OptListOfAnyMedicalRoleSchemasT", bound=OptListOfAnyMedicalRoleSchemas
)


# User Type key and Schemas
AnyMedicalRole = MedicalRole | AnyMedicalRoleSchema
AnyMedicalRoleT = TypeVar("AnyMedicalRoleT", bound=AnyMedicalRole)

OptAnyMedicalRole = AnyMedicalRole | None
OptAnyMedicalRoleT = TypeVar("OptAnyMedicalRoleT", bound=OptAnyMedicalRole)

ListOfAnyMedicalRoles = ListOfMedicalRoles | ListOfAnyMedicalRoleSchemas
ListOfAnyMedicalRolesT = TypeVar("ListOfAnyMedicalRolesT", bound=ListOfAnyMedicalRoles)

OptListOfAnyMedicalRoles = ListOfAnyMedicalRoles | None
OptListOfAnyMedicalRolesT = TypeVar(
    "OptListOfAnyMedicalRolesT", bound=OptListOfAnyMedicalRoles
)


class SimpleMedicalRoleMixin(BaseModel, Generic[OptAnyMedicalRoleT]):
    role: OptAnyMedicalRoleT = Field(..., description="Medical role")


class FullMedicalRoleMixin(BaseModel, Generic[OptAnyMedicalRoleT]):
    medical_role: OptAnyMedicalRoleT = Field(..., description="Medical role")


class SimpleMedicalRolesMixin(BaseModel, Generic[OptListOfAnyMedicalRolesT]):
    roles: OptListOfAnyMedicalRolesT = Field(..., description="Medical roles")


class FullMedicalRolesMixin(BaseModel, Generic[OptListOfAnyMedicalRolesT]):
    medical_roles: OptListOfAnyMedicalRolesT = Field(..., description="Medical roles")
