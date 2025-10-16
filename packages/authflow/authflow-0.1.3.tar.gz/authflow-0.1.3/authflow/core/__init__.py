"""Core authflow modules."""

from authflow.core.config import (
    AuthFlowConfig,
    KeycloakConfig,
    FeaturesConfig,
    RBACConfig,
    PRESET_SIMPLE_AUTH,
    PRESET_MULTI_TENANT,
    PRESET_ENTERPRISE,
)
from authflow.core.provider import AuthProvider
from authflow.core.jwt_handler import JWTHandler
from authflow.core.permissions import PermissionEngine
from authflow.core.exceptions import (
    AuthFlowError,
    AuthenticationError,
    InvalidTokenError,
    InvalidCredentialsError,
    UserError,
    UserNotFoundError,
    UserExistsError,
    OrganizationError,
    OrganizationNotFoundError,
    TeamError,
    TeamNotFoundError,
    RoleError,
    RoleNotFoundError,
    PermissionError,
    PermissionDeniedError,
    InsufficientPermissionsError,
)

__all__ = [
    # Config
    "AuthFlowConfig",
    "KeycloakConfig",
    "FeaturesConfig",
    "RBACConfig",
    "PRESET_SIMPLE_AUTH",
    "PRESET_MULTI_TENANT",
    "PRESET_ENTERPRISE",
    # Core classes
    "AuthProvider",
    "JWTHandler",
    "PermissionEngine",
    # Exceptions
    "AuthFlowError",
    "AuthenticationError",
    "InvalidTokenError",
    "InvalidCredentialsError",
    "UserError",
    "UserNotFoundError",
    "UserExistsError",
    "OrganizationError",
    "OrganizationNotFoundError",
    "TeamError",
    "TeamNotFoundError",
    "RoleError",
    "RoleNotFoundError",
    "PermissionError",
    "PermissionDeniedError",
    "InsufficientPermissionsError",
]
