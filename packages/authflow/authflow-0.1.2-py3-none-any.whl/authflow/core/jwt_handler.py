"""JWT validation and token handling."""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import logging

import jwt
from jwt import PyJWTError

from authflow.core.config import TokenConfig
from authflow.core.exceptions import InvalidTokenError

logger = logging.getLogger(__name__)


class JWTHandler:
    """Handle JWT token validation and decoding.

    This handler validates tokens issued by Keycloak or other providers,
    extracting user information and permissions from token claims.
    """

    def __init__(self, config: TokenConfig, public_key: Optional[str] = None):
        """Initialize JWT handler.

        Args:
            config: Token configuration
            public_key: Public key for token validation (optional)
        """
        self.config = config
        self.public_key = public_key
        self.algorithm = config.algorithm

    def decode_token(
        self,
        token: str,
        verify_signature: bool = True,
        verify_exp: bool = True,
    ) -> Dict[str, Any]:
        """Decode and validate JWT token.

        Args:
            token: JWT token string
            verify_signature: Whether to verify signature
            verify_exp: Whether to verify expiration

        Returns:
            Decoded token payload

        Raises:
            InvalidTokenError: If token is invalid or expired
        """
        try:
            options = {
                "verify_signature": verify_signature,
                "verify_exp": verify_exp,
                "verify_aud": False,  # Audience verification optional
            }

            if verify_signature and self.public_key:
                payload = jwt.decode(
                    token,
                    self.public_key,
                    algorithms=[self.algorithm],
                    options=options,
                )
            else:
                # Decode without verification (for development/testing)
                payload = jwt.decode(
                    token,
                    options={"verify_signature": False},
                )

            logger.debug(f"Token decoded successfully for subject: {payload.get('sub')}")
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise InvalidTokenError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            raise InvalidTokenError(f"Error decoding token: {str(e)}")

    def get_user_id(self, token: str) -> str:
        """Extract user ID from token.

        Args:
            token: JWT token string

        Returns:
            User ID (subject claim)
        """
        payload = self.decode_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise InvalidTokenError("Token missing subject claim")

        return user_id

    def get_username(self, token: str) -> Optional[str]:
        """Extract username from token.

        Args:
            token: JWT token string

        Returns:
            Username or None
        """
        payload = self.decode_token(token)
        return payload.get("preferred_username") or payload.get("username")

    def get_email(self, token: str) -> Optional[str]:
        """Extract email from token.

        Args:
            token: JWT token string

        Returns:
            Email or None
        """
        payload = self.decode_token(token)
        return payload.get("email")

    def get_roles(self, token: str) -> list[str]:
        """Extract roles from token.

        Args:
            token: JWT token string

        Returns:
            List of role names
        """
        payload = self.decode_token(token)

        # Try different claim formats
        roles = payload.get("roles", [])

        if not roles:
            # Try realm_access
            realm_access = payload.get("realm_access", {})
            roles = realm_access.get("roles", [])

        if not roles:
            # Try resource_access
            resource_access = payload.get("resource_access", {})
            for client_roles in resource_access.values():
                roles.extend(client_roles.get("roles", []))

        return roles

    def get_groups(self, token: str) -> list[str]:
        """Extract groups from token.

        Args:
            token: JWT token string

        Returns:
            List of group paths
        """
        payload = self.decode_token(token)
        return payload.get("groups", [])

    def get_permissions(self, token: str) -> list[str]:
        """Extract permissions from token.

        Args:
            token: JWT token string

        Returns:
            List of permissions
        """
        payload = self.decode_token(token)

        # Try different claim formats
        permissions = payload.get("permissions", [])

        if not permissions:
            # Try scope claim
            scope = payload.get("scope", "")
            if scope:
                permissions = scope.split()

        return permissions

    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired.

        Args:
            token: JWT token string

        Returns:
            True if expired, False otherwise
        """
        try:
            payload = self.decode_token(token, verify_exp=False)
            exp = payload.get("exp")

            if not exp:
                return False

            expiration = datetime.fromtimestamp(exp)
            return datetime.utcnow() > expiration

        except InvalidTokenError:
            return True

    def get_token_expiration(self, token: str) -> Optional[datetime]:
        """Get token expiration datetime.

        Args:
            token: JWT token string

        Returns:
            Expiration datetime or None
        """
        try:
            payload = self.decode_token(token, verify_exp=False)
            exp = payload.get("exp")

            if exp:
                return datetime.fromtimestamp(exp)

            return None

        except InvalidTokenError:
            return None
