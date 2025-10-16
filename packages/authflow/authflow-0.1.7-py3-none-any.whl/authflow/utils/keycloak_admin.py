"""Keycloak Admin API wrapper utility.

This module provides a comprehensive wrapper around the Keycloak Admin API
for managing users, groups (organizations/teams), roles, and permissions.
"""

from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

from keycloak import KeycloakAdmin, KeycloakOpenIDConnection
from keycloak.exceptions import KeycloakError, KeycloakGetError, KeycloakPostError

from authflow.core.config import KeycloakConfig
from authflow.core.exceptions import (
    ProviderConnectionError,
    ProviderAPIError,
    UserNotFoundError,
    UserExistsError,
    OrganizationNotFoundError,
    TeamNotFoundError,
    RoleNotFoundError,
)

logger = logging.getLogger(__name__)


class KeycloakAdminClient:
    """Wrapper for Keycloak Admin API operations.

    This class provides a clean interface to Keycloak's Admin API,
    handling connection management, error handling, and data transformation.
    """

    def __init__(self, config: KeycloakConfig):
        """Initialize Keycloak Admin client.

        Args:
            config: Keycloak configuration
        """
        self.config = config
        self._admin: Optional[KeycloakAdmin] = None

    def _get_admin(self) -> KeycloakAdmin:
        """Get or create admin client with connection retry.

        Returns:
            KeycloakAdmin instance

        Raises:
            ProviderConnectionError: If connection fails
        """
        if self._admin is None:
            try:
                # Create admin client using admin user in the target realm
                # This allows managing users within the same realm
                self._admin = KeycloakAdmin(
                    server_url=self.config.url,
                    username=self.config.admin_username,
                    password=self.config.admin_password,
                    realm_name=self.config.realm,  # Auth and manage in the same realm
                    client_id="admin-cli",  # Use admin-cli for admin operations
                    verify=self.config.verify_ssl,
                    timeout=self.config.timeout,
                )

                logger.info(f"Connected to Keycloak at {self.config.url}, realm: {self.config.realm}")

            except Exception as e:
                logger.error(f"Failed to connect to Keycloak: {e}")
                raise ProviderConnectionError(
                    f"Failed to connect to Keycloak: {str(e)}"
                )

        return self._admin

    def _handle_error(self, error: Exception, operation: str) -> None:
        """Handle Keycloak API errors.

        Args:
            error: Exception that occurred
            operation: Description of the operation

        Raises:
            Appropriate AuthFlow exception
        """
        logger.error(f"Keycloak error during {operation}: {error}")

        if isinstance(error, KeycloakGetError):
            status_code = error.response_code
            if status_code == 404:
                raise UserNotFoundError(f"Resource not found: {operation}")
            raise ProviderAPIError(
                f"Keycloak GET error: {operation}",
                status_code=status_code
            )

        if isinstance(error, KeycloakPostError):
            status_code = error.response_code
            if status_code == 409:
                raise UserExistsError(f"Resource already exists: {operation}")
            raise ProviderAPIError(
                f"Keycloak POST error: {operation}",
                status_code=status_code
            )

        if isinstance(error, KeycloakError):
            raise ProviderAPIError(f"Keycloak error: {operation} - {str(error)}")

        raise ProviderAPIError(f"Unexpected error: {operation} - {str(error)}")

    # ==================== User Management ====================

    async def create_user(
        self,
        username: str,
        email: str,
        password: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        enabled: bool = True,
        email_verified: bool = False,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new user in Keycloak.

        Args:
            username: Username
            email: Email address
            password: Password (optional, can be set later)
            first_name: First name
            last_name: Last name
            enabled: Whether user is enabled
            email_verified: Whether email is verified
            attributes: Custom attributes

        Returns:
            User ID

        Raises:
            UserExistsError: If user already exists
            ProviderAPIError: If creation fails
        """
        try:
            admin = self._get_admin()

            user_data = {
                "username": username,
                "email": email,
                "enabled": enabled,
                "emailVerified": email_verified,
            }

            if first_name:
                user_data["firstName"] = first_name
            if last_name:
                user_data["lastName"] = last_name
            if attributes:
                user_data["attributes"] = attributes

            # Create user
            user_id = admin.create_user(user_data)
            logger.info(f"Created user: {username} (ID: {user_id})")

            # Set password if provided
            if password:
                admin.set_user_password(user_id, password, temporary=False)

            return user_id

        except Exception as e:
            self._handle_error(e, f"create_user({username})")

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User data

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            admin = self._get_admin()
            user = admin.get_user(user_id)
            return user
        except Exception as e:
            self._handle_error(e, f"get_user({user_id})")

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username.

        Args:
            username: Username

        Returns:
            User data or None if not found
        """
        try:
            admin = self._get_admin()
            users = admin.get_users({"username": username, "exact": True})
            return users[0] if users else None
        except Exception as e:
            self._handle_error(e, f"get_user_by_username({username})")

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email.

        Args:
            email: Email address

        Returns:
            User data or None if not found
        """
        try:
            admin = self._get_admin()
            users = admin.get_users({"email": email, "exact": True})
            return users[0] if users else None
        except Exception as e:
            self._handle_error(e, f"get_user_by_email({email})")

    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> None:
        """Update user.

        Args:
            user_id: User ID
            user_data: Update data

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            admin = self._get_admin()
            admin.update_user(user_id, user_data)
            logger.info(f"Updated user: {user_id}")
        except Exception as e:
            self._handle_error(e, f"update_user({user_id})")

    async def delete_user(self, user_id: str) -> None:
        """Delete user.

        Args:
            user_id: User ID

        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            admin = self._get_admin()
            admin.delete_user(user_id)
            logger.info(f"Deleted user: {user_id}")
        except Exception as e:
            self._handle_error(e, f"delete_user({user_id})")

    async def list_users(
        self,
        search: Optional[str] = None,
        first: int = 0,
        max_results: int = 100,
        **filters: Any,
    ) -> List[Dict[str, Any]]:
        """List users with pagination and filters.

        Args:
            search: Search query
            first: Offset
            max_results: Maximum results
            **filters: Additional filters

        Returns:
            List of users
        """
        try:
            admin = self._get_admin()
            query = {"first": first, "max": max_results}

            if search:
                query["search"] = search

            query.update(filters)

            users = admin.get_users(query)
            return users
        except Exception as e:
            self._handle_error(e, "list_users")

    async def set_user_password(
        self, user_id: str, password: str, temporary: bool = False
    ) -> None:
        """Set user password.

        Args:
            user_id: User ID
            password: New password
            temporary: Whether password is temporary
        """
        try:
            admin = self._get_admin()
            admin.set_user_password(user_id, password, temporary)
            logger.info(f"Set password for user: {user_id}")
        except Exception as e:
            self._handle_error(e, f"set_user_password({user_id})")

    async def send_verify_email(self, user_id: str) -> None:
        """Send verification email to user.

        Args:
            user_id: User ID
        """
        try:
            admin = self._get_admin()
            admin.send_verify_email(user_id)
            logger.info(f"Sent verification email to user: {user_id}")
        except Exception as e:
            self._handle_error(e, f"send_verify_email({user_id})")

    async def send_password_reset_email(self, user_id: str) -> None:
        """Send password reset email to user.

        Args:
            user_id: User ID
        """
        try:
            admin = self._get_admin()
            # Execute actions - "UPDATE_PASSWORD" action sends reset email
            admin.send_update_account(
                user_id=user_id,
                payload=["UPDATE_PASSWORD"]
            )
            logger.info(f"Sent password reset email to user: {user_id}")
        except Exception as e:
            self._handle_error(e, f"send_password_reset_email({user_id})")

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's active sessions.

        Args:
            user_id: User ID

        Returns:
            List of sessions
        """
        try:
            admin = self._get_admin()
            sessions = admin.get_sessions(user_id)
            return sessions
        except Exception as e:
            self._handle_error(e, f"get_user_sessions({user_id})")

    # ==================== Group Management (Organizations/Teams) ====================

    async def create_group(
        self,
        name: str,
        parent_id: Optional[str] = None,
        attributes: Optional[Dict[str, List[str]]] = None,
    ) -> str:
        """Create a group (organization or team).

        Args:
            name: Group name
            parent_id: Parent group ID (for teams)
            attributes: Group attributes

        Returns:
            Group ID
        """
        try:
            admin = self._get_admin()

            group_data = {"name": name}
            if attributes:
                group_data["attributes"] = attributes

            if parent_id:
                # Create as subgroup
                group_id = admin.create_group(group_data, parent=parent_id)
            else:
                # Create as top-level group
                group_id = admin.create_group(group_data)

            logger.info(f"Created group: {name} (ID: {group_id})")
            return group_id

        except Exception as e:
            self._handle_error(e, f"create_group({name})")

    async def get_group(self, group_id: str) -> Dict[str, Any]:
        """Get group by ID.

        Args:
            group_id: Group ID

        Returns:
            Group data
        """
        try:
            admin = self._get_admin()
            group = admin.get_group(group_id)
            return group
        except Exception as e:
            self._handle_error(e, f"get_group({group_id})")

    async def get_group_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get group by path.

        Args:
            path: Group path (e.g., "/Organizations/Demo Org")

        Returns:
            Group data or None
        """
        try:
            admin = self._get_admin()
            group = admin.get_group_by_path(path)
            return group
        except Exception as e:
            if isinstance(e, KeycloakGetError) and e.response_code == 404:
                return None
            self._handle_error(e, f"get_group_by_path({path})")

    async def update_group(self, group_id: str, group_data: Dict[str, Any]) -> None:
        """Update group.

        Args:
            group_id: Group ID
            group_data: Update data
        """
        try:
            admin = self._get_admin()
            admin.update_group(group_id, group_data)
            logger.info(f"Updated group: {group_id}")
        except Exception as e:
            self._handle_error(e, f"update_group({group_id})")

    async def delete_group(self, group_id: str) -> None:
        """Delete group.

        Args:
            group_id: Group ID
        """
        try:
            admin = self._get_admin()
            admin.delete_group(group_id)
            logger.info(f"Deleted group: {group_id}")
        except Exception as e:
            self._handle_error(e, f"delete_group({group_id})")

    async def list_groups(
        self, search: Optional[str] = None, first: int = 0, max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """List groups.

        Args:
            search: Search query
            first: Offset
            max_results: Maximum results

        Returns:
            List of groups
        """
        try:
            admin = self._get_admin()
            query = {"first": first, "max": max_results}
            if search:
                query["search"] = search

            groups = admin.get_groups(query)
            return groups
        except Exception as e:
            self._handle_error(e, "list_groups")

    async def get_group_members(self, group_id: str) -> List[Dict[str, Any]]:
        """Get members of a group.

        Args:
            group_id: Group ID

        Returns:
            List of users
        """
        try:
            admin = self._get_admin()
            members = admin.get_group_members(group_id)
            return members
        except Exception as e:
            self._handle_error(e, f"get_group_members({group_id})")

    async def add_user_to_group(self, user_id: str, group_id: str) -> None:
        """Add user to group.

        Args:
            user_id: User ID
            group_id: Group ID
        """
        try:
            admin = self._get_admin()
            admin.group_user_add(user_id, group_id)
            logger.info(f"Added user {user_id} to group {group_id}")
        except Exception as e:
            self._handle_error(e, f"add_user_to_group({user_id}, {group_id})")

    async def remove_user_from_group(self, user_id: str, group_id: str) -> None:
        """Remove user from group.

        Args:
            user_id: User ID
            group_id: Group ID
        """
        try:
            admin = self._get_admin()
            admin.group_user_remove(user_id, group_id)
            logger.info(f"Removed user {user_id} from group {group_id}")
        except Exception as e:
            self._handle_error(e, f"remove_user_from_group({user_id}, {group_id})")

    async def get_user_groups(self, user_id: str) -> List[Dict[str, Any]]:
        """Get groups user belongs to.

        Args:
            user_id: User ID

        Returns:
            List of groups
        """
        try:
            admin = self._get_admin()
            groups = admin.get_user_groups(user_id)
            return groups
        except Exception as e:
            self._handle_error(e, f"get_user_groups({user_id})")

    # ==================== Role Management ====================

    async def create_realm_role(
        self, name: str, description: Optional[str] = None
    ) -> None:
        """Create a realm role.

        Args:
            name: Role name
            description: Role description
        """
        try:
            admin = self._get_admin()
            role_data = {"name": name}
            if description:
                role_data["description"] = description

            admin.create_realm_role(role_data)
            logger.info(f"Created realm role: {name}")
        except Exception as e:
            self._handle_error(e, f"create_realm_role({name})")

    async def get_realm_role(self, role_name: str) -> Dict[str, Any]:
        """Get realm role by name.

        Args:
            role_name: Role name

        Returns:
            Role data
        """
        try:
            admin = self._get_admin()
            role = admin.get_realm_role(role_name)
            return role
        except Exception as e:
            self._handle_error(e, f"get_realm_role({role_name})")

    async def list_realm_roles(self) -> List[Dict[str, Any]]:
        """List all realm roles.

        Returns:
            List of roles
        """
        try:
            admin = self._get_admin()
            roles = admin.get_realm_roles()
            return roles
        except Exception as e:
            self._handle_error(e, "list_realm_roles")

    async def delete_realm_role(self, role_name: str) -> None:
        """Delete realm role.

        Args:
            role_name: Role name
        """
        try:
            admin = self._get_admin()
            admin.delete_realm_role(role_name)
            logger.info(f"Deleted realm role: {role_name}")
        except Exception as e:
            self._handle_error(e, f"delete_realm_role({role_name})")

    async def assign_realm_roles_to_user(
        self, user_id: str, role_names: List[str]
    ) -> None:
        """Assign realm roles to user.

        Args:
            user_id: User ID
            role_names: List of role names
        """
        try:
            admin = self._get_admin()

            # Get role representations
            roles = [admin.get_realm_role(name) for name in role_names]

            # Assign roles
            admin.assign_realm_roles(user_id, roles)
            logger.info(f"Assigned roles {role_names} to user {user_id}")
        except Exception as e:
            self._handle_error(e, f"assign_realm_roles_to_user({user_id})")

    async def get_user_realm_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's realm roles.

        Args:
            user_id: User ID

        Returns:
            List of roles
        """
        try:
            admin = self._get_admin()
            roles = admin.get_realm_roles_of_user(user_id)
            return roles
        except Exception as e:
            self._handle_error(e, f"get_user_realm_roles({user_id})")

    async def remove_realm_roles_from_user(
        self, user_id: str, role_names: List[str]
    ) -> None:
        """Remove realm roles from user.

        Args:
            user_id: User ID
            role_names: List of role names
        """
        try:
            admin = self._get_admin()

            # Get role representations
            roles = [admin.get_realm_role(name) for name in role_names]

            # Remove roles
            admin.delete_realm_roles_of_user(user_id, roles)
            logger.info(f"Removed roles {role_names} from user {user_id}")
        except Exception as e:
            self._handle_error(e, f"remove_realm_roles_from_user({user_id})")

    async def assign_group_realm_roles(
        self, group_id: str, role_names: List[str]
    ) -> None:
        """Assign realm roles to group.

        Args:
            group_id: Group ID
            role_names: List of role names
        """
        try:
            admin = self._get_admin()

            # Get role representations
            roles = [admin.get_realm_role(name) for name in role_names]

            # Assign roles to group
            admin.assign_group_realm_roles(group_id, roles)
            logger.info(f"Assigned roles {role_names} to group {group_id}")
        except Exception as e:
            self._handle_error(e, f"assign_group_realm_roles({group_id})")

    async def get_group_realm_roles(self, group_id: str) -> List[Dict[str, Any]]:
        """Get group's realm roles.

        Args:
            group_id: Group ID

        Returns:
            List of roles
        """
        try:
            admin = self._get_admin()
            roles = admin.get_group_realm_roles(group_id)
            return roles
        except Exception as e:
            self._handle_error(e, f"get_group_realm_roles({group_id})")
