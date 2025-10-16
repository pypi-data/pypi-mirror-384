"""
Module that manages OAuth2 functions for authentication
"""

import enum
import logging

import jwt
from fastapi import HTTPException
from jwt import ExpiredSignatureError, InvalidAudienceError, InvalidIssuerError, InvalidSignatureError, PyJWKClient

from aixtools.utils import config

logger = logging.getLogger(__name__)


class AuthTokenErrorCode(str, enum.Enum):
    """Enum for error codes returned by the AuthTokenError exception."""

    TOKEN_EXPIRED = "Token expired"
    INVALID_AUDIENCE = "Token not for expected audience"
    INVALID_ISSUER = "Token not for expected issuer"
    INVALID_SIGNATURE = "Token signature error"
    INVALID_TOKEN = "Invalid token"
    JWT_ERROR = "Generic JWT error"
    MISSING_GROUPS_ERROR = "Missing authorized groups"
    INVALID_TOKEN_SCOPE = "Token scope does not match configured scope"


class AuthTokenError(Exception):
    """Exception raised for authentication token errors."""

    def __init__(self, error_code: AuthTokenErrorCode, msg: str = None):
        self.error_code = error_code
        error_msg = error_code.value if msg is None else msg
        super().__init__(error_msg)

    def to_http_exception(self, required_scope: str = None, realm: str = "MCP") -> HTTPException:
        """
        Returns an HTTPException with 401 status for all AuthTokenErrorCode,
        including MCP JSON body and WWW-Authenticate header.
        """
        status_code = 401
        www_error = (
            "insufficient_scope" if self.error_code == AuthTokenErrorCode.INVALID_TOKEN_SCOPE else "invalid_token"
        )

        header_value = f'Bearer realm="{realm}", error="{www_error}", error_description="{self.error_code.value}"'
        if self.error_code == AuthTokenErrorCode.INVALID_TOKEN_SCOPE and required_scope:
            header_value += f', scope="{required_scope}"'

        detail = {"error": {"code": self.error_code.name, "message": self.error_code.value}}
        if self.error_code == AuthTokenErrorCode.INVALID_TOKEN_SCOPE and required_scope:
            detail["error"]["required_scope"] = required_scope

        return HTTPException(status_code=status_code, detail=detail, headers={"WWW-Authenticate": header_value})


class AccessTokenVerifier:
    """
    Verifies Microsoft SSO JWT token against the configured Tenant ID, Audience, API ID and Issuer URL.
    """

    def __init__(self):
        tenant_id = config.APP_TENANT_ID
        self.api_id = config.APP_API_ID
        self.issuer_url = f"https://sts.windows.net/{tenant_id}/"

        self.authorized_groups = set(config.APP_AUTHORIZED_GROUPS.split(",")) if config.APP_AUTHORIZED_GROUPS else set()
        if not self.authorized_groups:
            logger.warning("No authorized groups configured")

        # Azure AD endpoints
        jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        self.jwks_client = PyJWKClient(
            uri=jwks_url,
            # cache keys url response to reduce SSO server network calls,
            # as public keys are not expected to change frequently
            cache_jwk_set=True,
            # cache resolved public keys
            cache_keys=True,
            # cache url response for 10 hours
            lifespan=36000,
        )

        logger.info("Using JWKS: %s", jwks_url)

    def verify(self, token: str) -> dict:
        """
        Verifies The JWT access token and returns decoded claims as a dictionary if the token is
        valid, otherwise raises an AuthTokenError
        """
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            logger.info("Verifying JWT token")
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.api_id,
                issuer=self.issuer_url,
                # ensure audience verification is carried out
                options={"verify_aud": True},
            )
            logger.info("Verified JWT token")
            return claims

        except ExpiredSignatureError as e:
            raise AuthTokenError(AuthTokenErrorCode.TOKEN_EXPIRED) from e
        except InvalidAudienceError as e:
            raise AuthTokenError(AuthTokenErrorCode.INVALID_AUDIENCE) from e
        except InvalidIssuerError as e:
            raise AuthTokenError(AuthTokenErrorCode.INVALID_ISSUER) from e
        except InvalidSignatureError as e:
            raise AuthTokenError(AuthTokenErrorCode.INVALID_SIGNATURE) from e
        except jwt.exceptions.PyJWTError as e:
            raise AuthTokenError(AuthTokenErrorCode.JWT_ERROR) from e

    def authorize_claims(self, claims: dict, expected_scope: str):
        """
        Authorize claims based on token scope, expected scope and authorized groups
        claims: decoded JWT claims
        expected_scope: expected scope for the token
        Raises AuthTokenError if authorization fails.
        """
        logger.info("Checking JWT token claims")
        if expected_scope:
            token_scopes = claims.get("scp", "").split()
            if expected_scope not in token_scopes:
                logger.error("Expected token scope: %s, got: %s", expected_scope, token_scopes)
                raise AuthTokenError(
                    AuthTokenErrorCode.INVALID_TOKEN_SCOPE,
                    f"Expected token scope: {expected_scope}, got: {token_scopes}",
                )

        if not self.authorized_groups:
            logger.info("Authorized JWT token, no authorized groups configured")
            return

        groups = claims.get("groups", [])
        if self.authorized_groups & set(groups):
            logger.info("Authorized JWT token, against %s", groups)
            return

        logger.error("Could not find any group in JWT token, matching: %s", self.authorized_groups)
        raise AuthTokenError(
            AuthTokenErrorCode.MISSING_GROUPS_ERROR,
            f"Could not find any group in JWT token, matching: {self.authorized_groups}",
        )
