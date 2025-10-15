"""Abstract authentication provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from authflow.models.schemas import (
    User,
    UserCreate,
    UserUpdate,
    UserFilters,
    Organization,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationFilters,
    Team,
    TeamCreate,
    TeamUpdate,
    TeamFilters,
    Role,
    RoleCreate,
    RoleUpdate,
    RoleFilters,
    TokenResponse,
    LoginRequest,
    Session,
    PaginatedResponse,
)


class AuthProvider(ABC):
    """Abstract base class for authentication providers.

    This interface defines all operations that an authentication provider
    must implement. Concrete implementations (KeycloakProvider, Auth0Provider, etc.)
    should inherit from this class and implement all abstract methods.
    """

    # ==================== Authentication Methods ====================

    @abstractmethod
    async def authenticate(self, credentials: LoginRequest) -> TokenResponse:
        """Authenticate user with credentials.

        Args:
            credentials: Login credentials (username/email and password)

        Returns:
            TokenResponse containing access_token, refresh_token, and user info

        Raises:
            AuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New TokenResponse with refreshed tokens

        Raises:
            InvalidTokenError: If refresh token is invalid or expired
        """
        pass

    @abstractmethod
    async def logout(self, refresh_token: Optional[str] = None) -> bool:
        """Logout user and invalidate tokens.

        Args:
            refresh_token: Refresh token to invalidate

        Returns:
            True if logout successful
        """
        pass

    @abstractmethod
    async def validate_token(self, token: str) -> Dict:
        """Validate and decode access token.

        Args:
            token: Access token to validate

        Returns:
            Decoded token claims

        Raises:
            InvalidTokenError: If token is invalid or expired
        """
        pass

    # ==================== User Management Methods ====================

    @abstractmethod
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user

        Raises:
            UserExistsError: If user already exists
            ValidationError: If user data is invalid
        """
        pass

    @abstractmethod
    async def get_user(self, user_id: str) -> User:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        pass

    @abstractmethod
    async def get_user_by_username(self, username: str) -> User:
        """Get user by username.

        Args:
            username: Username

        Returns:
            User object

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> User:
        """Get user by email.

        Args:
            email: Email address

        Returns:
            User object

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        pass

    @abstractmethod
    async def list_users(self, filters: UserFilters) -> PaginatedResponse:
        """List users with pagination and filters.

        Args:
            filters: Pagination and filter parameters

        Returns:
            Paginated list of users
        """
        pass

    @abstractmethod
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """Update user.

        Args:
            user_id: User ID
            user_data: Update data

        Returns:
            Updated user

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        pass

    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete user.

        Args:
            user_id: User ID

        Returns:
            True if deleted successfully

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        pass

    @abstractmethod
    async def set_user_password(self, user_id: str, password: str, temporary: bool = False) -> bool:
        """Set user password.

        Args:
            user_id: User ID
            password: New password
            temporary: Whether password is temporary (user must change on next login)

        Returns:
            True if successful

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        pass

    @abstractmethod
    async def send_verification_email(self, user_id: str) -> bool:
        """Send email verification to user.

        Args:
            user_id: User ID

        Returns:
            True if email sent successfully
        """
        pass

    @abstractmethod
    async def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get user's active sessions.

        Args:
            user_id: User ID

        Returns:
            List of active sessions
        """
        pass

    @abstractmethod
    async def revoke_session(self, user_id: str, session_id: str) -> bool:
        """Revoke a user session.

        Args:
            user_id: User ID
            session_id: Session ID

        Returns:
            True if revoked successfully
        """
        pass

    # ==================== Organization Management Methods ====================

    @abstractmethod
    async def create_organization(self, org_data: OrganizationCreate) -> Organization:
        """Create a new organization.

        Args:
            org_data: Organization creation data

        Returns:
            Created organization
        """
        pass

    @abstractmethod
    async def get_organization(self, org_id: str) -> Organization:
        """Get organization by ID.

        Args:
            org_id: Organization ID

        Returns:
            Organization object

        Raises:
            OrganizationNotFoundError: If organization doesn't exist
        """
        pass

    @abstractmethod
    async def list_organizations(self, filters: OrganizationFilters) -> PaginatedResponse:
        """List organizations with pagination.

        Args:
            filters: Pagination and filter parameters

        Returns:
            Paginated list of organizations
        """
        pass

    @abstractmethod
    async def update_organization(self, org_id: str, org_data: OrganizationUpdate) -> Organization:
        """Update organization.

        Args:
            org_id: Organization ID
            org_data: Update data

        Returns:
            Updated organization
        """
        pass

    @abstractmethod
    async def delete_organization(self, org_id: str) -> bool:
        """Delete organization.

        Args:
            org_id: Organization ID

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    async def add_organization_member(self, org_id: str, user_id: str, role_ids: List[str] = None) -> bool:
        """Add user to organization.

        Args:
            org_id: Organization ID
            user_id: User ID
            role_ids: Optional list of role IDs to assign

        Returns:
            True if added successfully
        """
        pass

    @abstractmethod
    async def remove_organization_member(self, org_id: str, user_id: str) -> bool:
        """Remove user from organization.

        Args:
            org_id: Organization ID
            user_id: User ID

        Returns:
            True if removed successfully
        """
        pass

    @abstractmethod
    async def list_organization_members(self, org_id: str, filters: UserFilters) -> PaginatedResponse:
        """List organization members.

        Args:
            org_id: Organization ID
            filters: Pagination and filter parameters

        Returns:
            Paginated list of users
        """
        pass

    # ==================== Team Management Methods ====================

    @abstractmethod
    async def create_team(self, team_data: TeamCreate) -> Team:
        """Create a new team.

        Args:
            team_data: Team creation data

        Returns:
            Created team
        """
        pass

    @abstractmethod
    async def get_team(self, team_id: str) -> Team:
        """Get team by ID.

        Args:
            team_id: Team ID

        Returns:
            Team object

        Raises:
            TeamNotFoundError: If team doesn't exist
        """
        pass

    @abstractmethod
    async def list_teams(self, filters: TeamFilters) -> PaginatedResponse:
        """List teams with pagination and filters.

        Args:
            filters: Pagination and filter parameters

        Returns:
            Paginated list of teams
        """
        pass

    @abstractmethod
    async def update_team(self, team_id: str, team_data: TeamUpdate) -> Team:
        """Update team.

        Args:
            team_id: Team ID
            team_data: Update data

        Returns:
            Updated team
        """
        pass

    @abstractmethod
    async def delete_team(self, team_id: str) -> bool:
        """Delete team.

        Args:
            team_id: Team ID

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    async def add_team_member(self, team_id: str, user_id: str, role_ids: List[str] = None) -> bool:
        """Add user to team.

        Args:
            team_id: Team ID
            user_id: User ID
            role_ids: Optional list of role IDs to assign

        Returns:
            True if added successfully
        """
        pass

    @abstractmethod
    async def remove_team_member(self, team_id: str, user_id: str) -> bool:
        """Remove user from team.

        Args:
            team_id: Team ID
            user_id: User ID

        Returns:
            True if removed successfully
        """
        pass

    @abstractmethod
    async def list_team_members(self, team_id: str, filters: UserFilters) -> PaginatedResponse:
        """List team members.

        Args:
            team_id: Team ID
            filters: Pagination and filter parameters

        Returns:
            Paginated list of users
        """
        pass

    # ==================== Role Management Methods ====================

    @abstractmethod
    async def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role.

        Args:
            role_data: Role creation data

        Returns:
            Created role
        """
        pass

    @abstractmethod
    async def get_role(self, role_id: str) -> Role:
        """Get role by ID.

        Args:
            role_id: Role ID

        Returns:
            Role object

        Raises:
            RoleNotFoundError: If role doesn't exist
        """
        pass

    @abstractmethod
    async def list_roles(self, filters: RoleFilters) -> PaginatedResponse:
        """List roles with pagination and filters.

        Args:
            filters: Pagination and filter parameters

        Returns:
            Paginated list of roles
        """
        pass

    @abstractmethod
    async def update_role(self, role_id: str, role_data: RoleUpdate) -> Role:
        """Update role.

        Args:
            role_id: Role ID
            role_data: Update data

        Returns:
            Updated role
        """
        pass

    @abstractmethod
    async def delete_role(self, role_id: str) -> bool:
        """Delete role.

        Args:
            role_id: Role ID

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    async def assign_role_to_user(self, user_id: str, role_id: str, scope_id: Optional[str] = None) -> bool:
        """Assign role to user.

        Args:
            user_id: User ID
            role_id: Role ID
            scope_id: Optional organization or team ID for scoped roles

        Returns:
            True if assigned successfully
        """
        pass

    @abstractmethod
    async def remove_role_from_user(self, user_id: str, role_id: str, scope_id: Optional[str] = None) -> bool:
        """Remove role from user.

        Args:
            user_id: User ID
            role_id: Role ID
            scope_id: Optional organization or team ID for scoped roles

        Returns:
            True if removed successfully
        """
        pass

    @abstractmethod
    async def get_user_roles(self, user_id: str, scope: Optional[str] = None, scope_id: Optional[str] = None) -> List[Role]:
        """Get user's roles.

        Args:
            user_id: User ID
            scope: Optional scope filter (global, organization, team)
            scope_id: Optional scope ID (organization or team ID)

        Returns:
            List of roles
        """
        pass

    @abstractmethod
    async def check_user_permission(self, user_id: str, permission: str, scope_id: Optional[str] = None) -> bool:
        """Check if user has a specific permission.

        Args:
            user_id: User ID
            permission: Permission string (e.g., "contracts:write")
            scope_id: Optional organization or team ID

        Returns:
            True if user has permission
        """
        pass
