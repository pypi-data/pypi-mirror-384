import contextvars
import datetime
import logging
from dataclasses import dataclass
from typing import Any, Literal

from fastapi import HTTPException, Request
from fastapi_another_jwt_auth import AuthJWT as JWT
from pydantic import Field

from apppy.auth import convert_token_to_jwt, extract_jwt_from_request
from apppy.env import Env, EnvSettings
from apppy.fastql.errors import GraphQLClientError, GraphQLError, GraphQLServerError
from apppy.fastql.permissions import GraphQLPermission
from apppy.logger import WithLogger

JwtAuthSubjectType = Literal["user", "service"]

# Define a context variable per key
_current_auth_context: contextvars.ContextVar["JwtAuthContext"] = contextvars.ContextVar(
    "_current_auth_context"
)

# This breaks the typically logger pattern
# but logging is needed in static methods
_logger = logging.getLogger("apppy.auth.jwt.JwtAuthContext")


class JwtAuthSettings(EnvSettings):
    # The names here must match the names found in
    # fastapi_another_jwt_auth.AuthConfig.load_config

    # JWTAUTH_DECODE_AUDIENCE
    authjwt_decode_audience: str = Field(default="authenticated")
    # JWTAUTH_ENCODE_ISSUER
    authjwt_encode_issuer: str = Field()
    # JWTAUTH_SECRET_KEY
    authjwt_secret_key: str = Field(exclude=True)

    def __init__(self, env: Env) -> None:
        super().__init__(env=env, domain_prefix=None)


@dataclass
class JwtAuthContext(WithLogger):
    # In some cases we'll encounter an error
    # while preprocessing a JwtAuthContext. The classic
    # example of this is attempting a service authentication
    # when service authentication is disabled. For those cases,
    # we'll store the preprocessing error code here so that we
    # can return the appropriate error type to the client.
    preprocessing_error: GraphQLError | None = None

    has_token: bool = False
    is_token_well_formed: bool = False
    expires_at: int = 0
    issued_at: int = 0

    auth_session_id: str | None = None
    auth_subject_id: str | None = None  # user_id or service_id
    auth_subject_type: JwtAuthSubjectType | None = None

    iam_enabled: bool = False
    iam_revoked_at: datetime.datetime | None = None
    iam_role: str | None = None
    iam_scopes: list[str] | None = None

    raw_claims: dict[str, Any] | None = None

    def check_graphql_permissions(self, *permissions: GraphQLPermission) -> "JwtAuthContext":
        for perm in permissions:
            if not perm.has_permission(source=None, info=None, auth_ctx=self):  # type: ignore[arg-type]
                raise perm.graphql_client_error_class(*perm.graphql_client_error_args())  # type: ignore[missing-argument]

        return self

    def check_http_permissions(self, *permissions: GraphQLPermission) -> "JwtAuthContext":
        # Here we'll get the context for the appropriate GraphQL permissions
        # but then raise an HTTP exception rather than a typed GraphQL exception
        for perm in permissions:
            try:
                if not perm.has_permission(source=None, info=None, auth_ctx=self):  # type: ignore[arg-type]
                    raise HTTPException(status_code=401)
            except GraphQLClientError as e:
                raise HTTPException(status_code=401) from e
            except GraphQLServerError as e:
                raise HTTPException(status_code=500) from e

        return self

    @staticmethod
    def current_auth_context() -> "JwtAuthContext":
        return _current_auth_context.get()

    @staticmethod
    def set_current_auth_context(auth_ctx: "JwtAuthContext") -> None:
        _current_auth_context.set(auth_ctx)

    @staticmethod
    def _create_service_context(claims) -> "JwtAuthContext":
        if claims is None:
            _logger.warning("No claims found in service JWT")
            return JwtAuthContext(has_token=False)
        elif "service_metadata" not in claims:
            _logger.warning("No service_metadata found in service JWT.")
            return JwtAuthContext(has_token=True, is_token_well_formed=False)

        service_metadata: dict[str, Any] = claims["service_metadata"]  # type: ignore[invalid-assignment]
        iam_metadata: dict[str, Any] = service_metadata.get("iam_metadata", {})

        return JwtAuthContext(
            has_token=True,
            is_token_well_formed=True,
            expires_at=claims["exp"],  # type: ignore[invalid-argument-type]
            issued_at=claims["iat"],  # type: ignore[invalid-argument-type]
            auth_session_id=None,
            auth_subject_id=service_metadata.get("service_name"),
            auth_subject_type="service",
            iam_enabled=True,
            iam_revoked_at=None,
            iam_role=iam_metadata.get("role"),
            iam_scopes=iam_metadata.get("scopes", []),
            raw_claims=claims,
        )

    @staticmethod
    def _create_user_context(claims) -> "JwtAuthContext":
        if claims is None:
            _logger.warning("No claims found in user JWT")
            return JwtAuthContext(has_token=False)
        elif "user_metadata" not in claims:
            _logger.warning("No user_metadata found in user JWT.")
            return JwtAuthContext(has_token=True, is_token_well_formed=False)

        user_metadata: dict[str, Any] = claims["user_metadata"]  # type: ignore[invalid-assignment]
        iam_metadata: dict[str, Any] = user_metadata.get("iam_metadata", {})
        return JwtAuthContext(
            has_token=True,
            is_token_well_formed=True,
            expires_at=claims["exp"],  # type: ignore[invalid-argument-type]
            issued_at=claims["iat"],  # type: ignore[invalid-argument-type]
            auth_session_id=claims.get("session_id"),  # type: ignore[invalid-argument-type]
            auth_subject_id=user_metadata.get("subject_id"),
            auth_subject_type="user",
            iam_enabled=iam_metadata.get("enabled", False),
            iam_revoked_at=iam_metadata.get("revoked_at"),
            iam_role=iam_metadata.get("role"),
            iam_scopes=iam_metadata.get("scopes", []),
            raw_claims=claims,
        )

    @staticmethod
    def from_jwt(jwt_: JWT) -> "JwtAuthContext":
        if not jwt_._token:
            return JwtAuthContext(has_token=False)

        claims = jwt_.get_raw_jwt()
        if claims is None:
            _logger.warning("No claims found in JWT")
            return JwtAuthContext(has_token=False)

        if "user_metadata" in claims:
            return JwtAuthContext._create_user_context(claims)
        elif "service_metadata" in claims:
            return JwtAuthContext._create_service_context(claims)

        _logger.warning(
            "No user_metadata nor kid found in JWT. We do not know if this is a user or a service"
        )
        return JwtAuthContext(has_token=True, is_token_well_formed=False)

    @staticmethod
    def from_service_request(
        request: Request,
        algorithm: str,
        public_key: str,
    ) -> "JwtAuthContext":
        jwt_ = extract_jwt_from_request(request)
        jwt_._algorithm = algorithm
        jwt_._public_key = public_key

        claims = jwt_.get_raw_jwt()
        return JwtAuthContext._create_service_context(claims)

    @staticmethod
    def from_user_request(request: Request) -> "JwtAuthContext":
        jwt_ = extract_jwt_from_request(request)

        claims = jwt_.get_raw_jwt()
        return JwtAuthContext._create_user_context(claims)

    @staticmethod
    def from_token(token: str) -> "JwtAuthContext":
        jwt_: JWT = convert_token_to_jwt(token)
        return JwtAuthContext.from_jwt(jwt_)

    @staticmethod
    def peek(request: Request) -> dict | None:
        jwt_: JWT = extract_jwt_from_request(request)
        if jwt_._token is None:
            return None

        headers = jwt_.get_unverified_jwt_headers()
        return headers
