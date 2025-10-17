from datetime import datetime, timezone
from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload
from starlette.authentication import AuthenticationError
from typing import Tuple
from uuid import UUID
from maleo.crypto.hash.enums import Mode
from maleo.crypto.hash.sha256 import hash
from maleo.database.enums import CacheOrigin, CacheLayer, Connection
from maleo.database.handlers import PostgreSQLHandler, RedisHandler
from maleo.database.utils import build_cache_key
from maleo.enums.expiration import Expiration
from maleo.enums.status import DataStatus
from maleo.schemas.connection import ConnectionContext
from maleo.types.datetime import OptDatetime
from .models import (
    Base,
    User as UserModel,
    Organization as OrganizationModel,
    UserOrganization as UserOrganizationModel,
    APIKey as APIKeyModel,
    UserOrganizationRole as UserOrganizationRoleModel,
)
from .schemas import (
    User as UserSchema,
    Organization as OrganizationSchema,
    UserOrganizationId,
    UserOrganization as UserOrganizationSchema,
)


class IdentityProvider:
    def __init__(
        self,
        *,
        database: PostgreSQLHandler[Base],
        cache: RedisHandler,
    ) -> None:
        self._database = database
        self._cache = cache
        self._namespace = self._cache.config.additional.build_namespace(
            "identity",
            use_self_base=True,
            origin=CacheOrigin.SERVICE,
            layer=CacheLayer.MIDDLEWARE,
        )

    def _build_get_user_statement(self, user_id: UUID) -> Select[Tuple[UserModel]]:
        return (
            select(UserModel)
            .options(selectinload(UserModel.system_roles))
            .where(
                UserModel.uuid == user_id,
                UserModel.status == DataStatus.ACTIVE,
            )
        )

    async def get_user(
        self,
        user_id: UUID,
        exp: OptDatetime = None,
        *,
        operation_id: UUID,
        connection_context: ConnectionContext,
    ) -> UserSchema:
        cache_key = build_cache_key("user", str(user_id), namespace=self._namespace)
        redis = self._cache.manager.client.get(Connection.ASYNC)
        redis_data = await redis.get(cache_key)
        if redis_data is not None:
            return UserSchema.model_validate_json(redis_data)

        async with self._database.manager.session.get(
            Connection.ASYNC,
            operation_id=operation_id,
            connection_context=connection_context,
        ) as session:
            stmt = self._build_get_user_statement(user_id)

            # Execute and fetch results
            result = await session.execute(stmt)
            row = result.scalars().one_or_none()

            if row is None:
                raise AuthenticationError(
                    f"Can not find active User with ID: {user_id}"
                )

            data = UserSchema.model_validate(row, from_attributes=True)

        if exp is None:
            ex = Expiration.EXP_1WK.value
        else:
            now = datetime.now(tz=timezone.utc)
            if exp <= now:
                raise AuthenticationError("Cache expiry is less then now")
            ex = min(int((exp - now).total_seconds()), Expiration.EXP_1WK.value)
        await redis.set(cache_key, data.model_dump_json(), ex)

        return data

    def _build_get_organization_statement(
        self, organization_id: UUID
    ) -> Select[Tuple[OrganizationModel]]:
        return select(OrganizationModel).where(
            OrganizationModel.uuid == organization_id,
            OrganizationModel.status == DataStatus.ACTIVE,
        )

    async def get_organization(
        self,
        organization_id: UUID,
        exp: OptDatetime = None,
        *,
        operation_id: UUID,
        connection_context: ConnectionContext,
    ) -> OrganizationSchema:
        cache_key = build_cache_key(
            "organization", str(organization_id), namespace=self._namespace
        )
        redis = self._cache.manager.client.get(Connection.ASYNC)
        redis_data = await redis.get(cache_key)
        if redis_data is not None:
            return OrganizationSchema.model_validate_json(redis_data)

        async with self._database.manager.session.get(
            Connection.ASYNC,
            operation_id=operation_id,
            connection_context=connection_context,
        ) as session:
            stmt = self._build_get_organization_statement(organization_id)

            # Execute and fetch results
            result = await session.execute(stmt)
            row = result.scalars().one_or_none()

            if row is None:
                raise AuthenticationError(
                    f"Can not find active Organization with ID: {organization_id}"
                )

            data = OrganizationSchema.model_validate(row, from_attributes=True)

        if exp is None:
            ex = Expiration.EXP_1WK.value
        else:
            now = datetime.now(tz=timezone.utc)
            if exp <= now:
                raise AuthenticationError("Cache expiry is less then now")
            ex = min(int((exp - now).total_seconds()), Expiration.EXP_1WK.value)
        await redis.set(cache_key, data.model_dump_json(), ex)

        return data

    def _build_get_user_organization_statement(
        self, user_id: UUID, organization_id: UUID
    ) -> Select[Tuple[UserOrganizationModel]]:
        return (
            select(UserOrganizationModel)
            .options(
                selectinload(
                    UserOrganizationModel.user_organization_roles
                ).selectinload(UserOrganizationRoleModel.organization_role)
            )
            .join(UserModel, UserOrganizationModel.user_id == UserModel.id)
            .join(
                OrganizationModel,
                UserOrganizationModel.organization_id == OrganizationModel.id,
            )
            .where(
                UserOrganizationModel.status == DataStatus.ACTIVE,
                UserModel.uuid == user_id,
                UserModel.status == DataStatus.ACTIVE,
                OrganizationModel.uuid == organization_id,
                OrganizationModel.status == DataStatus.ACTIVE,
            )
        )

    async def get_user_organization(
        self,
        user_id: UUID,
        organization_id: UUID,
        exp: OptDatetime = None,
        *,
        operation_id: UUID,
        connection_context: ConnectionContext,
    ) -> UserOrganizationSchema:
        cache_key = build_cache_key(
            "user_organization",
            str(user_id),
            str(organization_id),
            namespace=self._namespace,
        )
        redis = self._cache.manager.client.get(Connection.ASYNC)
        redis_data = await redis.get(cache_key)
        if redis_data is not None:
            return UserOrganizationSchema.model_validate_json(redis_data)

        async with self._database.manager.session.get(
            Connection.ASYNC,
            operation_id=operation_id,
            connection_context=connection_context,
        ) as session:
            stmt = self._build_get_user_organization_statement(user_id, organization_id)

            # Execute and fetch results
            result = await session.execute(stmt)
            row = result.scalars().one_or_none()

            if row is None:
                raise AuthenticationError(
                    f"Can not find active relation for User '{user_id}' and Organization '{organization_id}'"
                )

            user_organization_roles = row.get_user_organization_roles(
                [DataStatus.ACTIVE]
            )
            data = UserOrganizationSchema(
                id=row.id,
                uuid=row.uuid,
                status=row.status,
                user_id=row.user_id,
                organization_id=row.organization_id,
                user_organization_roles=user_organization_roles,
            )

        if exp is None:
            ex = Expiration.EXP_1WK.value
        else:
            now = datetime.now(tz=timezone.utc)
            if exp <= now:
                raise AuthenticationError("Cache expiry is less then now")
            ex = min(int((exp - now).total_seconds()), Expiration.EXP_1WK.value)
        await redis.set(cache_key, data.model_dump_json(), ex)

        return data

    async def user_organization_id_from_api_key(
        self,
        api_key: str,
        *,
        operation_id: UUID,
        connection_context: ConnectionContext,
    ) -> UserOrganizationId:
        hashed_api_key = hash(Mode.DIGEST, message=api_key)

        cache_key = build_cache_key(
            "user_organization_id",
            hashed_api_key,
            namespace=self._namespace,
        )
        redis = self._cache.manager.client.get(Connection.ASYNC)
        redis_data = await redis.get(cache_key)
        if redis_data is not None:
            return UserOrganizationId.model_validate_json(redis_data)

        async with self._database.manager.session.get(
            Connection.ASYNC,
            operation_id=operation_id,
            connection_context=connection_context,
        ) as session:
            stmt = (
                select(APIKeyModel)
                .options(
                    selectinload(APIKeyModel.user),
                    selectinload(APIKeyModel.organization),
                )
                .where(
                    APIKeyModel.status == DataStatus.ACTIVE,
                    APIKeyModel.api_key == hashed_api_key,
                )
            )

            # Execute and fetch results
            result = await session.execute(stmt)
            row = result.scalars().one_or_none()

            if row is None:
                raise AuthenticationError(
                    "Can not find valid User-Organization combination for given API Key"
                )

            data = UserOrganizationId(
                user_id=row.user.uuid,
                organization_id=(
                    row.organization.uuid if row.organization is not None else None
                ),
            )

        await redis.set(cache_key, data.model_dump_json(), Expiration.EXP_1MO.value)

        return data
