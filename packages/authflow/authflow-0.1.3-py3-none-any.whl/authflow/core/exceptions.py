"""Custom exceptions for authflow."""


class AuthFlowError(Exception):
    """Base exception for authflow."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# Authentication Exceptions
class AuthenticationError(AuthFlowError):
    """Authentication failed."""

    pass


class InvalidTokenError(AuthFlowError):
    """Token is invalid or expired."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password."""

    pass


# User Exceptions
class UserError(AuthFlowError):
    """Base user exception."""

    pass


class UserNotFoundError(UserError):
    """User not found."""

    pass


class UserExistsError(UserError):
    """User already exists."""

    pass


class UserInactiveError(UserError):
    """User account is inactive."""

    pass


class UserNotVerifiedError(UserError):
    """User email not verified."""

    pass


# Organization Exceptions
class OrganizationError(AuthFlowError):
    """Base organization exception."""

    pass


class OrganizationNotFoundError(OrganizationError):
    """Organization not found."""

    pass


class OrganizationExistsError(OrganizationError):
    """Organization already exists."""

    pass


# Team Exceptions
class TeamError(AuthFlowError):
    """Base team exception."""

    pass


class TeamNotFoundError(TeamError):
    """Team not found."""

    pass


class TeamExistsError(TeamError):
    """Team already exists."""

    pass


class TeamHierarchyError(TeamError):
    """Team hierarchy constraint violated."""

    pass


# Role Exceptions
class RoleError(AuthFlowError):
    """Base role exception."""

    pass


class RoleNotFoundError(RoleError):
    """Role not found."""

    pass


class RoleExistsError(RoleError):
    """Role already exists."""

    pass


# Permission Exceptions
class PermissionError(AuthFlowError):
    """Base permission exception."""

    pass


class PermissionDeniedError(PermissionError):
    """Permission denied."""

    pass


class InsufficientPermissionsError(PermissionError):
    """User lacks required permissions."""

    pass


# Configuration Exceptions
class ConfigurationError(AuthFlowError):
    """Configuration error."""

    pass


class InvalidConfigurationError(ConfigurationError):
    """Invalid configuration."""

    pass


# Provider Exceptions
class ProviderError(AuthFlowError):
    """Provider error."""

    pass


class ProviderConnectionError(ProviderError):
    """Failed to connect to provider."""

    pass


class ProviderAPIError(ProviderError):
    """Provider API error."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


# Validation Exceptions
class ValidationError(AuthFlowError):
    """Validation error."""

    pass


# Session Exceptions
class SessionError(AuthFlowError):
    """Session error."""

    pass


class SessionExpiredError(SessionError):
    """Session has expired."""

    pass


class SessionNotFoundError(SessionError):
    """Session not found."""

    pass
