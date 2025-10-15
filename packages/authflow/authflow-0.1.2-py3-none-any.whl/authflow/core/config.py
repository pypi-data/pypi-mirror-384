"""Configuration system for authflow using Pydantic Settings."""

from typing import Any, Dict, List, Literal, Optional
from pathlib import Path
import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class KeycloakConfig(BaseSettings):
    """Keycloak provider configuration."""

    url: str = Field(..., description="Keycloak server URL")
    realm: str = Field(..., description="Keycloak realm name")
    client_id: str = Field(..., description="Client ID")
    client_secret: Optional[str] = Field(None, description="Client secret (if confidential)")
    admin_username: Optional[str] = Field(None, description="Admin username for management")
    admin_password: Optional[str] = Field(None, description="Admin password")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    connection_pool_size: int = Field(10, description="HTTP connection pool size")
    timeout: int = Field(30, description="Request timeout in seconds")

    model_config = SettingsConfigDict(env_prefix="KEYCLOAK_")


class ProviderConfig(BaseSettings):
    """Authentication provider configuration."""

    type: Literal["keycloak", "auth0", "custom"] = Field(
        "keycloak", description="Provider type"
    )
    keycloak: Optional[KeycloakConfig] = None

    @field_validator("keycloak")
    @classmethod
    def validate_keycloak_config(cls, v: Optional[KeycloakConfig], values: Any) -> Optional[KeycloakConfig]:
        """Validate that keycloak config is provided when type is keycloak."""
        if values.data.get("type") == "keycloak" and v is None:
            raise ValueError("keycloak configuration is required when provider type is 'keycloak'")
        return v


class FeaturesConfig(BaseSettings):
    """Feature flags configuration."""

    organizations: bool = Field(True, description="Enable organization support")
    teams: bool = Field(True, description="Enable team support")
    email_verification: bool = Field(True, description="Require email verification")
    password_reset: bool = Field(True, description="Enable password reset flow")
    social_login: bool = Field(False, description="Enable OAuth/social login")
    api_keys: bool = Field(False, description="Enable API key authentication")
    mfa: bool = Field(False, description="Enable multi-factor authentication")
    audit_logs: bool = Field(False, description="Enable audit logging")


class MultiTenantConfig(BaseSettings):
    """Multi-tenant configuration."""

    enabled: bool = Field(True, description="Enable multi-tenancy")
    mode: Literal["organization", "workspace", "company"] = Field(
        "organization", description="Tenant mode"
    )
    isolation_level: Literal["strict", "shared", "hybrid"] = Field(
        "strict", description="Data isolation level"
    )
    hierarchy_depth: int = Field(3, ge=1, le=10, description="Maximum nesting depth")


class RBACConfig(BaseSettings):
    """RBAC (Role-Based Access Control) configuration."""

    model: Literal["role-based", "attribute-based", "resource-based"] = Field(
        "role-based", description="Permission model type"
    )
    scopes: List[str] = Field(
        ["global", "organization", "team"], description="Available permission scopes"
    )
    inheritance: bool = Field(True, description="Enable role/permission inheritance")
    permission_format: str = Field(
        "resource:action", description="Permission string format"
    )
    wildcard_support: bool = Field(True, description="Support wildcard permissions")


class PasswordPolicyConfig(BaseSettings):
    """Password policy configuration."""

    min_length: int = Field(8, ge=6, le=128, description="Minimum password length")
    require_uppercase: bool = Field(True, description="Require uppercase letters")
    require_lowercase: bool = Field(True, description="Require lowercase letters")
    require_numbers: bool = Field(True, description="Require numbers")
    require_special: bool = Field(True, description="Require special characters")
    expiry_days: Optional[int] = Field(None, description="Password expiry in days")


class SessionConfig(BaseSettings):
    """Session management configuration."""

    provider: Literal["redis", "memory", "database"] = Field(
        "redis", description="Session storage provider"
    )
    redis_url: Optional[str] = Field(None, description="Redis connection URL")
    timeout: int = Field(3600, ge=60, description="Session timeout in seconds")
    refresh_enabled: bool = Field(True, description="Enable session refresh")
    concurrent_sessions: int = Field(5, ge=1, description="Max concurrent sessions per user")

    model_config = SettingsConfigDict(env_prefix="SESSION_")


class TokenConfig(BaseSettings):
    """JWT token configuration."""

    access_token_ttl: int = Field(900, ge=60, description="Access token TTL in seconds")
    refresh_token_ttl: int = Field(604800, ge=3600, description="Refresh token TTL in seconds")
    algorithm: str = Field("RS256", description="JWT signing algorithm")
    issuer: Optional[str] = Field(None, description="Token issuer")


class AuthenticationConfig(BaseSettings):
    """Authentication configuration."""

    flows: Dict[str, bool] = Field(
        default_factory=lambda: {
            "password": True,
            "oauth2": False,
            "saml": False,
            "magic_link": False,
            "api_key": False,
        },
        description="Enabled authentication flows",
    )
    password_policy: PasswordPolicyConfig = Field(
        default_factory=PasswordPolicyConfig, description="Password policy"
    )
    session: SessionConfig = Field(default_factory=SessionConfig, description="Session config")
    tokens: TokenConfig = Field(default_factory=TokenConfig, description="Token config")


class CORSConfig(BaseSettings):
    """CORS configuration."""

    enabled: bool = Field(True, description="Enable CORS")
    origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="Allowed origins",
    )
    allow_credentials: bool = Field(True, description="Allow credentials")
    allow_methods: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods",
    )
    allow_headers: List[str] = Field(
        default_factory=lambda: ["*"], description="Allowed headers"
    )


class RateLimitConfig(BaseSettings):
    """Rate limiting configuration."""

    enabled: bool = Field(True, description="Enable rate limiting")
    requests_per_minute: int = Field(60, ge=1, description="Requests per minute per IP")
    burst: int = Field(10, ge=1, description="Burst size")


class APIConfig(BaseSettings):
    """API configuration."""

    prefix: str = Field("/api/v1/auth", description="API route prefix")
    cors: CORSConfig = Field(default_factory=CORSConfig, description="CORS config")
    rate_limiting: RateLimitConfig = Field(
        default_factory=RateLimitConfig, description="Rate limiting config"
    )


class CustomFieldConfig(BaseSettings):
    """Custom field definition."""

    name: str = Field(..., description="Field name")
    type: Literal["string", "integer", "boolean", "date", "json"] = Field(
        "string", description="Field type"
    )
    required: bool = Field(False, description="Is field required")
    default: Optional[Any] = Field(None, description="Default value")


class UserModelConfig(BaseSettings):
    """User model configuration."""

    required_fields: List[str] = Field(
        default_factory=lambda: ["email", "username"], description="Required user fields"
    )
    optional_fields: List[str] = Field(
        default_factory=lambda: ["first_name", "last_name", "phone"],
        description="Optional user fields",
    )
    custom_attributes: List[CustomFieldConfig] = Field(
        default_factory=list, description="Custom user attributes"
    )


class WebhookEventConfig(BaseSettings):
    """Webhook event configuration."""

    url: str = Field(..., description="Webhook URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom headers")
    enabled: bool = Field(True, description="Enable this webhook")


class WebhooksConfig(BaseSettings):
    """Webhooks configuration."""

    enabled: bool = Field(False, description="Enable webhooks")
    events: Dict[str, Optional[str]] = Field(
        default_factory=dict, description="Event name to webhook URL mapping"
    )
    max_retries: int = Field(3, ge=0, description="Maximum retry attempts")
    timeout: int = Field(10, ge=1, description="Webhook timeout in seconds")


class AuthFlowConfig(BaseSettings):
    """Main authflow configuration."""

    provider: ProviderConfig = Field(..., description="Authentication provider config")
    features: FeaturesConfig = Field(
        default_factory=FeaturesConfig, description="Feature flags"
    )
    multi_tenant: MultiTenantConfig = Field(
        default_factory=MultiTenantConfig, description="Multi-tenant config"
    )
    rbac: RBACConfig = Field(default_factory=RBACConfig, description="RBAC config")
    authentication: AuthenticationConfig = Field(
        default_factory=AuthenticationConfig, description="Authentication config"
    )
    api: APIConfig = Field(default_factory=APIConfig, description="API config")
    user_model: UserModelConfig = Field(
        default_factory=UserModelConfig, description="User model config"
    )
    webhooks: WebhooksConfig = Field(
        default_factory=WebhooksConfig, description="Webhooks config"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AuthFlowConfig":
        """Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            AuthFlowConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)

    @classmethod
    def from_preset(
        cls, 
        preset: str, 
        **overrides: Any
    ) -> "AuthFlowConfig":
        """Load configuration from a preset.

        Args:
            preset: Preset name (simple_auth, multi_tenant, enterprise)
            **overrides: Configuration overrides to merge with preset

        Returns:
            AuthFlowConfig instance

        Raises:
            ValueError: If preset is not found
        """
        presets = {
            "simple_auth": PRESET_SIMPLE_AUTH,
            "multi_tenant": PRESET_MULTI_TENANT,
            "enterprise": PRESET_ENTERPRISE,
        }
        
        if preset not in presets:
            raise ValueError(
                f"Unknown preset: {preset}. Available presets: {list(presets.keys())}"
            )
        
        # Deep merge preset with overrides
        config_data = cls._deep_merge(presets[preset], overrides)
        return cls(**config_data)

    @classmethod
    def _deep_merge(cls, base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries.
        
        Args:
            base: Base configuration
            overrides: Override configuration
            
        Returns:
            Merged configuration
        """
        result = base.copy()
        for key, value in overrides.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = cls._deep_merge(result[key], value)
            else:
                result[key] = value
        return result


# Default configuration presets
PRESET_SIMPLE_AUTH: Dict[str, Any] = {
    "provider": {
        "type": "keycloak",
        "keycloak": {
            "url": "http://localhost:8080",
            "realm": "master",
            "client_id": "authflow",
        },
    },
    "features": {
        "organizations": False,
        "teams": False,
        "email_verification": False,
    },
    "multi_tenant": {"enabled": False},
}

PRESET_MULTI_TENANT: Dict[str, Any] = {
    "provider": {
        "type": "keycloak",
        "keycloak": {
            "url": "http://localhost:8080",
            "realm": "master",
            "client_id": "authflow",
        },
    },
    "features": {
        "organizations": True,
        "teams": True,
        "email_verification": True,
    },
    "multi_tenant": {"enabled": True, "isolation_level": "strict"},
}

PRESET_ENTERPRISE: Dict[str, Any] = {
    "provider": {
        "type": "keycloak",
        "keycloak": {
            "url": "http://localhost:8080",
            "realm": "master",
            "client_id": "authflow",
        },
    },
    "features": {
        "organizations": True,
        "teams": True,
        "email_verification": True,
        "social_login": True,
        "mfa": True,
        "audit_logs": True,
    },
    "multi_tenant": {"enabled": True, "isolation_level": "strict"},
    "authentication": {
        "flows": {
            "password": True,
            "oauth2": True,
            "saml": True,
        }
    },
}
