"""Keycloak authentication provider implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError

from authflow.core.provider import AuthProvider
from authflow.core.config import KeycloakConfig
from authflow.core.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserNotFoundError,
    OrganizationNotFoundError,
    TeamNotFoundError,
)
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
from authflow.utils.keycloak_admin import KeycloakAdminClient

logger = logging.getLogger(__name__)


class KeycloakProvider(AuthProvider):
    """Keycloak implementation of AuthProvider.

    This provider uses Keycloak as the backend for all authentication
    and authorization operations, mapping Keycloak concepts to AuthFlow concepts:
    - Groups → Organizations and Teams
    - Realm Roles → Roles
    - User Attributes → Custom Fields
    """

    def __init__(self, config: KeycloakConfig):
        """Initialize Keycloak provider.

        Args:
            config: Keycloak configuration
        """
        self.config = config
        self.admin = KeycloakAdminClient(config)

        # Initialize OpenID Connect client for authentication
        self.oidc = KeycloakOpenID(
            server_url=config.url,
            client_id=config.client_id,
            realm_name=config.realm,
            client_secret_key=config.client_secret,
            verify=config.verify_ssl,
        )

        logger.info(f"Initialized KeycloakProvider for realm: {config.realm}")

    # ==================== Authentication Methods ====================

    async def authenticate(self, credentials: LoginRequest) -> TokenResponse:
        """Authenticate user with credentials."""
        try:
            # Get token from Keycloak
            token_response = self.oidc.token(
                username=credentials.username,
                password=credentials.password,
            )

            # Get user info from token
            userinfo = self.oidc.userinfo(token_response["access_token"])

            # Decode the access token to extract permissions and roles
            import jwt
            decoded_token = jwt.decode(
                token_response["access_token"],
                options={"verify_signature": False}  # Already validated by Keycloak
            )

            # Extract roles from token - check multiple locations
            roles = decoded_token.get("roles", [])  # Top-level roles claim (custom mapper)
            if not roles and "realm_access" in decoded_token:
                roles.extend(decoded_token["realm_access"].get("roles", []))
            if not roles and "resource_access" in decoded_token:
                for client_roles in decoded_token["resource_access"].values():
                    roles.extend(client_roles.get("roles", []))

            # Extract groups from token
            groups = decoded_token.get("groups", [])

            # Get permissions from role attributes
            permissions = []
            try:
                for role_name in roles:
                    role_data = await self.admin.get_realm_role(role_name)
                    role_permissions = role_data.get("attributes", {}).get("permissions", [])
                    permissions.extend(role_permissions)
                # Remove duplicates
                permissions = list(set(permissions))
                logger.info(f"Extracted {len(permissions)} permissions from {len(roles)} roles")
            except Exception as e:
                logger.warning(f"Could not fetch role permissions: {e}")
                # Fallback to permissions from token if available
                permissions = decoded_token.get("permissions", [])

            # Try to get full user data from admin API, fall back to userinfo if unavailable
            try:
                user_data = await self.admin.get_user(userinfo["sub"])
            except Exception as e:
                logger.warning(f"Could not fetch full user data via admin API: {e}. Using userinfo instead.")
                # Use userinfo as fallback - map standard OIDC claims to user data
                user_data = {
                    "id": userinfo.get("sub"),
                    "username": userinfo.get("preferred_username"),
                    "email": userinfo.get("email"),
                    "firstName": userinfo.get("given_name"),
                    "lastName": userinfo.get("family_name"),
                    "enabled": True,
                    "emailVerified": userinfo.get("email_verified", False),
                    "attributes": {},
                }

            # Ensure attributes exist
            if "attributes" not in user_data:
                user_data["attributes"] = {}

            # Add permissions, roles, and groups from token to attributes
            user_data["attributes"]["permissions"] = permissions
            user_data["attributes"]["roles"] = roles
            user_data["attributes"]["groups"] = groups

            # Convert to User model
            user = self._map_keycloak_user(user_data)

            return TokenResponse(
                access_token=token_response["access_token"],
                refresh_token=token_response["refresh_token"],
                token_type="bearer",
                expires_in=token_response["expires_in"],
                user=user,
            )

        except KeycloakError as e:
            logger.error(f"Authentication failed: {e}")
            if "invalid_grant" in str(e):
                raise InvalidCredentialsError("Invalid username or password")
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        try:
            token_response = self.oidc.refresh_token(refresh_token)

            # Get user info
            userinfo = self.oidc.userinfo(token_response["access_token"])

            # Decode the access token to extract permissions and roles
            import jwt
            decoded_token = jwt.decode(
                token_response["access_token"],
                options={"verify_signature": False}  # Already validated by Keycloak
            )

            # Extract roles from token - check multiple locations
            roles = decoded_token.get("roles", [])  # Top-level roles claim (custom mapper)
            if not roles and "realm_access" in decoded_token:
                roles.extend(decoded_token["realm_access"].get("roles", []))
            if not roles and "resource_access" in decoded_token:
                for client_roles in decoded_token["resource_access"].values():
                    roles.extend(client_roles.get("roles", []))

            # Extract groups from token
            groups = decoded_token.get("groups", [])

            # Get permissions from role attributes
            permissions = []
            try:
                for role_name in roles:
                    role_data = await self.admin.get_realm_role(role_name)
                    role_permissions = role_data.get("attributes", {}).get("permissions", [])
                    permissions.extend(role_permissions)
                # Remove duplicates
                permissions = list(set(permissions))
                logger.info(f"Extracted {len(permissions)} permissions from {len(roles)} roles")
            except Exception as e:
                logger.warning(f"Could not fetch role permissions: {e}")
                # Fallback to permissions from token if available
                permissions = decoded_token.get("permissions", [])

            # Try to get full user data from admin API, fall back to userinfo if unavailable
            try:
                user_data = await self.admin.get_user(userinfo["sub"])
            except Exception as e:
                logger.warning(f"Could not fetch full user data via admin API during token refresh: {e}. Using userinfo instead.")
                user_data = {
                    "id": userinfo.get("sub"),
                    "username": userinfo.get("preferred_username"),
                    "email": userinfo.get("email"),
                    "firstName": userinfo.get("given_name"),
                    "lastName": userinfo.get("family_name"),
                    "enabled": True,
                    "emailVerified": userinfo.get("email_verified", False),
                    "attributes": {},
                }

            # Ensure attributes exist
            if "attributes" not in user_data:
                user_data["attributes"] = {}

            # Add permissions, roles, and groups from token to attributes
            user_data["attributes"]["permissions"] = permissions
            user_data["attributes"]["roles"] = roles
            user_data["attributes"]["groups"] = groups

            user = self._map_keycloak_user(user_data)

            return TokenResponse(
                access_token=token_response["access_token"],
                refresh_token=token_response["refresh_token"],
                token_type="bearer",
                expires_in=token_response["expires_in"],
                user=user,
            )

        except KeycloakError as e:
            logger.error(f"Token refresh failed: {e}")
            raise InvalidTokenError("Invalid or expired refresh token")

    async def logout(self, refresh_token: Optional[str] = None) -> bool:
        """Logout user and invalidate tokens."""
        try:
            if refresh_token:
                self.oidc.logout(refresh_token)
            return True
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return False

    async def validate_token(self, token: str) -> Dict:
        """Validate and decode access token."""
        try:
            # Use PyJWT directly for token validation
            import jwt
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend

            # Get public key from Keycloak
            public_key_str = self.oidc.public_key()

            # Convert to PEM format if needed
            if not public_key_str.startswith('-----BEGIN'):
                # Keycloak returns the key without PEM headers, add them
                public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{public_key_str}\n-----END PUBLIC KEY-----"
            else:
                public_key_pem = public_key_str

            token_info = jwt.decode(
                token,
                public_key_pem,
                algorithms=["RS256"],
                options={"verify_signature": True, "verify_aud": False, "verify_exp": True},
            )
            return token_info
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            raise InvalidTokenError("Invalid or expired token")

    # ==================== User Management Methods ====================

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Prepare custom attributes
        attributes = user_data.custom_attributes or {}

        user_id = await self.admin.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            enabled=True,
            email_verified=False,
            attributes=attributes,
        )

        # Add user to organization if specified
        if user_data.organization_id:
            await self.admin.add_user_to_group(user_id, user_data.organization_id)

        # Add user to teams if specified
        for team_id in user_data.team_ids:
            await self.admin.add_user_to_group(user_id, team_id)

        # Assign roles if specified
        if user_data.role_ids:
            await self.admin.assign_realm_roles_to_user(user_id, user_data.role_ids)

        # Get and return created user
        keycloak_user = await self.admin.get_user(user_id)
        return self._map_keycloak_user(keycloak_user)

    async def get_user(self, user_id: str) -> User:
        """Get user by ID."""
        keycloak_user = await self.admin.get_user(user_id)
        return self._map_keycloak_user(keycloak_user)

    async def get_user_by_username(self, username: str) -> User:
        """Get user by username."""
        keycloak_user = await self.admin.get_user_by_username(username)
        if not keycloak_user:
            raise UserNotFoundError(f"User not found: {username}")
        return self._map_keycloak_user(keycloak_user)

    async def get_user_by_email(self, email: str) -> User:
        """Get user by email."""
        keycloak_user = await self.admin.get_user_by_email(email)
        if not keycloak_user:
            raise UserNotFoundError(f"User not found: {email}")
        return self._map_keycloak_user(keycloak_user)

    async def list_users(self, filters: UserFilters) -> PaginatedResponse:
        """List users with pagination and filters."""
        # Calculate offset
        offset = (filters.page - 1) * filters.page_size

        # Build query
        query = {}
        if filters.search:
            query["search"] = filters.search

        # Get users from Keycloak
        keycloak_users = await self.admin.list_users(
            first=offset,
            max_results=filters.page_size,
            **query,
        )

        # Map to User models
        users = [self._map_keycloak_user(u) for u in keycloak_users]

        # Note: Keycloak doesn't provide total count easily, estimate it
        total = len(users) if len(users) < filters.page_size else offset + len(users) + 1

        return PaginatedResponse(
            items=users,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=(total + filters.page_size - 1) // filters.page_size,
        )

    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """Update user."""
        update_payload = {}

        if user_data.email:
            update_payload["email"] = user_data.email
        if user_data.username:
            update_payload["username"] = user_data.username
        if user_data.first_name:
            update_payload["firstName"] = user_data.first_name
        if user_data.last_name:
            update_payload["lastName"] = user_data.last_name
        if user_data.is_active is not None:
            update_payload["enabled"] = user_data.is_active
        if user_data.custom_attributes:
            update_payload["attributes"] = user_data.custom_attributes

        await self.admin.update_user(user_id, update_payload)

        # Get and return updated user
        keycloak_user = await self.admin.get_user(user_id)
        return self._map_keycloak_user(keycloak_user)

    async def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        await self.admin.delete_user(user_id)
        return True

    async def set_user_password(self, user_id: str, password: str, temporary: bool = False) -> bool:
        """Set user password."""
        await self.admin.set_user_password(user_id, password, temporary)
        return True

    async def send_verification_email(self, user_id: str) -> bool:
        """Send email verification to user."""
        await self.admin.send_verify_email(user_id)
        return True

    async def send_password_reset_email(self, user_id: str) -> bool:
        """Send password reset email to user."""
        await self.admin.send_password_reset_email(user_id)
        return True

    async def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get user's active sessions."""
        keycloak_sessions = await self.admin.get_user_sessions(user_id)

        sessions = []
        for ks in keycloak_sessions:
            session = Session(
                id=ks.get("id", ""),
                user_id=user_id,
                device_info=ks.get("clients", {}).get("clientId", ""),
                ip_address=ks.get("ipAddress", ""),
                created_at=datetime.fromtimestamp(ks.get("start", 0) / 1000),
                expires_at=datetime.fromtimestamp(
                    (ks.get("start", 0) + ks.get("expires", 0)) / 1000
                ),
                is_active=True,
            )
            sessions.append(session)

        return sessions

    async def revoke_session(self, user_id: str, session_id: str) -> bool:
        """Revoke a user session."""
        # Note: Keycloak doesn't have direct session revocation by ID
        # This would need to be implemented via admin API extensions
        logger.warning("Session revocation not fully implemented for Keycloak")
        return True

    # ==================== Organization Management (Groups) ====================

    async def create_organization(self, org_data: OrganizationCreate) -> Organization:
        """Create a new organization (top-level group)."""
        attributes = {
            "organization_id": [org_data.name.lower().replace(" ", "-")],
            "display_name": [org_data.display_name or org_data.name],
        }

        if org_data.description:
            attributes["description"] = [org_data.description]

        if org_data.custom_attributes:
            attributes.update(org_data.custom_attributes)

        group_id = await self.admin.create_group(
            name=org_data.name,
            attributes=attributes,
        )

        keycloak_group = await self.admin.get_group(group_id)
        return self._map_keycloak_group_to_organization(keycloak_group)

    async def get_organization(self, org_id: str) -> Organization:
        """Get organization by ID."""
        keycloak_group = await self.admin.get_group(org_id)
        return self._map_keycloak_group_to_organization(keycloak_group)

    async def list_organizations(self, filters: OrganizationFilters) -> PaginatedResponse:
        """List organizations with pagination."""
        offset = (filters.page - 1) * filters.page_size

        keycloak_groups = await self.admin.list_groups(
            search=filters.search,
            first=offset,
            max_results=filters.page_size,
        )

        # Filter only top-level groups (organizations)
        orgs = [
            self._map_keycloak_group_to_organization(g)
            for g in keycloak_groups
            if not g.get("path", "").count("/") > 1  # Top level has 1 slash
        ]

        total = len(orgs) if len(orgs) < filters.page_size else offset + len(orgs) + 1

        return PaginatedResponse(
            items=orgs,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=(total + filters.page_size - 1) // filters.page_size,
        )

    async def update_organization(self, org_id: str, org_data: OrganizationUpdate) -> Organization:
        """Update organization."""
        update_payload = {}

        if org_data.name:
            update_payload["name"] = org_data.name
        if org_data.display_name or org_data.description or org_data.custom_attributes:
            attributes = {}
            if org_data.display_name:
                attributes["display_name"] = [org_data.display_name]
            if org_data.description:
                attributes["description"] = [org_data.description]
            if org_data.custom_attributes:
                attributes.update(org_data.custom_attributes)
            update_payload["attributes"] = attributes

        await self.admin.update_group(org_id, update_payload)

        keycloak_group = await self.admin.get_group(org_id)
        return self._map_keycloak_group_to_organization(keycloak_group)

    async def delete_organization(self, org_id: str) -> bool:
        """Delete organization."""
        await self.admin.delete_group(org_id)
        return True

    async def add_organization_member(self, org_id: str, user_id: str, role_ids: List[str] = None) -> bool:
        """Add user to organization."""
        await self.admin.add_user_to_group(user_id, org_id)

        if role_ids:
            await self.admin.assign_realm_roles_to_user(user_id, role_ids)

        return True

    async def remove_organization_member(self, org_id: str, user_id: str) -> bool:
        """Remove user from organization."""
        await self.admin.remove_user_from_group(user_id, org_id)
        return True

    async def list_organization_members(self, org_id: str, filters: UserFilters) -> PaginatedResponse:
        """List organization members."""
        keycloak_users = await self.admin.get_group_members(org_id)

        # Apply search filter
        if filters.search:
            search_lower = filters.search.lower()
            keycloak_users = [
                u for u in keycloak_users
                if search_lower in u.get("username", "").lower()
                or search_lower in u.get("email", "").lower()
            ]

        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        paginated_users = keycloak_users[offset:offset + filters.page_size]

        users = [self._map_keycloak_user(u) for u in paginated_users]

        return PaginatedResponse(
            items=users,
            total=len(keycloak_users),
            page=filters.page,
            page_size=filters.page_size,
            total_pages=(len(keycloak_users) + filters.page_size - 1) // filters.page_size,
        )

    # ==================== Team Management (Subgroups) ====================

    async def create_team(self, team_data: TeamCreate) -> Team:
        """Create a new team (subgroup)."""
        attributes = {
            "team_id": [team_data.name.lower().replace(" ", "-")],
            "display_name": [team_data.display_name or team_data.name],
        }

        if team_data.description:
            attributes["description"] = [team_data.description]

        if team_data.custom_attributes:
            attributes.update(team_data.custom_attributes)

        # Create as subgroup of organization or parent team
        parent_id = team_data.parent_team_id or team_data.organization_id

        team_id = await self.admin.create_group(
            name=team_data.name,
            parent_id=parent_id,
            attributes=attributes,
        )

        keycloak_group = await self.admin.get_group(team_id)
        return self._map_keycloak_group_to_team(keycloak_group)

    async def get_team(self, team_id: str) -> Team:
        """Get team by ID."""
        keycloak_group = await self.admin.get_group(team_id)
        return self._map_keycloak_group_to_team(keycloak_group)

    async def list_teams(self, filters: TeamFilters) -> PaginatedResponse:
        """List teams with pagination and filters."""
        if filters.organization_id:
            # Get subgroups of organization
            org_group = await self.admin.get_group(filters.organization_id)
            keycloak_groups = org_group.get("subGroups", [])
        else:
            # Get all groups and filter subgroups
            offset = (filters.page - 1) * filters.page_size
            keycloak_groups = await self.admin.list_groups(
                search=filters.search,
                first=offset,
                max_results=filters.page_size,
            )
            # Filter only subgroups (teams)
            keycloak_groups = [
                g for g in keycloak_groups
                if g.get("path", "").count("/") > 1  # Subgroups have 2+ slashes
            ]

        teams = [self._map_keycloak_group_to_team(g) for g in keycloak_groups]

        total = len(teams) if len(teams) < filters.page_size else (filters.page - 1) * filters.page_size + len(teams) + 1

        return PaginatedResponse(
            items=teams,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=(total + filters.page_size - 1) // filters.page_size,
        )

    async def update_team(self, team_id: str, team_data: TeamUpdate) -> Team:
        """Update team."""
        update_payload = {}

        if team_data.name:
            update_payload["name"] = team_data.name
        if team_data.display_name or team_data.description or team_data.custom_attributes:
            attributes = {}
            if team_data.display_name:
                attributes["display_name"] = [team_data.display_name]
            if team_data.description:
                attributes["description"] = [team_data.description]
            if team_data.custom_attributes:
                attributes.update(team_data.custom_attributes)
            update_payload["attributes"] = attributes

        await self.admin.update_group(team_id, update_payload)

        keycloak_group = await self.admin.get_group(team_id)
        return self._map_keycloak_group_to_team(keycloak_group)

    async def delete_team(self, team_id: str) -> bool:
        """Delete team."""
        await self.admin.delete_group(team_id)
        return True

    async def add_team_member(self, team_id: str, user_id: str, role_ids: List[str] = None) -> bool:
        """Add user to team."""
        await self.admin.add_user_to_group(user_id, team_id)

        if role_ids:
            await self.admin.assign_realm_roles_to_user(user_id, role_ids)

        return True

    async def remove_team_member(self, team_id: str, user_id: str) -> bool:
        """Remove user from team."""
        await self.admin.remove_user_from_group(user_id, team_id)
        return True

    async def list_team_members(self, team_id: str, filters: UserFilters) -> PaginatedResponse:
        """List team members."""
        keycloak_users = await self.admin.get_group_members(team_id)

        # Apply search filter
        if filters.search:
            search_lower = filters.search.lower()
            keycloak_users = [
                u for u in keycloak_users
                if search_lower in u.get("username", "").lower()
                or search_lower in u.get("email", "").lower()
            ]

        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        paginated_users = keycloak_users[offset:offset + filters.page_size]

        users = [self._map_keycloak_user(u) for u in paginated_users]

        return PaginatedResponse(
            items=users,
            total=len(keycloak_users),
            page=filters.page,
            page_size=filters.page_size,
            total_pages=(len(keycloak_users) + filters.page_size - 1) // filters.page_size,
        )

    # ==================== Role Management ====================

    async def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role."""
        await self.admin.create_realm_role(
            name=role_data.name,
            description=role_data.description,
        )

        keycloak_role = await self.admin.get_realm_role(role_data.name)
        return self._map_keycloak_role(keycloak_role, role_data.scope, role_data.scope_id)

    async def get_role(self, role_id: str) -> Role:
        """Get role by ID (name in Keycloak)."""
        keycloak_role = await self.admin.get_realm_role(role_id)
        return self._map_keycloak_role(keycloak_role)

    async def list_roles(self, filters: RoleFilters) -> PaginatedResponse:
        """List roles with pagination and filters."""
        keycloak_roles = await self.admin.list_realm_roles()

        # Apply search filter
        if filters.search:
            search_lower = filters.search.lower()
            keycloak_roles = [
                r for r in keycloak_roles
                if search_lower in r.get("name", "").lower()
                or search_lower in r.get("description", "").lower()
            ]

        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        paginated_roles = keycloak_roles[offset:offset + filters.page_size]

        roles = [self._map_keycloak_role(r, filters.scope, filters.scope_id) for r in paginated_roles]

        return PaginatedResponse(
            items=roles,
            total=len(keycloak_roles),
            page=filters.page,
            page_size=filters.page_size,
            total_pages=(len(keycloak_roles) + filters.page_size - 1) // filters.page_size,
        )

    async def update_role(self, role_id: str, role_data: RoleUpdate) -> Role:
        """Update role."""
        # Note: Keycloak roles are primarily name and description
        # More complex updates would require additional API calls
        logger.warning("Role update partially implemented for Keycloak")
        keycloak_role = await self.admin.get_realm_role(role_id)
        return self._map_keycloak_role(keycloak_role)

    async def delete_role(self, role_id: str) -> bool:
        """Delete role."""
        await self.admin.delete_realm_role(role_id)
        return True

    async def assign_role_to_user(self, user_id: str, role_id: str, scope_id: Optional[str] = None) -> bool:
        """Assign role to user."""
        await self.admin.assign_realm_roles_to_user(user_id, [role_id])
        return True

    async def remove_role_from_user(self, user_id: str, role_id: str, scope_id: Optional[str] = None) -> bool:
        """Remove role from user."""
        await self.admin.remove_realm_roles_from_user(user_id, [role_id])
        return True

    async def get_user_roles(self, user_id: str, scope: Optional[str] = None, scope_id: Optional[str] = None) -> List[Role]:
        """Get user's roles."""
        keycloak_roles = await self.admin.get_user_realm_roles(user_id)
        return [self._map_keycloak_role(r, scope, scope_id) for r in keycloak_roles]

    async def check_user_permission(self, user_id: str, permission: str, scope_id: Optional[str] = None) -> bool:
        """Check if user has a specific permission."""
        # Get user roles
        roles = await self.get_user_roles(user_id, scope_id=scope_id)

        # Check if permission is in any role (simplified check)
        # In a real implementation, you'd have a permission->role mapping
        for role in roles:
            # Simplified: check if role name matches permission pattern
            if permission in role.name or role.name == "admin":
                return True

        return False

    # ==================== Helper Methods ====================

    def _map_keycloak_user(self, keycloak_user: Dict[str, Any]) -> User:
        """Map Keycloak user to AuthFlow User model."""
        attributes = keycloak_user.get("attributes", {})

        return User(
            id=keycloak_user["id"],
            username=keycloak_user.get("username", ""),
            email=keycloak_user.get("email", ""),
            first_name=keycloak_user.get("firstName", ""),
            last_name=keycloak_user.get("lastName", ""),
            avatar_url=attributes.get("avatar_url", [None])[0] if "avatar_url" in attributes else None,
            is_active=keycloak_user.get("enabled", True),
            is_verified=keycloak_user.get("emailVerified", False),
            provider="keycloak",
            provider_id=keycloak_user["id"],
            created_at=datetime.fromtimestamp(keycloak_user.get("createdTimestamp", 0) / 1000),
            updated_at=datetime.now(),
            custom_attributes=attributes,
        )

    def _map_keycloak_group_to_organization(self, keycloak_group: Dict[str, Any]) -> Organization:
        """Map Keycloak group to Organization."""
        attributes = keycloak_group.get("attributes", {})

        return Organization(
            id=keycloak_group["id"],
            name=keycloak_group["name"],
            display_name=attributes.get("display_name", [keycloak_group["name"]])[0],
            description=attributes.get("description", [None])[0] if "description" in attributes else None,
            path=keycloak_group.get("path", ""),
            enabled=True,  # Keycloak groups don't have enabled/disabled status
            created_at=datetime.now(),
            member_count=len(keycloak_group.get("members", [])),
            custom_attributes=attributes,
        )

    def _map_keycloak_group_to_team(self, keycloak_group: Dict[str, Any]) -> Team:
        """Map Keycloak group to Team."""
        attributes = keycloak_group.get("attributes", {})
        path = keycloak_group.get("path", "")

        # Extract parent organization from path
        path_parts = path.split("/")
        org_id = attributes.get("organization_id", [None])[0]

        return Team(
            id=keycloak_group["id"],
            name=keycloak_group["name"],
            display_name=attributes.get("display_name", [keycloak_group["name"]])[0],
            description=attributes.get("description", [None])[0] if "description" in attributes else None,
            organization_id=org_id or "",
            parent_team_id=keycloak_group.get("parentId"),
            path=path,
            level=path.count("/") - 1,
            created_at=datetime.now(),
            member_count=len(keycloak_group.get("members", [])),
            custom_attributes=attributes,
        )

    def _map_keycloak_role(self, keycloak_role: Dict[str, Any], scope: Optional[str] = None, scope_id: Optional[str] = None) -> Role:
        """Map Keycloak role to Role."""
        return Role(
            id=keycloak_role.get("id", keycloak_role["name"]),
            name=keycloak_role["name"],
            display_name=keycloak_role.get("description", keycloak_role["name"]),
            description=keycloak_role.get("description"),
            scope=scope or "global",
            scope_id=scope_id,
            is_composite=keycloak_role.get("composite", False),
            created_at=datetime.now(),
        )
