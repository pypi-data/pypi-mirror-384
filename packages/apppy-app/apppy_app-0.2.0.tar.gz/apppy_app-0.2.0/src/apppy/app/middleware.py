import uuid
from contextlib import suppress

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi_another_jwt_auth import AuthJWT as JWT
from pydantic import Field
from starlette.middleware.base import BaseHTTPMiddleware as StarletteHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware as StarletteSessionMiddleware

from apppy.auth.errors.service import (
    ServiceKeyAlgorithmMissingError,
)
from apppy.auth.jwks import JwkInfo, JwksAuthStorage
from apppy.auth.jwt import JwtAuthContext, JwtAuthSettings
from apppy.env import Env, EnvSettings
from apppy.fastql.errors import GraphQLError
from apppy.logger.storage import LoggingStorage


class JwtAuthMiddleware(StarletteHTTPMiddleware):
    """
    A middleware instance which analyzes the request headers,
    creates a JwtAuthContext, and set it in thread local storage
    """

    def __init__(
        self,
        fastapi: FastAPI,
        jwt_auth_settings: JwtAuthSettings,
        jwks_auth_storage: JwksAuthStorage,
    ):
        super().__init__(app=fastapi)
        self._jwks_auth_storage = jwks_auth_storage

        # Load the global JWT configuration JWT.
        # This is used for processing user requests below.
        @JWT.load_config
        def load_config_jwtauth_global():
            return jwt_auth_settings

    async def dispatch(self, request: Request, call_next):
        jwt_headers: dict | None = JwtAuthContext.peek(request)

        try:
            if jwt_headers is not None and "kid" in jwt_headers:
                # CASE: A Service is making the request
                jwk_info: JwkInfo = self._jwks_auth_storage.get_jwk(jwt_headers["kid"])

                if "alg" not in jwt_headers:
                    raise ServiceKeyAlgorithmMissingError()

                public_key = jwk_info.jwk.get_op_key("verify")
                auth_ctx = JwtAuthContext.from_service_request(
                    request, jwt_headers["alg"], public_key
                )
            else:
                # CASE: A User is making the request
                # Instead of using the JWKS storage, we'll
                # use the global configuration loaded in __init__
                auth_ctx = JwtAuthContext.from_user_request(request)
        except GraphQLError as e:
            # If we encounter an error while preprocessing the
            # auth context, we'll capture the error and keep going. The
            # authentication and authorization permission are designed
            # to handle this and raise the appropriate error.
            auth_ctx = JwtAuthContext(preprocessing_error=e)

        JwtAuthContext.set_current_auth_context(auth_ctx)
        response = await call_next(request)
        return response


class RequestIdMiddleware(StarletteHTTPMiddleware):
    def __init__(self, fastapi: FastAPI, header_name: str = "X-Request-ID"):
        super().__init__(fastapi)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())

        # Store in LoggingStorage (thread-local)
        with suppress(RuntimeError):
            LoggingStorage.get_global().add_request_id(request_id)

        response = await call_next(request)

        # Cleanup after the response has been sent
        def cleanup_logging_storage():
            with suppress(RuntimeError):
                LoggingStorage.get_global().reset()

        # Ensure background task manager exists
        if response.background is None:
            response.background = BackgroundTasks()

        response.background.add_task(cleanup_logging_storage)
        response.headers.setdefault(self.header_name, request_id)

        return response


class SessionMiddlewareSettings(EnvSettings):
    # SESSION_MIDDLEWARE_SECRET_KEY
    secret_key: str = Field(exclude=True)

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix="SESSION_MIDDLEWARE")


class SessionMiddleware(StarletteSessionMiddleware):
    """
    Simple wrapper around Starlette's SessionMiddleware to allow for
    injected settings via EnvSettings
    """

    def __init__(self, fastapi: FastAPI, settings: SessionMiddlewareSettings):
        super().__init__(app=fastapi, secret_key=settings.secret_key)
