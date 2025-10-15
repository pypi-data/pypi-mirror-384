"""Organization management API endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query

from authflow.core.provider import AuthProvider
from authflow.core.exceptions import OrganizationNotFoundError, OrganizationExistsError
from authflow.models.schemas import (
    User,
    Organization,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationFilters,
    PaginatedResponse,
    MemberAssignment,
)
from authflow.api.dependencies import AuthFlowDependencies

logger = logging.getLogger(__name__)


def create_organizations_router(
    provider: AuthProvider,
    dependencies: AuthFlowDependencies,
) -> APIRouter:
    """Create organizations management router.

    Args:
        provider: Authentication provider
        dependencies: AuthFlow dependencies

    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/organizations", tags=["organizations"])

    @router.get("", response_model=PaginatedResponse)
    async def list_organizations(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        search: str = Query(None),
        current_user: User = Depends(dependencies.get_current_user),
    ) -> PaginatedResponse:
        """List organizations with pagination.

        Requires: organizations:read permission

        Args:
            page: Page number
            page_size: Items per page
            search: Search query
            current_user: Current authenticated user

        Returns:
            Paginated list of organizations
        """
        try:
            logger.info(f"List organizations requested by: {current_user.username}")

            filters = OrganizationFilters(
                page=page,
                page_size=page_size,
                search=search,
            )

            result = await provider.list_organizations(filters)

            logger.debug(f"Found {result.total} organizations")
            return result

        except Exception as e:
            logger.error(f"Error listing organizations: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list organizations",
            )

    @router.post("", response_model=Organization, status_code=status.HTTP_201_CREATED)
    async def create_organization(
        org_data: OrganizationCreate,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> Organization:
        """Create a new organization.

        Requires: organizations:write permission

        Args:
            org_data: Organization creation data
            current_user: Current authenticated user

        Returns:
            Created organization
        """
        try:
            logger.info(
                f"Create organization requested: {org_data.name} by {current_user.username}"
            )

            organization = await provider.create_organization(org_data)

            logger.info(f"Organization created: {organization.name}")
            return organization

        except OrganizationExistsError as e:
            logger.warning(f"Organization already exists: {org_data.name}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create organization",
            )

    @router.get("/{org_id}", response_model=Organization)
    async def get_organization(
        org_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> Organization:
        """Get organization by ID.

        Requires: organizations:read permission

        Args:
            org_id: Organization ID
            current_user: Current authenticated user

        Returns:
            Organization details
        """
        try:
            logger.debug(f"Get organization requested: {org_id}")

            organization = await provider.get_organization(org_id)

            return organization

        except OrganizationNotFoundError:
            logger.warning(f"Organization not found: {org_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        except Exception as e:
            logger.error(f"Error getting organization: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get organization",
            )

    @router.patch("/{org_id}", response_model=Organization)
    async def update_organization(
        org_id: str,
        org_data: OrganizationUpdate,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> Organization:
        """Update organization.

        Requires: organizations:write permission

        Args:
            org_id: Organization ID
            org_data: Update data
            current_user: Current authenticated user

        Returns:
            Updated organization
        """
        try:
            logger.info(
                f"Update organization requested: {org_id} by {current_user.username}"
            )

            organization = await provider.update_organization(org_id, org_data)

            logger.info(f"Organization updated: {org_id}")
            return organization

        except OrganizationNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        except Exception as e:
            logger.error(f"Error updating organization: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update organization",
            )

    @router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_organization(
        org_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> None:
        """Delete organization.

        Requires: organizations:delete permission

        Args:
            org_id: Organization ID
            current_user: Current authenticated user
        """
        try:
            logger.info(
                f"Delete organization requested: {org_id} by {current_user.username}"
            )

            await provider.delete_organization(org_id)

            logger.info(f"Organization deleted: {org_id}")

        except OrganizationNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        except Exception as e:
            logger.error(f"Error deleting organization: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete organization",
            )

    @router.get("/{org_id}/members", response_model=PaginatedResponse)
    async def list_organization_members(
        org_id: str,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        search: str = Query(None),
        current_user: User = Depends(dependencies.get_current_user),
    ) -> PaginatedResponse:
        """List organization members.

        Args:
            org_id: Organization ID
            page: Page number
            page_size: Items per page
            search: Search query
            current_user: Current authenticated user

        Returns:
            Paginated list of members
        """
        try:
            logger.debug(f"List members for organization: {org_id}")

            from authflow.models.schemas import UserFilters

            filters = UserFilters(
                page=page,
                page_size=page_size,
                search=search,
                organization_id=org_id,
            )

            result = await provider.list_organization_members(org_id, filters)

            return result

        except OrganizationNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        except Exception as e:
            logger.error(f"Error listing organization members: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list members",
            )

    @router.post("/{org_id}/members")
    async def add_organization_member(
        org_id: str,
        member_data: MemberAssignment,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Add member to organization.

        Requires: organizations:write permission

        Args:
            org_id: Organization ID
            member_data: Member assignment data
            current_user: Current authenticated user

        Returns:
            Success message
        """
        try:
            logger.info(
                f"Add member to organization: {org_id}, user: {member_data.user_id}"
            )

            await provider.add_organization_member(
                org_id,
                member_data.user_id,
                member_data.role_ids,
            )

            logger.info(f"Member added to organization: {org_id}")
            return {"message": "Member added successfully"}

        except OrganizationNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        except Exception as e:
            logger.error(f"Error adding organization member: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add member",
            )

    @router.delete("/{org_id}/members/{user_id}")
    async def remove_organization_member(
        org_id: str,
        user_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Remove member from organization.

        Requires: organizations:write permission

        Args:
            org_id: Organization ID
            user_id: User ID to remove
            current_user: Current authenticated user

        Returns:
            Success message
        """
        try:
            logger.info(f"Remove member from organization: {org_id}, user: {user_id}")

            await provider.remove_organization_member(org_id, user_id)

            logger.info(f"Member removed from organization: {org_id}")
            return {"message": "Member removed successfully"}

        except OrganizationNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        except Exception as e:
            logger.error(f"Error removing organization member: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove member",
            )

    @router.get("/{org_id}/teams")
    async def list_organization_teams(
        org_id: str,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_user: User = Depends(dependencies.get_current_user),
    ) -> PaginatedResponse:
        """List teams in organization.

        Args:
            org_id: Organization ID
            page: Page number
            page_size: Items per page
            current_user: Current authenticated user

        Returns:
            Paginated list of teams
        """
        try:
            logger.debug(f"List teams for organization: {org_id}")

            from authflow.models.schemas import TeamFilters

            filters = TeamFilters(
                page=page,
                page_size=page_size,
                organization_id=org_id,
            )

            result = await provider.list_teams(filters)

            return result

        except Exception as e:
            logger.error(f"Error listing organization teams: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list teams",
            )

    @router.get("/{org_id}/settings")
    async def get_organization_settings(
        org_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Get organization settings.

        Args:
            org_id: Organization ID
            current_user: Current authenticated user

        Returns:
            Organization settings
        """
        try:
            logger.debug(f"Get settings for organization: {org_id}")

            # Get organization and return custom attributes as settings
            org = await provider.get_organization(org_id)

            return {"settings": org.custom_attributes}

        except OrganizationNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        except Exception as e:
            logger.error(f"Error getting organization settings: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get settings",
            )

    @router.patch("/{org_id}/settings")
    async def update_organization_settings(
        org_id: str,
        settings: dict,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Update organization settings.

        Args:
            org_id: Organization ID
            settings: Settings to update
            current_user: Current authenticated user

        Returns:
            Updated settings
        """
        try:
            logger.info(f"Update settings for organization: {org_id}")

            # Update custom attributes
            org_update = OrganizationUpdate(custom_attributes=settings)
            org = await provider.update_organization(org_id, org_update)

            logger.info(f"Settings updated for organization: {org_id}")
            return {"settings": org.custom_attributes}

        except OrganizationNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        except Exception as e:
            logger.error(f"Error updating organization settings: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update settings",
            )

    return router
