"""Pydantic schemas for authflow."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Annotated
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, computed_field


# Base Schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# User Schemas
class UserBase(BaseSchema):
    """Base user schema."""

    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format (lenient for development)."""
        if '@' not in v:
            raise ValueError('Email must contain @')
        return v.lower()


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    organization_id: Optional[str] = None
    team_ids: List[str] = Field(default_factory=list)
    role_ids: List[str] = Field(default_factory=list)
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class UserRegister(BaseSchema):
    """Schema for public user registration (limited fields)."""

    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=100, description="Username")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if '@' not in v:
            raise ValueError('Email must contain @')
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


class UserUpdate(BaseSchema):
    """Schema for updating a user."""

    email: Optional[str] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None
    custom_attributes: Optional[Dict[str, Any]] = None


class User(UserBase):
    """Full user schema."""

    id: str
    is_active: bool = True
    is_verified: bool = False
    provider: str
    provider_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def enabled(self) -> bool:
        """Alias for is_active for frontend compatibility."""
        return self.is_active

    @computed_field
    @property
    def email_verified(self) -> bool:
        """Alias for is_verified for frontend compatibility."""
        return self.is_verified


# Organization Schemas
class OrganizationBase(BaseSchema):
    """Base organization schema."""

    name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""

    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class OrganizationUpdate(BaseSchema):
    """Schema for updating an organization."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None


class Organization(OrganizationBase):
    """Full organization schema."""

    id: str
    path: str
    enabled: bool = True
    created_at: datetime
    member_count: int = 0
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


# Team Schemas
class TeamBase(BaseSchema):
    """Base team schema."""

    name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class TeamCreate(TeamBase):
    """Schema for creating a team."""

    organization_id: str
    parent_team_id: Optional[str] = None
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class TeamUpdate(BaseSchema):
    """Schema for updating a team."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None


class Team(TeamBase):
    """Full team schema."""

    id: str
    organization_id: str
    parent_team_id: Optional[str] = None
    path: str
    level: int
    created_at: datetime
    member_count: int = 0
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


# Role Schemas
class RoleBase(BaseSchema):
    """Base role schema."""

    name: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Schema for creating a role."""

    scope: str = "global"  # global, organization, team
    scope_id: Optional[str] = None  # organization_id or team_id
    permissions: List[str] = Field(default_factory=list)
    composite_roles: List[str] = Field(default_factory=list)


class RoleUpdate(BaseSchema):
    """Schema for updating a role."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class Role(RoleBase):
    """Full role schema."""

    id: str
    scope: str
    scope_id: Optional[str] = None
    is_composite: bool = False
    created_at: datetime


# Permission Schemas
class Permission(BaseSchema):
    """Permission schema."""

    id: str
    name: str
    resource: str
    action: str
    description: Optional[str] = None


# Authentication Schemas
class LoginRequest(BaseSchema):
    """Login request schema."""

    username: str  # Can be email or username
    password: str
    organization_id: Optional[str] = None


class TokenResponse(BaseSchema):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


class RefreshRequest(BaseSchema):
    """Refresh token request."""

    refresh_token: str


class LogoutRequest(BaseSchema):
    """Logout request schema."""

    refresh_token: Optional[str] = None


class PasswordResetRequest(BaseSchema):
    """Password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseSchema):
    """Password reset confirmation."""

    token: str
    new_password: str = Field(..., min_length=8)


class PasswordChangeRequest(BaseSchema):
    """Password change request."""

    old_password: str
    new_password: str = Field(..., min_length=8)


# Assignment Schemas
class RoleAssignment(BaseSchema):
    """Role assignment schema."""

    user_id: str
    role_id: str
    scope: str = "global"
    scope_id: Optional[str] = None


class MemberAssignment(BaseSchema):
    """Member assignment to organization/team."""

    user_id: str
    role_ids: List[str] = Field(default_factory=list)


# Session Schema
class Session(BaseSchema):
    """User session schema."""

    id: str
    user_id: str
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    is_active: bool = True


# Pagination Schemas
class PaginationParams(BaseSchema):
    """Pagination parameters."""

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    search: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper."""

    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# Filter Schemas
class UserFilters(PaginationParams):
    """User list filters."""

    organization_id: Optional[str] = None
    team_id: Optional[str] = None
    role_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class OrganizationFilters(PaginationParams):
    """Organization list filters."""

    pass


class TeamFilters(PaginationParams):
    """Team list filters."""

    organization_id: Optional[str] = None
    parent_team_id: Optional[str] = None


class RoleFilters(PaginationParams):
    """Role list filters."""

    scope: Optional[str] = None
    scope_id: Optional[str] = None


# Error Schemas
class ErrorResponse(BaseSchema):
    """Error response schema."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
