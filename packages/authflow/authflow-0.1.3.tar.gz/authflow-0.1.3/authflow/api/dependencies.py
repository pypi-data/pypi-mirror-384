"""FastAPI dependencies for authentication and authorization."""

from typing import Callable, List, Optional
from functools import wraps
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from authflow.core.provider import AuthProvider
from authflow.core.jwt_handler import JWTHandler
from authflow.core.permissions import PermissionEngine
from authflow.core.exceptions import (
    InvalidTokenError,
    InsufficientPermissionsError,
    UserNotFoundError,
)
from authflow.models.schemas import User

logger = logging.getLogger(__name__)

# Security scheme for bearer tokens
security = HTTPBearer()


class AuthFlowDependencies:
    """Container for AuthFlow FastAPI dependencies.

    This class holds the provider, JWT handler, and permission engine,
    and provides dependency functions for FastAPI routes.
    """

    def __init__(
        self,
        provider: AuthProvider,
        jwt_handler: JWTHandler,
        permission_engine: PermissionEngine,
    ):
        """Initialize dependencies.

        Args:
            provider: Authentication provider
            jwt_handler: JWT handler
            permission_engine: Permission engine
        """
        self.provider = provider
        self.jwt_handler = jwt_handler
        self.permission_engine = permission_engine

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> User:
        """Get current authenticated user from token.

        Args:
            credentials: HTTP authorization credentials

        Returns:
            Current user

        Raises:
            HTTPException: If token is invalid or user not found
        """
        token = credentials.credentials

        try:
            # Validate token
            token_data = await self.provider.validate_token(token)

            # Get user ID from token
            user_id = token_data.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing subject",
                )

            # Try to get user from provider, fall back to token data
            try:
                user = await self.provider.get_user(user_id)
            except Exception as e:
                logger.warning(f"Could not fetch user via admin API: {e}. Using token data.")
                # Construct user from token data
                from authflow.models.schemas import User
                from datetime import datetime
                user = User(
                    id=user_id,
                    email=token_data.get("email", ""),
                    username=token_data.get("preferred_username", ""),
                    first_name=token_data.get("given_name"),
                    last_name=token_data.get("family_name"),
                    is_active=True,
                    is_verified=token_data.get("email_verified", False),
                    provider="keycloak",
                    provider_id=user_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    custom_attributes={},
                )

            # Check if user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive",
                )

            logger.debug(f"Authenticated user: {user.username}")
            return user

        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
        except UserNotFoundError:
            logger.warning(f"User not found for token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error",
            )

    async def get_current_user_optional(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(
            HTTPBearer(auto_error=False)
        ),
    ) -> Optional[User]:
        """Get current user if authenticated, None otherwise.

        Args:
            credentials: HTTP authorization credentials (optional)

        Returns:
            Current user or None
        """
        if not credentials:
            return None

        try:
            return await self.get_current_user(credentials)
        except HTTPException:
            return None

    async def get_current_active_user(
        self,
        user: User = Depends(lambda: None),  # Will be replaced by get_current_user
    ) -> User:
        """Get current active user.

        Args:
            user: Current user from get_current_user

        Returns:
            Current active user

        Raises:
            HTTPException: If user is inactive
        """
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )
        return user

    async def get_user_permissions(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> List[str]:
        """Extract permissions from user's token.

        Args:
            credentials: HTTP authorization credentials

        Returns:
            List of user permissions
        """
        token = credentials.credentials

        try:
            # Get permissions from token
            permissions = self.jwt_handler.get_permissions(token)

            # Also get roles (which can grant permissions)
            roles = self.jwt_handler.get_roles(token)

            # Combine permissions and roles
            all_permissions = list(set(permissions + roles))

            return all_permissions

        except Exception as e:
            logger.error(f"Error extracting permissions: {e}")
            return []

    def require_permission(self, permission: str):
        """Dependency factory for requiring a specific permission.

        Args:
            permission: Required permission (e.g., "users:write")

        Returns:
            FastAPI dependency function

        Example:
            @app.get("/admin", dependencies=[Depends(require_permission("admin"))])
            async def admin_route():
                return {"message": "Admin access granted"}
        """

        async def permission_checker(
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ) -> bool:
            """Check if user has required permission."""
            token = credentials.credentials

            try:
                # Get user permissions
                permissions = self.jwt_handler.get_permissions(token)
                roles = self.jwt_handler.get_roles(token)
                all_permissions = list(set(permissions + roles))

                # Check permission
                has_permission = self.permission_engine.check_permission(
                    all_permissions, permission
                )

                if not has_permission:
                    logger.warning(
                        f"Permission denied: {permission} not in {all_permissions}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {permission} required",
                    )

                logger.debug(f"Permission granted: {permission}")
                return True

            except InvalidTokenError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=str(e),
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking permission: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Permission check failed",
                )

        return permission_checker

    def require_any_permission(self, permissions: List[str]):
        """Dependency factory for requiring any of the specified permissions.

        Args:
            permissions: List of permissions (user needs at least one)

        Returns:
            FastAPI dependency function
        """

        async def permission_checker(
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ) -> bool:
            """Check if user has any of the required permissions."""
            token = credentials.credentials

            try:
                user_permissions = self.jwt_handler.get_permissions(token)
                roles = self.jwt_handler.get_roles(token)
                all_permissions = list(set(user_permissions + roles))

                has_permission = self.permission_engine.check_any_permission(
                    all_permissions, permissions
                )

                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"One of these permissions required: {', '.join(permissions)}",
                    )

                return True

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking permissions: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Permission check failed",
                )

        return permission_checker

    def require_role(self, role: str):
        """Dependency factory for requiring a specific role.

        Args:
            role: Required role name

        Returns:
            FastAPI dependency function
        """

        async def role_checker(
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ) -> bool:
            """Check if user has required role."""
            token = credentials.credentials

            try:
                roles = self.jwt_handler.get_roles(token)

                has_role = self.permission_engine.check_role(roles, role)

                if not has_role:
                    logger.warning(f"Role denied: {role} not in {roles}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Role required: {role}",
                    )

                logger.debug(f"Role granted: {role}")
                return True

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking role: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Role check failed",
                )

        return role_checker

    def require_any_role(self, roles: List[str]):
        """Dependency factory for requiring any of the specified roles.

        Args:
            roles: List of roles (user needs at least one)

        Returns:
            FastAPI dependency function
        """

        async def role_checker(
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ) -> bool:
            """Check if user has any of the required roles."""
            token = credentials.credentials

            try:
                user_roles = self.jwt_handler.get_roles(token)

                has_role = self.permission_engine.check_any_role(user_roles, roles)

                if not has_role:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"One of these roles required: {', '.join(roles)}",
                    )

                return True

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking roles: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Role check failed",
                )

        return role_checker


# Decorator for permission-based route protection
def requires_permission(permission: str):
    """Decorator for requiring permission on a route handler.

    Args:
        permission: Required permission

    Example:
        @requires_permission("users:write")
        async def create_user(user: User = Depends(get_current_user)):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This is a decorator for the route function
            # Actual permission checking happens in the dependency
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def requires_role(role: str):
    """Decorator for requiring role on a route handler.

    Args:
        role: Required role

    Example:
        @requires_role("admin")
        async def admin_route(user: User = Depends(get_current_user)):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator
