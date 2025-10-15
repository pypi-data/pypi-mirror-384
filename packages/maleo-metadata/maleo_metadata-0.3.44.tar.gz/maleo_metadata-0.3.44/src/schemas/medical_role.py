from pydantic import BaseModel, Field
from typing import Generic, List, Literal, Optional, Type, TypeVar, Union, overload
from uuid import UUID
from maleo.enums.medical import Role as MedicalRoleKey
from maleo.enums.status import (
    DataStatus as DataStatusEnum,
    ListOfDataStatuses,
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
from maleo.schemas.mixins.status import DataStatus
from maleo.schemas.mixins.timestamp import LifecycleTimestamp, DataTimestamp
from maleo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
    StatusUpdateParameter as BaseStatusUpdateParameter,
    DeleteSingleParameter as BaseDeleteSingleParameter,
)
from maleo.types.boolean import OptionalBoolean
from maleo.types.dict import StringToAnyDict
from maleo.types.integer import OptionalInteger, OptionalListOfIntegers
from maleo.types.string import OptionalListOfStrings, OptionalString
from maleo.types.uuid import OptionalListOfUUIDs
from ..enums.medical_role import IdentifierType
from ..mixins.medical_role import Code, Key, Name
from ..types.medical_role import IdentifierValueType


class CreateData(
    Name[str],
    Key,
    Code[str],
    Order[OptionalInteger],
    ParentId[OptionalInteger],
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
    Names[OptionalListOfStrings],
    Keys[OptionalListOfStrings],
    Codes[OptionalListOfStrings],
    UUIDs[OptionalListOfUUIDs],
    Ids[OptionalListOfIntegers],
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

    def to_query_params(self) -> StringToAnyDict:
        params = self.model_dump(
            mode="json", include=self._query_param_fields, exclude_none=True
        )
        params["filters"] = convert_filter(self.date_filters)
        params["sorts"] = convert_sort(self.sort_columns)
        params = {k: v for k, v in params.items()}
        return params


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    Names[OptionalListOfStrings],
    Keys[OptionalListOfStrings],
    Codes[OptionalListOfStrings],
    IsLeaf[OptionalBoolean],
    IsChild[OptionalBoolean],
    IsParent[OptionalBoolean],
    IsRoot[OptionalBoolean],
    ParentIds[OptionalListOfIntegers],
    UUIDs[OptionalListOfUUIDs],
    Ids[OptionalListOfIntegers],
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

    def to_query_params(self) -> StringToAnyDict:
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
        identifier: Literal[IdentifierType.ID],
        value: int,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier: Literal[IdentifierType.UUID],
        value: UUID,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier: Literal[IdentifierType.KEY, IdentifierType.NAME],
        value: str,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @classmethod
    def new(
        cls,
        identifier: IdentifierType,
        value: IdentifierValueType,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter":
        return cls(
            identifier=identifier,
            value=value,
            statuses=statuses,
            use_cache=use_cache,
        )

    def to_query_params(self) -> StringToAnyDict:
        return self.model_dump(
            mode="json", include={"statuses", "use_cache"}, exclude_none=True
        )


class FullUpdateData(
    Name[str],
    Code[str],
    Order[OptionalInteger],
    ParentId[OptionalInteger],
):
    pass


class PartialUpdateData(
    Name[OptionalString],
    Code[OptionalString],
    Order[OptionalInteger],
    ParentId[OptionalInteger],
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
    Order[OptionalInteger],
    ParentId[OptionalInteger],
):
    pass


class StandardMedicalRoleSchema(
    BaseMedicalRoleSchema,
    DataStatus[DataStatusEnum],
    LifecycleTimestamp,
    DataIdentifier,
):
    pass


class FullMedicalRoleSchema(
    BaseMedicalRoleSchema,
    DataStatus[DataStatusEnum],
    DataTimestamp,
    DataIdentifier,
):
    pass


AnyMedicalRoleSchemaType = Union[
    Type[StandardMedicalRoleSchema],
    Type[FullMedicalRoleSchema],
]


AnyMedicalRoleSchema = Union[
    StandardMedicalRoleSchema,
    FullMedicalRoleSchema,
]


MedicalRoleSchemaT = TypeVar("MedicalRoleSchemaT", bound=AnyMedicalRoleSchema)


KeyOrStandardSchema = Union[MedicalRoleKey, StandardMedicalRoleSchema]
KeyOrFullSchema = Union[MedicalRoleKey, FullMedicalRoleSchema]
AnyMedicalRole = Union[MedicalRoleKey, AnyMedicalRoleSchema]


MedicalRoleT = TypeVar("MedicalRoleT", bound=AnyMedicalRole)


class MedicalRoleMixin(BaseModel, Generic[MedicalRoleT]):
    medical_role: MedicalRoleT = Field(..., description="Medical role")


class OptionalMedicalRoleMixin(BaseModel, Generic[MedicalRoleT]):
    medical_role: Optional[MedicalRoleT] = Field(..., description="Medical role")


class MedicalRolesMixin(BaseModel, Generic[MedicalRoleT]):
    medical_roles: List[MedicalRoleT] = Field(..., description="Medical roles")


class OptionalMedicalRolesMixin(BaseModel, Generic[MedicalRoleT]):
    medical_roles: Optional[List[MedicalRoleT]] = Field(
        ..., description="Medical roles"
    )
