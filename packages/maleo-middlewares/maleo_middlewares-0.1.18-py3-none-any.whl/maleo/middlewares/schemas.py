from pydantic import BaseModel, Field
from typing import Annotated, List
from uuid import UUID
from maleo.enums.organization import OrganizationType, FullOrganizationTypeMixin
from maleo.enums.status import DataStatus as DataStatusEnum, SimpleDataStatusMixin
from maleo.enums.system import SystemRole as SystemRoleEnum
from maleo.enums.user import UserType, FullUserTypeMixin
from maleo.schemas.mixins.identity import (
    DataIdentifier,
    Key,
    IntOrganizationId,
    IntUserId,
    UUIDOrganizationId,
    UUIDUserId,
)
from maleo.types.string import ListOfStrs
from maleo.types.uuid import OptUUID


class InactiveKeys(BaseModel):
    keys: ListOfStrs = Field(..., min_length=1, description="Inactive keys")


class SystemRole(SimpleDataStatusMixin[DataStatusEnum], DataIdentifier):
    system_role: Annotated[SystemRoleEnum, Field(..., description="System role")]


class User(
    FullUserTypeMixin[UserType], SimpleDataStatusMixin[DataStatusEnum], DataIdentifier
):
    username: Annotated[str, Field(..., description="User's username", max_length=50)]
    email: Annotated[str, Field(..., description="User's email", max_length=255)]
    system_roles: Annotated[
        List[SystemRole], Field(..., description="User's system roles", min_length=1)
    ]


class Organization(
    Key[str],
    FullOrganizationTypeMixin[OrganizationType],
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    key: Annotated[str, Field(..., description="Organization's key", max_length=255)]


class UserOrganization(
    IntOrganizationId[int],
    IntUserId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    user_organization_roles: Annotated[
        ListOfStrs, Field(..., description="User's organization roles", min_length=1)
    ]


class UserOrganizationId(UUIDOrganizationId[OptUUID], UUIDUserId[UUID]):
    pass
