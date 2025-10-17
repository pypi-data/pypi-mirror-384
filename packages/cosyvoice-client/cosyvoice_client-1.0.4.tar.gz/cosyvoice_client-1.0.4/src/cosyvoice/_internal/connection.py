"""Connection Manager

Handles WebSocket connections, reconnection strategies, and error handling
"""

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum

from ..utils.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)


class ReconnectPolicy(Enum):
    """Reconnection strategy"""
    NONE = "none"
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"


@dataclass
class ConnectionConfig:
    """Connection configuration"""
    max_reconnect_attempts: int = 3
    base_reconnect_delay: float = 1.0
    max_reconnect_delay: float = 30.0
    reconnect_policy: ReconnectPolicy = ReconnectPolicy.EXPONENTIAL_BACKOFF
    connection_timeout: float = 30.0
    ping_interval: float = 20.0
    ping_timeout: float = 10.0
    close_timeout: float = 10.0


class ConnectionState(Enum):
    """Connection state"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class ConnectionManager:
    """WebSocket connection manager"""

    def __init__(
        self,
        config: ConnectionConfig,
        on_connected: Callable[[], Awaitable[None]] | None = None,
        on_disconnected: Callable[[], Awaitable[None]] | None = None,
        on_error: Callable[[Exception], Awaitable[None]] | None = None,
    ) -> None:
        self.config = config
        self.state = ConnectionState.DISCONNECTED

        # Callback functions
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
        self._on_error = on_error

        # Reconnection state
        self._reconnect_attempts = 0
        self._should_reconnect = True

    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.state == ConnectionState.CONNECTED

    @property
    def is_connecting(self) -> bool:
        """Check if connecting"""
        return self.state in (ConnectionState.CONNECTING, ConnectionState.RECONNECTING)

    def calculate_backoff_delay(self) -> float:
        """Calculate backoff delay"""
        if self.config.reconnect_policy == ReconnectPolicy.NONE:
            return 0.0
        elif self.config.reconnect_policy == ReconnectPolicy.FIXED_DELAY:
            return self.config.base_reconnect_delay
        elif self.config.reconnect_policy == ReconnectPolicy.LINEAR_BACKOFF:
            delay = self.config.base_reconnect_delay * (self._reconnect_attempts + 1)
            return min(delay, self.config.max_reconnect_delay)
        elif self.config.reconnect_policy == ReconnectPolicy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_reconnect_delay * (2 ** self._reconnect_attempts)
            # Add random jitter to avoid thundering herd
            jitter: float = random.uniform(0.1, 0.3) * delay
            total_delay = delay + jitter
            return float(min(total_delay, self.config.max_reconnect_delay))
        else:
            # Default case for unknown policies
            return float(self.config.base_reconnect_delay)  # type: ignore[unreachable]

    async def connect(self, connect_func: Callable[[], Awaitable[None]]) -> None:
        """Connect to server"""
        if self.is_connected or self.is_connecting:
            return

        self.state = ConnectionState.CONNECTING

        try:
            # Execute actual connection
            await asyncio.wait_for(connect_func(), timeout=self.config.connection_timeout)

            # Connection successful
            self.state = ConnectionState.CONNECTED
            self._reconnect_attempts = 0

            logger.info("Connection established successfully")

            if self._on_connected:
                await self._on_connected()

        except asyncio.TimeoutError:
            self.state = ConnectionState.FAILED
            error = TimeoutError(f"Connection timeout ({self.config.connection_timeout}s)")
            logger.error(f"Connection timeout: {error}")

            if self._on_error:
                await self._on_error(error)
            raise error from None

        except Exception as e:
            self.state = ConnectionState.FAILED
            connection_error = ConnectionError(f"Connection failed: {e!s}")
            logger.error(f"Connection failed: {connection_error}")

            if self._on_error:
                await self._on_error(connection_error)
            raise connection_error from e

    async def disconnect(self, disconnect_func: Callable[[], Awaitable[None]] | None = None) -> None:
        """Disconnect"""
        if self.state == ConnectionState.DISCONNECTED:
            return

        self._should_reconnect = False
        self.state = ConnectionState.DISCONNECTED

        try:
            if disconnect_func:
                await disconnect_func()
        except Exception as e:
            logger.error(f"Error occurred while disconnecting: {e}")

        logger.info("Connection disconnected")

        if self._on_disconnected:
            await self._on_disconnected()

    async def handle_connection_lost(
        self,
        reconnect_func: Callable[[], Awaitable[None]]
    ) -> None:
        """Handle connection lost"""
        if not self._should_reconnect:
            return

        if self._reconnect_attempts >= self.config.max_reconnect_attempts:
            logger.error(f"Reached maximum reconnect attempts ({self.config.max_reconnect_attempts}), stopping reconnection")
            self.state = ConnectionState.FAILED
            return

        # Calculate backoff delay
        delay = self.calculate_backoff_delay()
        self._reconnect_attempts += 1

        logger.info(f"Connection lost, reconnecting in {delay:.2f}s (attempt {self._reconnect_attempts})...")

        self.state = ConnectionState.RECONNECTING
        await asyncio.sleep(delay)

        if not self._should_reconnect:
            return  # type: ignore[unreachable]

        try:
            await self.connect(reconnect_func)
            logger.info("Reconnection successful")
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            # Recursive reconnection
            await self.handle_connection_lost(reconnect_func)

    def reset_reconnect_state(self) -> None:
        """Reset reconnection state"""
        self._reconnect_attempts = 0
        self._should_reconnect = True

    def stop_reconnect(self) -> None:
        """Stop reconnection"""
        self._should_reconnect = False
