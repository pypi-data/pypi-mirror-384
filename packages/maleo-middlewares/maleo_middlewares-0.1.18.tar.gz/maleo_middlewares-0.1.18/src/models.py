from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import Enum, Integer, String
from typing import List, Optional
from maleo.enums.organization import OrganizationType
from maleo.enums.status import OptListOfDataStatuses, FULL_DATA_STATUSES
from maleo.enums.system import SystemRole
from maleo.enums.user import UserType
from maleo.schemas.model import DataIdentifier, DataStatus
from maleo.types.integer import OptInt
from maleo.types.string import ListOfStrs


class Base(DeclarativeBase):
    """Declarative Base"""


class User(
    DataStatus,
    DataIdentifier,
    Base,
):
    __tablename__ = "users"
    user_type: Mapped[UserType] = mapped_column(
        "user_type", Enum(UserType, name="user_type"), nullable=False
    )
    username: Mapped[str] = mapped_column(
        "username", String(50), unique=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        "email", String(255), unique=True, nullable=False
    )

    # relationships
    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    organizations: Mapped[List["UserOrganization"]] = relationship(
        "UserOrganization",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    system_roles: Mapped[List["UserSystemRole"]] = relationship(
        "UserSystemRole",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def get_system_roles(self, statuses: OptListOfDataStatuses = None) -> ListOfStrs:
        if not statuses:
            statuses = list(FULL_DATA_STATUSES)
        return [
            str(usr.system_role) for usr in self.system_roles if usr.status in statuses
        ]


class UserSystemRole(
    DataStatus,
    DataIdentifier,
    Base,
):
    __tablename__ = "user_system_roles"
    user_id: Mapped[int] = mapped_column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    system_role: Mapped[SystemRole] = mapped_column(
        "system_role", Enum(SystemRole, name="system_role"), nullable=False
    )

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="system_roles")


class Organization(
    DataStatus,
    DataIdentifier,
    Base,
):
    __tablename__ = "organizations"
    organization_type: Mapped[OrganizationType] = mapped_column(
        "organization_type",
        Enum(OrganizationType, name="organization_type"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column("key", String(255), unique=True, nullable=False)

    # relationships
    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    users: Mapped[List["UserOrganization"]] = relationship(
        "UserOrganization",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    organization_roles: Mapped[List["OrganizationRole"]] = relationship(
        "OrganizationRole",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def get_organization_roles(
        self, statuses: OptListOfDataStatuses = None
    ) -> ListOfStrs:
        if not statuses:
            statuses = list(FULL_DATA_STATUSES)
        return [orr.key for orr in self.organization_roles if orr.status in statuses]


class APIKey(
    DataStatus,
    DataIdentifier,
    Base,
):
    __tablename__ = "api_keys"
    user_id: Mapped[int] = mapped_column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[OptInt] = mapped_column(
        "organization_id",
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    api_key: Mapped[str] = mapped_column(
        "api_key", String(255), unique=True, nullable=False
    )

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="api_keys"
    )


class UserOrganization(
    DataStatus,
    DataIdentifier,
    Base,
):
    __tablename__ = "user_organizations"
    user_id: Mapped[int] = mapped_column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[int] = mapped_column(
        "organization_id",
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="organizations")
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="users"
    )
    user_organization_roles: Mapped[List["UserOrganizationRole"]] = relationship(
        "UserOrganizationRole",
        back_populates="user_organization",
        cascade="all, delete-orphan",
    )

    def get_user_organization_roles(
        self, statuses: OptListOfDataStatuses = None
    ) -> ListOfStrs:
        if not statuses:
            statuses = list(FULL_DATA_STATUSES)
        return [
            uor.organization_role.key
            for uor in self.user_organization_roles
            if (
                uor.status in statuses
                and uor.user_organization_id == self.id
                and uor.user_organization.user_id == self.user_id
                and uor.user_organization.organization_id == self.organization_id
            )
        ]


class OrganizationRole(
    DataStatus,
    DataIdentifier,
    Base,
):
    __tablename__ = "organization_roles"

    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column("key", String(50), nullable=False)

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="organization_roles"
    )

    # relationship
    user_organization_roles: Mapped[List["UserOrganizationRole"]] = relationship(
        "UserOrganizationRole",
        back_populates="organization_role",
        cascade="all, delete-orphan",
    )


class UserOrganizationRole(
    DataStatus,
    DataIdentifier,
    Base,
):
    __tablename__ = "user_organization_roles"

    user_organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user_organizations.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )

    organization_role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organization_roles.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )

    # Relationships
    user_organization: Mapped["UserOrganization"] = relationship(
        "UserOrganization",
        back_populates="user_organization_roles",
    )

    organization_role: Mapped["OrganizationRole"] = relationship(
        "OrganizationRole",
        back_populates="user_organization_roles",
    )
