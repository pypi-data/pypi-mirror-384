from Crypto.PublicKey.RSA import RsaKey
from datetime import datetime, timezone
from fastapi.requests import HTTPConnection
from starlette.authentication import AuthenticationBackend, AuthenticationError
from typing import Optional, Tuple
from uuid import UUID
from maleo.database.handlers import PostgreSQLHandler, RedisHandler
from maleo.enums.organization import OrganizationRole
from maleo.enums.status import DataStatus
from maleo.enums.system import SystemRole
from maleo.schemas.application import ApplicationContext
from maleo.schemas.connection import ConnectionContext
from maleo.schemas.security.api_key import validate as validate_api_key
from maleo.schemas.security.authentication import (
    RequestCredentials,
    RequestUser,
    BaseAuthentication,
    BaseCredentials,
    BaseUser,
    is_authenticated,
    is_tenant,
    is_system,
)
from maleo.schemas.security.authorization import (
    BaseAuthorization,
    BearerTokenAuthorization,
    APIKeyAuthorization,
    is_bearer_token,
    is_api_key,
)
from maleo.schemas.security.impersonation import Impersonation
from maleo.schemas.security.token import Domain
from maleo.types.datetime import OptDatetime
from maleo.types.string import OptListOfStrs
from maleo.types.uuid import OptUUID
from .identity import IdentityProvider
from .models import Base
from .schemas import (
    User as UserSchema,
    Organization as OrganizationSchema,
    UserOrganization as UserOrganizationSchema,
)


class Backend(AuthenticationBackend):
    def __init__(
        self,
        *,
        application_context: ApplicationContext,
        database: PostgreSQLHandler[Base],
        cache: RedisHandler,
        public_key: RsaKey,
    ):
        super().__init__()
        self._application_context = application_context
        self._database = database
        self._cache = cache
        self._identity_provider = IdentityProvider(database=database, cache=cache)
        self._public_key = public_key

    async def _get_credentials(
        self,
        user_id: UUID,
        organization_id: OptUUID,
        roles: OptListOfStrs = None,
        exp: OptDatetime = None,
        *,
        operation_id: UUID,
        connection_context: ConnectionContext,
    ) -> Tuple[
        UserSchema, Optional[OrganizationSchema], Optional[UserOrganizationSchema]
    ]:
        user = await self._identity_provider.get_user(
            user_id,
            exp,
            operation_id=operation_id,
            connection_context=connection_context,
        )

        if organization_id is None:
            organization = None
            user_organization = None

            active_system_roles = [
                system_role.system_role.value
                for system_role in user.system_roles
                if system_role.status is DataStatus.ACTIVE
            ]

            if roles is not None:
                for role in roles:
                    if role not in active_system_roles:
                        raise AuthenticationError(
                            f"User is not assigned to role '{role}' in the database"
                        )
        else:
            organization = await self._identity_provider.get_organization(
                organization_id,
                exp,
                operation_id=operation_id,
                connection_context=connection_context,
            )

            user_organization = await self._identity_provider.get_user_organization(
                user_id,
                organization_id,
                exp,
                operation_id=operation_id,
                connection_context=connection_context,
            )

            if roles is not None:
                for role in roles:
                    if role not in user_organization.user_organization_roles:
                        raise AuthenticationError(
                            f"User is not assigned to role '{role}' in the database"
                        )

        return user, organization, user_organization

    def _build_authentication_component(
        self,
        user: UserSchema,
        organization: Optional[OrganizationSchema],
        user_organization: Optional[UserOrganizationSchema],
    ) -> Tuple[RequestCredentials, RequestUser]:
        if user_organization is not None:
            roles = user_organization.user_organization_roles
        else:
            roles = [
                system_role.system_role.value
                for system_role in user.system_roles
                if system_role.status is DataStatus.ACTIVE
            ]

        domain = Domain.SYSTEM if user_organization is None else Domain.TENANT
        scopes = ["authenticated", domain] + [f"{domain}:{role}" for role in roles]

        request_credentials = RequestCredentials(
            domain=domain,
            user_id=user.id,
            user_uuid=user.uuid,
            organization_id=organization.id if organization is not None else None,
            organization_uuid=organization.uuid if organization is not None else None,
            roles=roles,
            scopes=scopes,
        )

        request_user = RequestUser(
            authenticated=True,
            organization=organization.key if organization is not None else None,
            username=user.username,
            email=user.email,
        )

        return request_credentials, request_user

    async def _authenticate_api_key(
        self,
        authorization: APIKeyAuthorization,
        *,
        operation_id: UUID,
        connection_context: ConnectionContext,
    ) -> Tuple[RequestCredentials, RequestUser]:
        validate_api_key(
            authorization.credentials, self._application_context.environment
        )
        user_organization_id = (
            await self._identity_provider.user_organization_id_from_api_key(
                api_key=authorization.credentials,
                operation_id=operation_id,
                connection_context=connection_context,
            )
        )

        user, organization, user_organization = await self._get_credentials(
            user_organization_id.user_id,
            user_organization_id.organization_id,
            operation_id=operation_id,
            connection_context=connection_context,
        )

        return self._build_authentication_component(
            user, organization, user_organization
        )

    async def _authenticate_bearer_token(
        self,
        authorization: BearerTokenAuthorization,
        *,
        operation_id: UUID,
        connection_context: ConnectionContext,
    ) -> Tuple[RequestCredentials, RequestUser]:
        token = authorization.parse_token(key=self._public_key)

        user, organization, user_organization = await self._get_credentials(
            token.sub,
            token.o,
            token.r,
            datetime.fromtimestamp(token.exp, tz=timezone.utc),
            operation_id=operation_id,
            connection_context=connection_context,
        )

        return self._build_authentication_component(
            user, organization, user_organization
        )

    async def _authenticate(
        self,
        authorization: BaseAuthorization,
        *,
        operation_id: UUID,
        connection_context: ConnectionContext,
    ) -> Tuple[RequestCredentials, RequestUser]:
        if is_api_key(authorization):
            return await self._authenticate_api_key(
                authorization,
                operation_id=operation_id,
                connection_context=connection_context,
            )

        if is_bearer_token(authorization):
            return await self._authenticate_bearer_token(
                authorization,
                operation_id=operation_id,
                connection_context=connection_context,
            )

        raise AuthenticationError(f"Unknown authorization type: {type(authorization)}")

    async def _validate_impersonation(
        self,
        operation_id: UUID,
        connection_context: ConnectionContext,
        authentication: BaseAuthentication,
        impersonation: Impersonation,
    ):
        if not is_authenticated(authentication):
            raise AuthenticationError(
                "Can not perform impersonation if user is unauthenticated"
            )

        impersonated_user, impersonated_organization, impersonated_user_organization = (
            await self._get_credentials(
                impersonation.user_id,
                impersonation.organization_id,
                operation_id=operation_id,
                connection_context=connection_context,
            )
        )

        if is_system(authentication):
            if (
                SystemRole.ADMINISTRATOR not in authentication.credentials.roles
                or f"{Domain.SYSTEM}:{SystemRole.ADMINISTRATOR}"
                not in authentication.credentials.scopes
            ):
                raise AuthenticationError(
                    "You must have administrator role to perform impersonation"
                )

            if SystemRole.ADMINISTRATOR in impersonated_user.system_roles:
                raise AuthenticationError(
                    "Can not impersonate user with administrator system role"
                )
        elif is_tenant(authentication):
            if (
                impersonation.organization_id is None
                or impersonated_organization is None
                or impersonated_user_organization is None
            ):
                raise AuthenticationError("Can not impersonate system-level user")

            if (
                authentication.credentials.organization.uuid
                != impersonation.organization_id
            ):
                raise AuthenticationError(
                    "Can not impersonate user from other organization"
                )

            role_scope = (
                (OrganizationRole.OWNER, f"{Domain.TENANT}:{OrganizationRole.OWNER}"),
                (
                    OrganizationRole.ADMINISTRATOR,
                    f"{Domain.TENANT}:{OrganizationRole.ADMINISTRATOR}",
                ),
            )

            valid_role_scope = [
                (
                    role in authentication.credentials.roles
                    and scope in authentication.credentials.scopes
                )
                for role, scope in role_scope
            ]
            if not any(valid_role_scope):
                raise AuthenticationError(
                    "Insufficient tenant-level role and/or scope to perform impersonation"
                )

            if (
                OrganizationRole.OWNER
                in impersonated_user_organization.user_organization_roles
            ):
                raise AuthenticationError("Can not impersonate organization's owner")

    async def authenticate(
        self, conn: HTTPConnection
    ) -> Tuple[RequestCredentials, RequestUser]:
        """Authentication flow"""
        operation_id = getattr(conn.state, "operation_id", None)
        if not operation_id or not isinstance(operation_id, UUID):
            raise AuthenticationError("Unable to determine operation_id")

        connection_context = ConnectionContext.from_connection(conn)
        authorization = BaseAuthorization.extract(conn=conn, auto_error=False)
        impersonation = Impersonation.extract(conn=conn)

        if authorization is None:
            if impersonation is None:
                return RequestCredentials(), RequestUser(False, None, "", "")
            else:
                raise AuthenticationError(
                    "Can not perform impersonation if user is unauthorized"
                )
        else:
            try:
                request_credentials, request_user = await self._authenticate(
                    authorization,
                    operation_id=operation_id,
                    connection_context=connection_context,
                )
            except Exception as e:
                raise AuthenticationError(
                    f"Exception occured while authenticating: {e}"
                ) from e

            authentication = BaseAuthentication(
                credentials=BaseCredentials.model_validate(
                    request_credentials, from_attributes=True
                ),
                user=BaseUser.model_validate(request_user, from_attributes=True),
            )

            if impersonation is not None:
                await self._validate_impersonation(
                    operation_id=operation_id,
                    connection_context=connection_context,
                    authentication=authentication,
                    impersonation=impersonation,
                )

            return request_credentials, request_user
