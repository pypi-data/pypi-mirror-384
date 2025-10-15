"""Main AuthFlow class for easy integration with FastAPI."""

import logging
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware as StarlettesCORSMiddleware

from authflow.core.config import AuthFlowConfig
from authflow.core.provider import AuthProvider
from authflow.core.jwt_handler import JWTHandler
from authflow.core.permissions import PermissionEngine
from authflow.providers.keycloak import KeycloakProvider
from authflow.api.dependencies import AuthFlowDependencies
from authflow.api.auth import create_auth_router
from authflow.api.users import create_users_router
from authflow.api.organizations import create_organizations_router
from authflow.api.teams import create_teams_router
from authflow.api.roles import create_roles_router
from authflow.middleware.auth import (
    AuthenticationMiddleware,
    CORSMiddleware,
    RequestLoggingMiddleware,
)

logger = logging.getLogger(__name__)


class AuthFlow:
    """Main AuthFlow class for managing authentication and authorization.

    This class provides:
    - Easy setup and configuration
    - Provider initialization (Keycloak, etc.)
    - Router creation for all endpoints
    - Middleware configuration
    - Dependency injection setup

    Example:
        ```python
        from fastapi import FastAPI
        from authflow import AuthFlow

        app = FastAPI()
        authflow = AuthFlow.from_config_file("config.yaml")
        authflow.setup_app(app)
        ```
    """

    def __init__(
        self,
        config: AuthFlowConfig,
        provider: Optional[AuthProvider] = None,
    ):
        """Initialize AuthFlow.

        Args:
            config: AuthFlow configuration
            provider: Optional custom provider (defaults to KeycloakProvider)
        """
        self.config = config

        # Initialize provider
        if provider:
            self.provider = provider
        else:
            # Default to Keycloak provider
            self.provider = KeycloakProvider(config.provider.keycloak)

        # Initialize JWT handler
        self.jwt_handler = JWTHandler(config.authentication.tokens)

        # Initialize permission engine
        self.permission_engine = PermissionEngine(config.rbac)

        # Initialize dependencies
        self.dependencies = AuthFlowDependencies(
            provider=self.provider,
            jwt_handler=self.jwt_handler,
            permission_engine=self.permission_engine,
        )

        logger.info("AuthFlow initialized successfully")

    @classmethod
    def from_config_file(cls, config_path: str) -> "AuthFlow":
        """Create AuthFlow from configuration file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Configured AuthFlow instance
        """
        config = AuthFlowConfig.from_yaml(config_path)
        return cls(config)

    @classmethod
    def from_env(cls) -> "AuthFlow":
        """Create AuthFlow from environment variables.

        Returns:
            Configured AuthFlow instance
        """
        config = AuthFlowConfig()
        return cls(config)

    @classmethod
    def from_preset(cls, preset: str, **overrides) -> "AuthFlow":
        """Create AuthFlow from preset configuration.

        Args:
            preset: Preset name (simple_auth, multi_tenant, enterprise)
            **overrides: Configuration overrides

        Returns:
            Configured AuthFlow instance
        """
        config = AuthFlowConfig.from_preset(preset, **overrides)
        return cls(config)

    def create_routers(self) -> Dict[str, APIRouter]:
        """Create all API routers.

        Returns:
            Dictionary of routers by name
        """
        routers = {}

        # Authentication router
        routers["auth"] = create_auth_router(
            provider=self.provider,
            dependencies=self.dependencies,
        )

        # User management router
        routers["users"] = create_users_router(
            provider=self.provider,
            dependencies=self.dependencies,
        )

        # Organization router
        if self.config.features.organizations:
            routers["organizations"] = create_organizations_router(
                provider=self.provider,
                dependencies=self.dependencies,
            )

        # Team router
        if self.config.features.teams:
            routers["teams"] = create_teams_router(
                provider=self.provider,
                dependencies=self.dependencies,
            )

        # Role router (always enabled as part of RBAC)
        routers["roles"] = create_roles_router(
            provider=self.provider,
            dependencies=self.dependencies,
        )

        logger.info(f"Created {len(routers)} routers")
        return routers

    def setup_app(
        self,
        app: FastAPI,
        prefix: str = "/api/v1",
        enable_cors: bool = True,
        enable_request_logging: bool = False,
        cors_origins: Optional[List[str]] = None,
    ) -> FastAPI:
        """Setup FastAPI app with AuthFlow.

        This method:
        - Adds CORS middleware
        - Adds authentication middleware
        - Includes all routers
        - Configures dependencies

        Args:
            app: FastAPI application
            prefix: API prefix for all routes
            enable_cors: Enable CORS middleware
            enable_request_logging: Enable request logging middleware
            cors_origins: Custom CORS origins

        Returns:
            Configured FastAPI app
        """
        # Add CORS middleware
        if enable_cors:
            cors_config = CORSMiddleware.create(
                allow_origins=cors_origins,
            )
            app.add_middleware(
                StarlettesCORSMiddleware,
                **cors_config,
            )
            logger.info("CORS middleware enabled")

        # Add request logging middleware
        if enable_request_logging:
            app.add_middleware(RequestLoggingMiddleware)
            logger.info("Request logging middleware enabled")

        # Add authentication middleware
        app.add_middleware(
            AuthenticationMiddleware,
            jwt_handler=self.jwt_handler,
        )
        logger.info("Authentication middleware enabled")

        # Include routers
        routers = self.create_routers()
        for name, router in routers.items():
            app.include_router(router, prefix=prefix)
            logger.info(f"Router '{name}' included at {prefix}{router.prefix}")

        # Add health check endpoint
        @app.get("/health")
        async def health_check() -> Dict[str, Any]:
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "authflow",
                "version": "1.0.0",
            }

        logger.info(f"AuthFlow setup complete for app: {app.title}")
        return app

    def get_provider(self) -> AuthProvider:
        """Get the authentication provider.

        Returns:
            Configured authentication provider
        """
        return self.provider

    def get_dependencies(self) -> AuthFlowDependencies:
        """Get the dependencies object.

        Returns:
            Configured dependencies
        """
        return self.dependencies


def setup_auth(
    app: FastAPI,
    config_path: Optional[str] = None,
    config: Optional[AuthFlowConfig] = None,
    preset: Optional[str] = None,
    prefix: str = "/api/v1",
    enable_cors: bool = True,
    enable_request_logging: bool = False,
    cors_origins: Optional[List[str]] = None,
    **config_overrides,
) -> AuthFlow:
    """Convenience function to setup AuthFlow with FastAPI.

    This is a quick setup function that handles common use cases.

    Args:
        app: FastAPI application
        config_path: Path to configuration file
        config: AuthFlow configuration object
        preset: Preset name (simple_auth, multi_tenant, enterprise)
        prefix: API prefix
        enable_cors: Enable CORS
        enable_request_logging: Enable request logging
        cors_origins: Custom CORS origins
        **config_overrides: Configuration overrides

    Returns:
        Configured AuthFlow instance

    Examples:
        ```python
        # From config file
        authflow = setup_auth(app, config_path="config.yaml")

        # From preset
        authflow = setup_auth(app, preset="multi_tenant")

        # From environment
        authflow = setup_auth(app)

        # With overrides
        authflow = setup_auth(
            app,
            preset="simple_auth",
            keycloak_server_url="http://localhost:8090",
        )
        ```
    """
    # Create AuthFlow instance
    if config:
        authflow = AuthFlow(config)
    elif config_path:
        authflow = AuthFlow.from_config_file(config_path)
    elif preset:
        authflow = AuthFlow.from_preset(preset, **config_overrides)
    else:
        authflow = AuthFlow.from_env()

    # Setup app
    authflow.setup_app(
        app=app,
        prefix=prefix,
        enable_cors=enable_cors,
        enable_request_logging=enable_request_logging,
        cors_origins=cors_origins,
    )

    return authflow
