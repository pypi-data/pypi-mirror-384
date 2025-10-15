"""Permission checking and authorization engine."""

from typing import List, Optional, Set
import re
import logging

from authflow.core.config import RBACConfig
from authflow.core.exceptions import PermissionDeniedError, InsufficientPermissionsError

logger = logging.getLogger(__name__)


class PermissionEngine:
    """Engine for checking permissions and authorization.

    Supports multiple permission models:
    - Role-based (RBAC)
    - Attribute-based (ABAC)
    - Resource-based
    - Wildcard permissions (e.g., users:*, *:read)
    """

    def __init__(self, config: RBACConfig):
        """Initialize permission engine.

        Args:
            config: RBAC configuration
        """
        self.config = config
        self.model = config.model
        self.wildcard_support = config.wildcard_support
        self.permission_format = config.permission_format

    def check_permission(
        self,
        user_permissions: List[str],
        required_permission: str,
        strict: bool = True,
    ) -> bool:
        """Check if user has a specific permission.

        Args:
            user_permissions: List of permissions user has
            required_permission: Permission to check
            strict: If True, permission must match exactly (unless wildcards)

        Returns:
            True if user has permission, False otherwise
        """
        if not required_permission:
            return True

        # Check for admin or superuser role (has all permissions)
        if "admin" in user_permissions or "superuser" in user_permissions:
            logger.debug("User has admin/superuser role, granting permission")
            return True

        # Direct match
        if required_permission in user_permissions:
            logger.debug(f"Direct permission match: {required_permission}")
            return True

        # Wildcard matching (if enabled)
        if self.wildcard_support:
            if self._check_wildcard_permission(user_permissions, required_permission):
                return True

        logger.debug(f"Permission denied: {required_permission}")
        return False

    def check_any_permission(
        self,
        user_permissions: List[str],
        required_permissions: List[str],
    ) -> bool:
        """Check if user has ANY of the required permissions.

        Args:
            user_permissions: List of permissions user has
            required_permissions: List of permissions to check

        Returns:
            True if user has at least one permission
        """
        for permission in required_permissions:
            if self.check_permission(user_permissions, permission):
                return True

        return False

    def check_all_permissions(
        self,
        user_permissions: List[str],
        required_permissions: List[str],
    ) -> bool:
        """Check if user has ALL of the required permissions.

        Args:
            user_permissions: List of permissions user has
            required_permissions: List of permissions to check

        Returns:
            True if user has all permissions
        """
        for permission in required_permissions:
            if not self.check_permission(user_permissions, permission):
                return False

        return True

    def require_permission(
        self,
        user_permissions: List[str],
        required_permission: str,
    ) -> None:
        """Require a specific permission, raise exception if not granted.

        Args:
            user_permissions: List of permissions user has
            required_permission: Permission to check

        Raises:
            InsufficientPermissionsError: If user lacks permission
        """
        if not self.check_permission(user_permissions, required_permission):
            raise InsufficientPermissionsError(
                f"Missing required permission: {required_permission}"
            )

    def require_any_permission(
        self,
        user_permissions: List[str],
        required_permissions: List[str],
    ) -> None:
        """Require any of the specified permissions.

        Args:
            user_permissions: List of permissions user has
            required_permissions: List of permissions to check

        Raises:
            InsufficientPermissionsError: If user lacks all permissions
        """
        if not self.check_any_permission(user_permissions, required_permissions):
            raise InsufficientPermissionsError(
                f"Missing one of required permissions: {', '.join(required_permissions)}"
            )

    def require_all_permissions(
        self,
        user_permissions: List[str],
        required_permissions: List[str],
    ) -> None:
        """Require all of the specified permissions.

        Args:
            user_permissions: List of permissions user has
            required_permissions: List of permissions to check

        Raises:
            InsufficientPermissionsError: If user lacks any permission
        """
        if not self.check_all_permissions(user_permissions, required_permissions):
            missing = [
                p for p in required_permissions
                if not self.check_permission(user_permissions, p)
            ]
            raise InsufficientPermissionsError(
                f"Missing required permissions: {', '.join(missing)}"
            )

    def check_role(
        self,
        user_roles: List[str],
        required_role: str,
    ) -> bool:
        """Check if user has a specific role.

        Args:
            user_roles: List of roles user has
            required_role: Role to check

        Returns:
            True if user has role
        """
        # Check for admin role (has all roles)
        if "admin" in user_roles or "superuser" in user_roles:
            return True

        return required_role in user_roles

    def check_any_role(
        self,
        user_roles: List[str],
        required_roles: List[str],
    ) -> bool:
        """Check if user has any of the required roles.

        Args:
            user_roles: List of roles user has
            required_roles: List of roles to check

        Returns:
            True if user has at least one role
        """
        for role in required_roles:
            if self.check_role(user_roles, role):
                return True

        return False

    def require_role(
        self,
        user_roles: List[str],
        required_role: str,
    ) -> None:
        """Require a specific role.

        Args:
            user_roles: List of roles user has
            required_role: Role to check

        Raises:
            InsufficientPermissionsError: If user lacks role
        """
        if not self.check_role(user_roles, required_role):
            raise InsufficientPermissionsError(
                f"Missing required role: {required_role}"
            )

    def parse_permission(self, permission: str) -> tuple[str, str]:
        """Parse permission string into resource and action.

        Args:
            permission: Permission string (e.g., "users:read")

        Returns:
            Tuple of (resource, action)
        """
        if ":" in permission:
            parts = permission.split(":", 1)
            return parts[0], parts[1]

        # If no separator, treat entire string as resource
        return permission, "*"

    def _check_wildcard_permission(
        self,
        user_permissions: List[str],
        required_permission: str,
    ) -> bool:
        """Check if user has permission via wildcards.

        Supports patterns like:
        - users:* (all actions on users)
        - *:read (read on all resources)
        - * (all permissions)

        Args:
            user_permissions: List of permissions user has
            required_permission: Permission to check

        Returns:
            True if wildcard match found
        """
        required_resource, required_action = self.parse_permission(required_permission)

        for user_perm in user_permissions:
            # Check for full wildcard
            if user_perm == "*":
                logger.debug(f"Wildcard match: * grants {required_permission}")
                return True

            user_resource, user_action = self.parse_permission(user_perm)

            # Check resource:* pattern (all actions on specific resource)
            if user_resource == required_resource and user_action == "*":
                logger.debug(
                    f"Wildcard match: {user_perm} grants {required_permission}"
                )
                return True

            # Check *:action pattern (specific action on all resources)
            if user_resource == "*" and user_action == required_action:
                logger.debug(
                    f"Wildcard match: {user_perm} grants {required_permission}"
                )
                return True

            # Check regex patterns if enabled
            if self._is_regex_pattern(user_perm):
                if self._regex_match(user_perm, required_permission):
                    logger.debug(
                        f"Regex match: {user_perm} grants {required_permission}"
                    )
                    return True

        return False

    def _is_regex_pattern(self, permission: str) -> bool:
        """Check if permission string contains regex special characters.

        Args:
            permission: Permission string

        Returns:
            True if contains regex patterns
        """
        regex_chars = r"[.*+?^${}()|[\]\\]"
        return bool(re.search(regex_chars, permission))

    def _regex_match(self, pattern: str, permission: str) -> bool:
        """Match permission against regex pattern.

        Args:
            pattern: Regex pattern
            permission: Permission to match

        Returns:
            True if matches
        """
        try:
            return bool(re.fullmatch(pattern, permission))
        except re.error:
            logger.warning(f"Invalid regex pattern: {pattern}")
            return False

    def get_effective_permissions(
        self,
        roles: List[str],
        role_permission_map: dict[str, List[str]],
    ) -> Set[str]:
        """Get all effective permissions from user's roles.

        Args:
            roles: List of user's roles
            role_permission_map: Mapping of role to permissions

        Returns:
            Set of all effective permissions
        """
        permissions = set()

        for role in roles:
            role_perms = role_permission_map.get(role, [])
            permissions.update(role_perms)

        return permissions

    def filter_by_permission(
        self,
        items: List[dict],
        user_permissions: List[str],
        permission_field: str = "required_permission",
    ) -> List[dict]:
        """Filter list of items based on user permissions.

        Args:
            items: List of items with permission requirements
            user_permissions: User's permissions
            permission_field: Field name containing required permission

        Returns:
            Filtered list of items user can access
        """
        filtered = []

        for item in items:
            required_perm = item.get(permission_field)

            if not required_perm:
                # No permission required, include item
                filtered.append(item)
            elif self.check_permission(user_permissions, required_perm):
                filtered.append(item)

        return filtered

    def check_scope_permission(
        self,
        user_permissions: List[str],
        required_permission: str,
        scope: str,
        scope_id: str,
    ) -> bool:
        """Check scoped permission (organization or team level).

        Args:
            user_permissions: User's permissions
            required_permission: Base permission (e.g., "users:write")
            scope: Scope type (organization, team)
            scope_id: Scope identifier

        Returns:
            True if user has scoped permission
        """
        # Build scoped permission string
        scoped_permission = f"{scope}:{scope_id}:{required_permission}"

        # Check scoped permission
        if scoped_permission in user_permissions:
            return True

        # Check if user has global permission (overrides scope)
        if self.check_permission(user_permissions, required_permission):
            return True

        # Check wildcard scoped permissions
        if self.wildcard_support:
            scope_wildcard = f"{scope}:*:{required_permission}"
            if scope_wildcard in user_permissions:
                return True

        return False
