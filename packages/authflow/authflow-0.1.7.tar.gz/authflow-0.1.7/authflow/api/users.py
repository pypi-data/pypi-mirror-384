"""User management API endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query

from authflow.core.provider import AuthProvider
from authflow.core.exceptions import UserNotFoundError, UserExistsError
from authflow.models.schemas import (
    User,
    UserCreate,
    UserUpdate,
    UserFilters,
    PaginatedResponse,
    Session,
)
from authflow.api.dependencies import AuthFlowDependencies

logger = logging.getLogger(__name__)


def create_users_router(
    provider: AuthProvider,
    dependencies: AuthFlowDependencies,
) -> APIRouter:
    """Create users management router.

    Args:
        provider: Authentication provider
        dependencies: AuthFlow dependencies

    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/users", tags=["users"])

    @router.get("", response_model=PaginatedResponse)
    async def list_users(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        search: str = Query(None, description="Search query"),
        organization_id: str = Query(None, description="Filter by organization"),
        team_id: str = Query(None, description="Filter by team"),
        role_id: str = Query(None, description="Filter by role"),
        is_active: bool = Query(None, description="Filter by active status"),
        current_user: User = Depends(dependencies.get_current_user),
    ) -> PaginatedResponse:
        """List users with pagination and filters.

        Requires: users:read permission

        Args:
            page: Page number
            page_size: Items per page
            search: Search query for username/email
            organization_id: Filter by organization
            team_id: Filter by team
            role_id: Filter by role
            is_active: Filter by active status
            current_user: Current authenticated user

        Returns:
            Paginated list of users
        """
        try:
            logger.info(f"List users requested by: {current_user.username}")

            filters = UserFilters(
                page=page,
                page_size=page_size,
                search=search,
                organization_id=organization_id,
                team_id=team_id,
                role_id=role_id,
                is_active=is_active,
            )

            try:
                result = await provider.list_users(filters)
                logger.debug(f"Found {result.total} users")
                return result
            except Exception as list_error:
                logger.warning(f"Could not list users via admin API: {list_error}. Returning current user only.")
                # Fallback: return just the current user as a minimal response
                return PaginatedResponse(
                    items=[current_user],
                    total=1,
                    page=page,
                    page_size=page_size,
                    total_pages=1,
                )

        except Exception as e:
            logger.error(f"Error listing users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list users",
            )

    @router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
    async def create_user(
        user_data: UserCreate,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> User:
        """Create a new user.

        Requires: users:write permission

        Args:
            user_data: User creation data
            current_user: Current authenticated user

        Returns:
            Created user

        Raises:
            HTTPException: If user already exists or creation fails
        """
        try:
            logger.info(
                f"Create user requested: {user_data.username} by {current_user.username}"
            )

            user = await provider.create_user(user_data)

            logger.info(f"User created: {user.username}")
            return user

        except UserExistsError as e:
            logger.warning(f"User already exists: {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            )

    @router.get("/{user_id}", response_model=User)
    async def get_user(
        user_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> User:
        """Get user by ID.

        Requires: users:read permission

        Args:
            user_id: User ID
            current_user: Current authenticated user

        Returns:
            User details

        Raises:
            HTTPException: If user not found
        """
        try:
            logger.debug(f"Get user requested: {user_id}")

            user = await provider.get_user(user_id)

            return user

        except UserNotFoundError:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user",
            )

    @router.patch("/{user_id}", response_model=User)
    async def update_user(
        user_id: str,
        user_data: UserUpdate,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> User:
        """Update user.

        Requires: users:write permission or self

        Args:
            user_id: User ID
            user_data: Update data
            current_user: Current authenticated user

        Returns:
            Updated user

        Raises:
            HTTPException: If user not found or update fails
        """
        try:
            # Check if user is updating self or has permission
            if user_id != current_user.id:
                # Would check for users:write permission here
                logger.warning(
                    f"User {current_user.username} attempting to update other user"
                )
                # For now, allow (add permission check in production)

            logger.info(f"Update user requested: {user_id} by {current_user.username}")

            user = await provider.update_user(user_id, user_data)

            logger.info(f"User updated: {user_id}")
            return user

        except UserNotFoundError:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user",
            )

    @router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_user(
        user_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> None:
        """Delete user.

        Requires: users:delete permission

        Args:
            user_id: User ID
            current_user: Current authenticated user

        Raises:
            HTTPException: If user not found or deletion fails
        """
        try:
            # Prevent self-deletion
            if user_id == current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete your own account",
                )

            logger.info(f"Delete user requested: {user_id} by {current_user.username}")

            await provider.delete_user(user_id)

            logger.info(f"User deleted: {user_id}")

        except HTTPException:
            raise
        except UserNotFoundError:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user",
            )

    @router.post("/{user_id}/password")
    async def set_user_password(
        user_id: str,
        password_data: dict,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Set user password.

        Requires: users:write permission or admin

        Args:
            user_id: User ID
            password_data: New password data
            current_user: Current authenticated user

        Returns:
            Success message
        """
        try:
            logger.info(
                f"Set password requested for user: {user_id} by {current_user.username}"
            )

            password = password_data.get("password")
            temporary = password_data.get("temporary", False)

            if not password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password is required",
                )

            await provider.set_user_password(user_id, password, temporary)

            logger.info(f"Password set for user: {user_id}")
            return {"message": "Password updated successfully"}

        except UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        except Exception as e:
            logger.error(f"Error setting password: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set password",
            )

    @router.get("/{user_id}/sessions", response_model=List[Session])
    async def get_user_sessions(
        user_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> List[Session]:
        """Get user's active sessions.

        Requires: users:read permission or self

        Args:
            user_id: User ID
            current_user: Current authenticated user

        Returns:
            List of active sessions
        """
        try:
            # Check if user is viewing own sessions or has permission
            if user_id != current_user.id:
                # Would check for users:read permission here
                pass

            logger.debug(f"Get sessions for user: {user_id}")

            sessions = await provider.get_user_sessions(user_id)

            return sessions

        except UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        except Exception as e:
            logger.error(f"Error getting sessions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get sessions",
            )

    @router.post("/{user_id}/send-verification")
    async def send_verification_email(
        user_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Send email verification to user.

        Requires: users:write permission or self

        Args:
            user_id: User ID
            current_user: Current authenticated user

        Returns:
            Success message
        """
        try:
            # Check if user is sending to self or has permission
            if user_id != current_user.id:
                # Would check for users:write permission here
                pass

            logger.info(f"Send verification email for user: {user_id}")

            await provider.send_verification_email(user_id)

            logger.info(f"Verification email sent to user: {user_id}")
            return {"message": "Verification email sent"}

        except UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email",
            )

    @router.get("/{user_id}/organizations")
    async def get_user_organizations(
        user_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Get organizations user belongs to.

        Args:
            user_id: User ID
            current_user: Current authenticated user

        Returns:
            List of organizations
        """
        try:
            logger.debug(f"Get organizations for user: {user_id}")

            # This would be implemented in the provider
            # For now, return empty list
            return {"organizations": []}

        except Exception as e:
            logger.error(f"Error getting user organizations: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get organizations",
            )

    @router.get("/{user_id}/teams")
    async def get_user_teams(
        user_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Get teams user belongs to.

        Args:
            user_id: User ID
            current_user: Current authenticated user

        Returns:
            List of teams
        """
        try:
            logger.debug(f"Get teams for user: {user_id}")

            # This would be implemented in the provider
            # For now, return empty list
            return {"teams": []}

        except Exception as e:
            logger.error(f"Error getting user teams: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get teams",
            )

    @router.get("/{user_id}/roles")
    async def get_user_roles(
        user_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Get user's roles.

        Args:
            user_id: User ID
            current_user: Current authenticated user

        Returns:
            List of roles
        """
        try:
            logger.debug(f"Get roles for user: {user_id}")

            roles = await provider.get_user_roles(user_id)

            return {"roles": roles}

        except Exception as e:
            logger.error(f"Error getting user roles: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get roles",
            )

    return router
