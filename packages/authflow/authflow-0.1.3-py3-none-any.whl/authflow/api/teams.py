"""Team management API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query

from authflow.core.provider import AuthProvider
from authflow.core.exceptions import TeamNotFoundError, TeamExistsError
from authflow.models.schemas import (
    User,
    Team,
    TeamCreate,
    TeamUpdate,
    TeamFilters,
    PaginatedResponse,
    MemberAssignment,
)
from authflow.api.dependencies import AuthFlowDependencies

logger = logging.getLogger(__name__)


def create_teams_router(
    provider: AuthProvider,
    dependencies: AuthFlowDependencies,
) -> APIRouter:
    """Create teams management router.

    Args:
        provider: Authentication provider
        dependencies: AuthFlow dependencies

    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/teams", tags=["teams"])

    @router.get("", response_model=PaginatedResponse)
    async def list_teams(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        search: str = Query(None),
        organization_id: str = Query(None),
        parent_team_id: str = Query(None),
        current_user: User = Depends(dependencies.get_current_user),
    ) -> PaginatedResponse:
        """List teams with pagination and filters.

        Args:
            page: Page number
            page_size: Items per page
            search: Search query
            organization_id: Filter by organization
            parent_team_id: Filter by parent team
            current_user: Current authenticated user

        Returns:
            Paginated list of teams
        """
        try:
            logger.info(f"List teams requested by: {current_user.username}")

            filters = TeamFilters(
                page=page,
                page_size=page_size,
                search=search,
                organization_id=organization_id,
                parent_team_id=parent_team_id,
            )

            result = await provider.list_teams(filters)

            logger.debug(f"Found {result.total} teams")
            return result

        except Exception as e:
            logger.error(f"Error listing teams: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list teams",
            )

    @router.post("", response_model=Team, status_code=status.HTTP_201_CREATED)
    async def create_team(
        team_data: TeamCreate,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> Team:
        """Create a new team.

        Args:
            team_data: Team creation data
            current_user: Current authenticated user

        Returns:
            Created team
        """
        try:
            logger.info(
                f"Create team requested: {team_data.name} by {current_user.username}"
            )

            team = await provider.create_team(team_data)

            logger.info(f"Team created: {team.name}")
            return team

        except TeamExistsError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        except Exception as e:
            logger.error(f"Error creating team: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create team",
            )

    @router.get("/{team_id}", response_model=Team)
    async def get_team(
        team_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> Team:
        """Get team by ID.

        Args:
            team_id: Team ID
            current_user: Current authenticated user

        Returns:
            Team details
        """
        try:
            logger.debug(f"Get team requested: {team_id}")

            team = await provider.get_team(team_id)

            return team

        except TeamNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )
        except Exception as e:
            logger.error(f"Error getting team: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get team",
            )

    @router.patch("/{team_id}", response_model=Team)
    async def update_team(
        team_id: str,
        team_data: TeamUpdate,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> Team:
        """Update team.

        Args:
            team_id: Team ID
            team_data: Update data
            current_user: Current authenticated user

        Returns:
            Updated team
        """
        try:
            logger.info(f"Update team requested: {team_id} by {current_user.username}")

            team = await provider.update_team(team_id, team_data)

            logger.info(f"Team updated: {team_id}")
            return team

        except TeamNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )
        except Exception as e:
            logger.error(f"Error updating team: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update team",
            )

    @router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_team(
        team_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> None:
        """Delete team.

        Args:
            team_id: Team ID
            current_user: Current authenticated user
        """
        try:
            logger.info(f"Delete team requested: {team_id} by {current_user.username}")

            await provider.delete_team(team_id)

            logger.info(f"Team deleted: {team_id}")

        except TeamNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )
        except Exception as e:
            logger.error(f"Error deleting team: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete team",
            )

    @router.get("/{team_id}/members", response_model=PaginatedResponse)
    async def list_team_members(
        team_id: str,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        search: str = Query(None),
        current_user: User = Depends(dependencies.get_current_user),
    ) -> PaginatedResponse:
        """List team members.

        Args:
            team_id: Team ID
            page: Page number
            page_size: Items per page
            search: Search query
            current_user: Current authenticated user

        Returns:
            Paginated list of members
        """
        try:
            logger.debug(f"List members for team: {team_id}")

            from authflow.models.schemas import UserFilters

            filters = UserFilters(
                page=page,
                page_size=page_size,
                search=search,
                team_id=team_id,
            )

            result = await provider.list_team_members(team_id, filters)

            return result

        except TeamNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )
        except Exception as e:
            logger.error(f"Error listing team members: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list members",
            )

    @router.post("/{team_id}/members")
    async def add_team_member(
        team_id: str,
        member_data: MemberAssignment,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Add member to team.

        Args:
            team_id: Team ID
            member_data: Member assignment data
            current_user: Current authenticated user

        Returns:
            Success message
        """
        try:
            logger.info(f"Add member to team: {team_id}, user: {member_data.user_id}")

            await provider.add_team_member(
                team_id,
                member_data.user_id,
                member_data.role_ids,
            )

            logger.info(f"Member added to team: {team_id}")
            return {"message": "Member added successfully"}

        except TeamNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )
        except Exception as e:
            logger.error(f"Error adding team member: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add member",
            )

    @router.delete("/{team_id}/members/{user_id}")
    async def remove_team_member(
        team_id: str,
        user_id: str,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> dict:
        """Remove member from team.

        Args:
            team_id: Team ID
            user_id: User ID to remove
            current_user: Current authenticated user

        Returns:
            Success message
        """
        try:
            logger.info(f"Remove member from team: {team_id}, user: {user_id}")

            await provider.remove_team_member(team_id, user_id)

            logger.info(f"Member removed from team: {team_id}")
            return {"message": "Member removed successfully"}

        except TeamNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )
        except Exception as e:
            logger.error(f"Error removing team member: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove member",
            )

    @router.post("/{team_id}/subteams", response_model=Team, status_code=status.HTTP_201_CREATED)
    async def create_subteam(
        team_id: str,
        team_data: dict,
        current_user: User = Depends(dependencies.get_current_user),
    ) -> Team:
        """Create a subteam within a team.

        Args:
            team_id: Parent team ID
            team_data: Subteam creation data
            current_user: Current authenticated user

        Returns:
            Created subteam
        """
        try:
            logger.info(f"Create subteam in team: {team_id}")

            # Add parent team ID to team data
            team_data["parent_team_id"] = team_id

            team_create = TeamCreate(**team_data)
            team = await provider.create_team(team_create)

            logger.info(f"Subteam created: {team.name}")
            return team

        except Exception as e:
            logger.error(f"Error creating subteam: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create subteam",
            )

    return router
