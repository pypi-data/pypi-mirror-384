"""Streaming synthesis package

Contains core functionality including WebSocket client, protocol handling, session management, etc.
"""

from .client import StreamWebSocketClient
from .handlers import MessageHandler
from .protocol import MessageBuilder, WebSocketProtocol
from .session import StreamSession

__all__ = [
    "MessageBuilder",
    "MessageHandler",
    "StreamSession",
    "StreamWebSocketClient",
    "WebSocketProtocol",
]
