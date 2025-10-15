"""AuthFlow - Keycloak authentication and authorization wrapper for FastAPI.

AuthFlow provides a clean, configurable wrapper around Keycloak for managing:
- Authentication (login, logout, token refresh)
- User management
- Organizations and teams (multi-tenant)
- Roles and permissions (RBAC)

Quick Start:
    ```python
    from fastapi import FastAPI
    from authflow import setup_auth

    app = FastAPI()

    # Simple setup with preset
    authflow = setup_auth(app, preset="multi_tenant")

    # Or from config file
    authflow = setup_auth(app, config_path="config.yaml")
    ```
"""

from authflow.authflow import AuthFlow, setup_auth
from authflow.core.config import AuthFlowConfig
from authflow.core.provider import AuthProvider
from authflow.providers.keycloak import KeycloakProvider
from authflow.api.dependencies import AuthFlowDependencies

__version__ = "1.0.0"

__all__ = [
    "AuthFlow",
    "setup_auth",
    "AuthFlowConfig",
    "AuthProvider",
    "KeycloakProvider",
    "AuthFlowDependencies",
]
