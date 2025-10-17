"""Configuration management module

Provides unified configuration loading, validation, and environment variable support.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from ..utils.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class ClientConfig:
    """Client configuration"""
    # Server configuration
    base_url: str = "http://localhost:8080"
    api_key: str | None = None

    # Connection configuration
    connection_timeout: float = 30.0
    read_timeout: float = 60.0
    max_reconnect_attempts: int = 3
    base_reconnect_delay: float = 1.0
    max_reconnect_delay: float = 30.0

    # WebSocket configuration
    ping_interval: float = 20.0
    ping_timeout: float = 10.0
    close_timeout: float = 10.0

    def __post_init__(self) -> None:
        """Configuration validation"""
        self.validate()

    def validate(self) -> None:
        """Validate configuration parameters"""
        # Validate URL format
        try:
            parsed = urlparse(self.base_url)
            if not parsed.scheme or not parsed.netloc:
                raise ConfigurationError(f"Invalid base_url: {self.base_url}")
        except Exception as e:
            raise ConfigurationError(f"Failed to parse base_url: {e}") from e

        # Validate timeout configuration
        if self.connection_timeout <= 0:
            raise ConfigurationError("connection_timeout must be greater than 0")
        if self.read_timeout <= 0:
            raise ConfigurationError("read_timeout must be greater than 0")

        # Validate reconnection configuration
        if self.max_reconnect_attempts < 0:
            raise ConfigurationError("max_reconnect_attempts cannot be negative")
        if self.base_reconnect_delay <= 0:
            raise ConfigurationError("base_reconnect_delay must be greater than 0")
        if self.max_reconnect_delay < self.base_reconnect_delay:
            raise ConfigurationError("max_reconnect_delay cannot be less than base_reconnect_delay")

        # Validate WebSocket configuration
        if self.ping_interval <= 0:
            raise ConfigurationError("ping_interval must be greater than 0")
        if self.ping_timeout <= 0:
            raise ConfigurationError("ping_timeout must be greater than 0")
        if self.ping_timeout >= self.ping_interval:
            logger.warning("ping_timeout should be less than ping_interval")

    @property
    def websocket_url(self) -> str:
        """Get WebSocket URL"""
        return self.base_url.replace("http://", "ws://").replace("https://", "wss://")

    @property
    def http_headers(self) -> dict[str, str]:
        """Get HTTP request headers"""
        headers = {
            "User-Agent": "CosyVoice-Python-SDK/1.0.0",
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def get_websocket_url_with_auth(self) -> str:
        """Get WebSocket URL with authentication"""
        ws_url = self.websocket_url

        if self.api_key:
            separator = "&" if "?" in ws_url else "?"
            ws_url = f"{ws_url}{separator}token={self.api_key}"

        return ws_url


def load_config_from_env(prefix: str = "COSYVOICE_") -> ClientConfig:
    """Load configuration from environment variables

    Note: .env file loading should be handled by the application layer,
    not by the SDK core. Use python-dotenv in your application if needed.
    """
    config_kwargs: dict[str, Any] = {}

    # Map environment variables to configuration fields
    env_mapping: dict[str, str | tuple[str, type[float] | type[int] | type[bool]]] = {
        f"{prefix}BASE_URL": "base_url",
        f"{prefix}API_KEY": "api_key",
        f"{prefix}CONNECTION_TIMEOUT": ("connection_timeout", float),
        f"{prefix}READ_TIMEOUT": ("read_timeout", float),
        f"{prefix}MAX_RECONNECT_ATTEMPTS": ("max_reconnect_attempts", int),
        f"{prefix}BASE_RECONNECT_DELAY": ("base_reconnect_delay", float),
        f"{prefix}MAX_RECONNECT_DELAY": ("max_reconnect_delay", float),
        f"{prefix}PING_INTERVAL": ("ping_interval", float),
        f"{prefix}PING_TIMEOUT": ("ping_timeout", float),
        f"{prefix}CLOSE_TIMEOUT": ("close_timeout", float),
    }

    for env_key, config_field in env_mapping.items():
        env_value = os.getenv(env_key)
        if env_value is not None:
            if isinstance(config_field, tuple):
                field_name, field_type = config_field
                try:
                    if field_type is bool:
                        # Boolean value handling
                        config_kwargs[field_name] = env_value.lower() in ("true", "1", "yes", "on")
                    else:
                        config_kwargs[field_name] = field_type(env_value)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to convert environment variable {env_key}: {e}")
            else:
                # config_field is str
                config_kwargs[config_field] = env_value

    logger.debug(f"Loaded configuration from environment variables: {list(config_kwargs.keys())}")

    try:
        return ClientConfig(**config_kwargs)
    except Exception as e:
        raise ConfigurationError(f"Failed to create configuration: {e}") from e


def load_config_from_dict(config_dict: dict[str, Any]) -> ClientConfig:
    """Load configuration from dictionary"""
    try:
        return ClientConfig(**config_dict)
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration from dictionary: {e}") from e


def merge_configs(base: ClientConfig, override: dict[str, Any]) -> ClientConfig:
    """Merge configurations"""
    # Convert to dictionary
    base_dict = base.__dict__.copy()
    base_dict.update(override)

    return load_config_from_dict(base_dict)


# Default configuration instance
DEFAULT_CONFIG = ClientConfig()


def get_default_config() -> ClientConfig:
    """Get a copy of the default configuration"""
    return ClientConfig(
        base_url=DEFAULT_CONFIG.base_url,
        api_key=DEFAULT_CONFIG.api_key,
        connection_timeout=DEFAULT_CONFIG.connection_timeout,
        read_timeout=DEFAULT_CONFIG.read_timeout,
        max_reconnect_attempts=DEFAULT_CONFIG.max_reconnect_attempts,
        base_reconnect_delay=DEFAULT_CONFIG.base_reconnect_delay,
        max_reconnect_delay=DEFAULT_CONFIG.max_reconnect_delay,
        ping_interval=DEFAULT_CONFIG.ping_interval,
        ping_timeout=DEFAULT_CONFIG.ping_timeout,
        close_timeout=DEFAULT_CONFIG.close_timeout,
    )
