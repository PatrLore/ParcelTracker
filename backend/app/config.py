"""Central configuration loading for the Parcel Server.

All runtime settings originate from ``config.yaml`` (see ``config.example.yaml``).
The path can be overridden with the ``PARCEL_SERVER_CONFIG`` environment variable,
which keeps secrets out of source control while still allowing zero-hardcoding.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

CONFIG_PATH_ENV_VAR = "PARCEL_SERVER_CONFIG"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


class AppSettings(BaseModel):
    name: str = "Parcel Server"
    environment: Literal["development", "production", "test"] = "development"
    debug: bool = False
    timezone: str = "Europe/Berlin"


class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(default_factory=list)


class DatabaseSettings(BaseModel):
    driver: Literal["sqlite", "postgresql", "mariadb"] = "sqlite"
    sqlite_path: str = "./data/parcel-server.db"
    host: str = "localhost"
    port: int = 5432
    name: str = "parcel_server"
    user: str = "parcel_server"
    password: str = ""

    @property
    def sqlalchemy_url(self) -> str:
        if self.driver == "sqlite":
            path = Path(self.sqlite_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{path}"
        if self.driver == "postgresql":
            return (
                f"postgresql+psycopg2://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.name}"
            )
        if self.driver == "mariadb":
            return (
                f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
            )
        raise ValueError(f"Unsupported database driver: {self.driver}")


class SecuritySettings(BaseModel):
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    password_hash_scheme: Literal["argon2", "bcrypt"] = "argon2"
    #: Fernet key encrypting mailbox passwords at rest. Generate a real one
    #: with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    mail_encryption_key: str = "wwNjK7vVV7DOZFW6aYDQF2AJea9AIUFZKHSHY5QE7Lg="


class RateLimitSettings(BaseModel):
    enabled: bool = True
    default: str = "100/minute"


class LoggingSettings(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    directory: str = "./logs"
    file_name: str = "parcel-server.log"
    max_bytes: int = 10_485_760
    backup_count: int = 5


class RedisSettings(BaseModel):
    enabled: bool = False
    host: str = "localhost"
    port: int = 6379
    db: int = 0


class TrackingProviderSettings(BaseModel):
    """Selects the Phase 3 tracking provider. "none" disables tracking sync
    entirely - the API/dashboard still work from email-derived data alone."""

    name: Literal["none", "seventeentrack", "aftership", "trackingmore", "ship24"] = "none"
    api_key: str = ""
    poll_interval_seconds: int = 900


class WebhookChannelSettings(BaseModel):
    enabled: bool = False
    url: str = ""


class DiscordChannelSettings(BaseModel):
    enabled: bool = False
    webhook_url: str = ""


class TelegramChannelSettings(BaseModel):
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""


class SignalChannelSettings(BaseModel):
    """See ``notification.channels.signal`` - ``base_url`` points at a
    self-hosted signal-cli-rest-api sidecar, not at any Signal server."""

    enabled: bool = False
    base_url: str = ""
    sender_number: str = ""
    recipient_number: str = ""


class EmailChannelSettings(BaseModel):
    enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    from_address: str = ""
    to_address: str = ""
    use_tls: bool = True


class NotificationSettings(BaseModel):
    """Each channel is independently enabled/disabled - all off by default,
    so nothing changes for anyone not using notifications."""

    webhook: WebhookChannelSettings = Field(default_factory=WebhookChannelSettings)
    discord: DiscordChannelSettings = Field(default_factory=DiscordChannelSettings)
    telegram: TelegramChannelSettings = Field(default_factory=TelegramChannelSettings)
    signal: SignalChannelSettings = Field(default_factory=SignalChannelSettings)
    email: EmailChannelSettings = Field(default_factory=EmailChannelSettings)


class MicrosoftOAuthSettings(BaseModel):
    """Enables "Sign in with Microsoft" for Outlook.com/Hotmail/Live mail
    accounts, whose plain-password IMAP login Microsoft has retired. Needs
    an Azure/Entra ID app registration - see docs/mailboxes.md."""

    enabled: bool = False
    client_id: str = ""
    #: "consumers" = personal Microsoft accounts only (Hotmail/Outlook/Live).
    #: Use "common" instead if the app registration also needs to support
    #: work/school accounts.
    tenant: str = "consumers"


class GoogleOAuthSettings(BaseModel):
    """Enables "Sign in with Google" for Gmail mailboxes, as an alternative
    to an app password (which still works for personal Gmail accounts,
    unlike Outlook.com/Hotmail). Needs a Google Cloud OAuth client of type
    "TVs and Limited Input devices" - see docs/mailboxes.md."""

    enabled: bool = False
    client_id: str = ""
    #: Unlike Microsoft's public-client device flow, Google's device flow
    #: requires a client secret even for this "limited input device" type.
    client_secret: str = ""


class MqttSettings(BaseModel):
    enabled: bool = False
    host: str = "localhost"
    port: int = 1883
    username: str = ""
    password: str = ""
    #: How often the tracking worker republishes sensor state, in seconds.
    publish_interval_seconds: int = 60


class Settings(BaseModel):
    """Root settings object assembled from ``config.yaml``."""

    app: AppSettings = Field(default_factory=AppSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    tracking_provider: TrackingProviderSettings = Field(default_factory=TrackingProviderSettings)
    notification: NotificationSettings = Field(default_factory=NotificationSettings)
    mqtt: MqttSettings = Field(default_factory=MqttSettings)
    microsoft_oauth: MicrosoftOAuthSettings = Field(default_factory=MicrosoftOAuthSettings)
    google_oauth: GoogleOAuthSettings = Field(default_factory=GoogleOAuthSettings)


def _config_path() -> Path:
    return Path(os.environ.get(CONFIG_PATH_ENV_VAR, DEFAULT_CONFIG_PATH))


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@lru_cache
def get_settings() -> Settings:
    """Load and cache the application settings.

    Cached with ``lru_cache`` so the YAML file is parsed once per process;
    call ``get_settings.cache_clear()`` in tests that need a fresh config.
    """
    raw = _load_yaml(_config_path())
    return Settings.model_validate(raw)
