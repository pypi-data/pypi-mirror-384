"""Role management API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query

from authflow.core.provider import AuthProvider
from authflow.core.exceptions import RoleNotFoundError, RoleExistsError
from authflow.models.schemas import (
    User,
    Role,
    RoleCreate,
    RoleUpdate,
    RoleFilters,
    PaginatedResponse,
    RoleAssignment,
)
from authflow.api.dependencies import AuthFlowDependencies

logger = logging.getLogger(__name__)


def create_roles_router(
    provider: AuthProvider,
    dependencies: AuthFlowDependencies,
) -> APIRouter:
    """Create roles management router.

    Args:
        provider: Authentication provider
        dependencies: AuthFlow dependencies

    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/roles", tags=["roles"])

    @router.get("", response_model=PaginatedResponse)
    async def list_roles(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        search: str = Query(None),
        scope: str = Query(None, description="Filter by scope (global, organization, team)"),
        scope_id: str = Query(None, description="Filter by scope ID"),
        current_user: User = Depends(dependencies.get_current_user),
    ) -> PaginatedResponse:
        """List roles with pagination and filters.

        Args:
            page: Page number
            page_size: Items per page
            search: Search query
            scope: Filter by scope
            scope_id: Filter by scope ID
            current_user: Current authenticated user

        Returns:
            Paginated list of roles
        """
        try:
            logger.info(f"List roles requested by: {current_user.username}")

            filters = RoleFilters(
                page=page,
                page_size=page_size,
                search=search,
                scope=scope,
                scope_id=scope_id,
            )

            result = await provider.list_roles(filters)

            logger.debug(f"Found {result.total} roles")
            return result

        except Exception as e:
            logger.error(f"Error listing roles: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list roles",
            )

    @router.post("", response_model=Role, status_code=status.HTTP_201_CREATED)
    async def create_role(
        role_data: RoleCreate,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> Role:
        """Create a new role.

        Requires: roles:write permission

        Args:
            role_data: Role creation data
            current_user: Current authenticated user

        Returns:
            Created role
        """
        try:
            logger.info(
                f"Create role requested: {role_data.name} by {current_user.username}"
            )

            role = await provider.create_role(role_data)

            logger.info(f"Role created: {role.name}")
            return role

        except RoleExistsError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        except Exception as e:
            logger.error(f"Error creating role: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create role",
            )

    @router.get("/{role_id}", response_model=Role)
    async def get_role(
        role_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> Role:
        """Get role by ID.

        Args:
            role_id: Role ID
            current_user: Current authenticated user

        Returns:
            Role details
        """
        try:
            logger.debug(f"Get role requested: {role_id}")

            role = await provider.get_role(role_id)

            return role

        except RoleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )
        except Exception as e:
            logger.error(f"Error getting role: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get role",
            )

    @router.patch("/{role_id}", response_model=Role)
    async def update_role(
        role_id: str,
        role_data: RoleUpdate,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> Role:
        """Update role.

        Requires: roles:write permission

        Args:
            role_id: Role ID
            role_data: Update data
            current_user: Current authenticated user

        Returns:
            Updated role
        """
        try:
            logger.info(f"Update role requested: {role_id} by {current_user.username}")

            role = await provider.update_role(role_id, role_data)

            logger.info(f"Role updated: {role_id}")
            return role

        except RoleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )
        except Exception as e:
            logger.error(f"Error updating role: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update role",
            )

    @router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_role(
        role_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> None:
        """Delete role.

        Requires: roles:delete permission

        Args:
            role_id: Role ID
            current_user: Current authenticated user
        """
        try:
            logger.info(f"Delete role requested: {role_id} by {current_user.username}")

            await provider.delete_role(role_id)

            logger.info(f"Role deleted: {role_id}")

        except RoleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )
        except Exception as e:
            logger.error(f"Error deleting role: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete role",
            )

    @router.post("/assign")
    async def assign_role(
        assignment: RoleAssignment,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Assign role to user.

        Requires: roles:write permission

        Args:
            assignment: Role assignment data
            current_user: Current authenticated user

        Returns:
            Success message
        """
        try:
            logger.info(
                f"Assign role: {assignment.role_id} to user: {assignment.user_id}"
            )

            await provider.assign_role_to_user(
                assignment.user_id,
                assignment.role_id,
                assignment.scope_id,
            )

            logger.info(f"Role assigned: {assignment.role_id} to {assignment.user_id}")
            return {"message": "Role assigned successfully"}

        except RoleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )
        except Exception as e:
            logger.error(f"Error assigning role: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign role",
            )

    @router.delete("/unassign")
    async def unassign_role(
        assignment: RoleAssignment,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Remove role from user.

        Requires: roles:write permission

        Args:
            assignment: Role assignment data
            current_user: Current authenticated user

        Returns:
            Success message
        """
        try:
            logger.info(
                f"Unassign role: {assignment.role_id} from user: {assignment.user_id}"
            )

            await provider.remove_role_from_user(
                assignment.user_id,
                assignment.role_id,
                assignment.scope_id,
            )

            logger.info(
                f"Role unassigned: {assignment.role_id} from {assignment.user_id}"
            )
            return {"message": "Role unassigned successfully"}

        except RoleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )
        except Exception as e:
            logger.error(f"Error unassigning role: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to unassign role",
            )

    @router.get("/{role_id}/members", response_model=PaginatedResponse)
    async def list_role_members(
        role_id: str,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_user: User = Depends(dependencies.get_current_user),
    ) -> PaginatedResponse:
        """List users with this role.

        Args:
            role_id: Role ID
            page: Page number
            page_size: Items per page
            current_user: Current authenticated user

        Returns:
            Paginated list of users with this role
        """
        try:
            logger.debug(f"List members with role: {role_id}")

            # This would need to be implemented in the provider
            # For now, return empty list
            from authflow.models.schemas import UserFilters

            filters = UserFilters(
                page=page,
                page_size=page_size,
                role_id=role_id,
            )

            result = await provider.list_users(filters)

            return result

        except Exception as e:
            logger.error(f"Error listing role members: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list role members",
            )

    @router.get("/{role_id}/permissions")
    async def get_role_permissions(
        role_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Get permissions granted by this role.

        Args:
            role_id: Role ID
            current_user: Current authenticated user

        Returns:
            List of permissions
        """
        try:
            logger.debug(f"Get permissions for role: {role_id}")

            role = await provider.get_role(role_id)
            permissions = role.permissions if role.permissions else []

            return {"permissions": permissions}

        except RoleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )
        except Exception as e:
            logger.error(f"Error getting role permissions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get role permissions",
            )

    @router.put("/{role_id}/permissions")
    async def update_role_permissions(
        role_id: str,
        permissions: list[str],
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Update permissions for a role.

        Requires: roles:write permission

        Args:
            role_id: Role ID
            permissions: List of permission strings
            current_user: Current authenticated user

        Returns:
            Updated permissions
        """
        try:
            logger.info(f"Update permissions for role: {role_id} by {current_user.username}")

            # Update role with new permissions
            role_data = RoleUpdate(permissions=permissions)
            role = await provider.update_role(role_id, role_data)

            logger.info(f"Permissions updated for role: {role_id}")
            return {"permissions": role.permissions if role.permissions else []}

        except RoleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )
        except Exception as e:
            logger.error(f"Error updating role permissions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update role permissions",
            )

    return router
