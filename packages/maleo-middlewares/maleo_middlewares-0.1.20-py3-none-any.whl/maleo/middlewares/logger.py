import json
from datetime import datetime
from fastapi import status, HTTPException, Request
from typing import Any
from starlette.middleware.base import RequestResponseEndpoint
from maleo.enums.connection import Header
from maleo.logging.enums import Level
from maleo.logging.logger import EnvironmentT, ServiceKeyT, Middleware
from maleo.schemas.application import ApplicationContext, OptApplicationContext
from maleo.schemas.connection import ConnectionContext
from maleo.schemas.response import ResponseContext
from maleo.schemas.error import Factory as ErrorFactory
from maleo.schemas.operation.action.resource import (
    Factory as ResourceOperationActionFactory,
)
from maleo.schemas.operation.context import generate
from maleo.schemas.operation.enums import Origin, Layer, Target
from maleo.schemas.operation.extractor import extract_operation_id
from maleo.schemas.operation.mixins import Timestamp
from maleo.schemas.operation.request import (
    FailedFactory as FailedRequestOperationFactory,
    SuccessfulFactory as SuccessfulRequestOperationFactory,
)
from maleo.schemas.pagination import OptAnyPagination
from maleo.schemas.response import AnyDataResponse, ErrorFactory as ErrorResponseFactory
from maleo.schemas.security.authentication import BaseAuthentication
from maleo.schemas.security.authorization import BaseAuthorization
from maleo.schemas.security.impersonation import Impersonation
from maleo.utils.extractor import ResponseBodyExtractor
from .config import LoggerConfig


def log_request(
    config: LoggerConfig,
    logger: Middleware[EnvironmentT, ServiceKeyT],
    *,
    application_context: OptApplicationContext = None,
):
    application_context = (
        application_context
        if application_context is not None
        else ApplicationContext.from_env()
    )

    operation_context = generate(
        origin=Origin.SERVICE,
        layer=Layer.MIDDLEWARE,
        target=Target.INTERNAL,
    )

    async def dependency(request: Request, call_next: RequestResponseEndpoint):
        response = await call_next(request)

        content_type = response.headers.get(Header.CONTENT_TYPE)

        if content_type is None or (
            content_type is not None and "application/json" not in content_type.lower()
        ):
            return response

        operation_id = extract_operation_id(conn=request)
        operation_action = ResourceOperationActionFactory.extract(
            request=request, strict=False
        )

        executed_at = getattr(request.state, "executed_at", None)
        if not isinstance(executed_at, datetime):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Executed At timestamp is not a datetime {executed_at}",
            )

        completed_at = getattr(request.state, "completed_at", None)
        if not isinstance(completed_at, datetime):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Completed At timestamp is not a datetime {completed_at}",
            )

        duration = getattr(request.state, "duration", None)
        if not isinstance(duration, float):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Duration is not a float {duration}",
            )

        operation_timestamp = Timestamp(
            executed_at=executed_at, completed_at=completed_at, duration=duration
        )

        connection_context = ConnectionContext.from_connection(request)
        authentication: BaseAuthentication = BaseAuthentication.extract(request)
        authorization = BaseAuthorization.extract(request, auto_error=False)
        impersonation = Impersonation.extract(request)

        response_context = ResponseContext(
            status_code=response.status_code,
            media_type=response.media_type,
            headers=response.headers.items(),
        )

        response_body, final_response = await ResponseBodyExtractor.async_extract(
            response
        )
        try:
            json_dict = json.loads(response_body)
            if 200 <= final_response.status_code < 400:
                validated_response = AnyDataResponse[
                    Any, OptAnyPagination, Any
                ].model_validate(json_dict)
                operation = SuccessfulRequestOperationFactory.generate(
                    operation_action,
                    application_context=application_context,
                    id=operation_id,
                    context=operation_context,
                    timestamp=operation_timestamp,
                    summary="Successfully processed request",
                    connection_context=connection_context,
                    authentication=authentication,
                    authorization=authorization,
                    impersonation=impersonation,
                    response=validated_response,
                    response_context=response_context,
                )
                operation.log(logger, Level.INFO)
            elif 400 <= final_response.status_code <= 500:
                response_cls = ErrorResponseFactory.cls_from_code(
                    final_response.status_code
                )
                validated_response = response_cls.model_validate(json_dict)
                error_cls = ErrorFactory.cls_from_code(final_response.status_code)
                operation = FailedRequestOperationFactory[
                    error_cls, response_cls
                ].generate(
                    operation_action,
                    application_context=application_context,
                    id=operation_id,
                    context=operation_context,
                    timestamp=operation_timestamp,
                    summary="Failed processing request",
                    error=error_cls(),
                    connection_context=connection_context,
                    authentication=authentication,
                    authorization=authorization,
                    impersonation=impersonation,
                    response=validated_response,
                    response_context=response_context,
                )
                operation.log(logger, Level.ERROR)
        except Exception:
            decoded_body = response_body.decode(errors="replace")
            if len(decoded_body) > config.max_size:
                decoded_body = (
                    decoded_body[: config.max_size]
                    + f"... [truncated, {len(decoded_body)} bytes total]"
                )
            logger.info(
                f"Successfully processed request with status code {final_response.status_code} but response body can not be loaded to maleo response schema",
                extra={
                    "json_fields": {
                        "response": {
                            "body": decoded_body,
                            "headers": final_response.headers.items(),
                            "media_type": final_response.media_type,
                            "status_code": final_response.status_code,
                        }
                    }
                },
            )

        return final_response

    return dependency
