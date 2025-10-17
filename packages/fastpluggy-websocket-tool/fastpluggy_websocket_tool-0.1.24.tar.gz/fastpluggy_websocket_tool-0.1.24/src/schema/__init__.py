import time
from dataclasses import dataclass, field
from enum import Enum

from starlette.websockets import WebSocket


class DisconnectReason(Enum):
    """Simple disconnect reasons for better tracking"""
    CLIENT_DISCONNECT = "client_disconnect"
    SERVER_DISCONNECT = "server_disconnect"
    HEARTBEAT_TIMEOUT = "heartbeat_timeout"
    SEND_ERROR = "send_error"
    SHUTDOWN = "shutdown"
    DUPLICATE_CLIENT = "duplicate_client"


@dataclass
class ConnectionMetadata:
    """Simple connection metadata for tracking"""
    websocket: WebSocket
    connected_at: float = field(default_factory=time.time)
    last_ping: float = field(default_factory=time.time)
    last_pong: float = field(default_factory=time.time)
    messages_sent: int = 0
    messages_failed: int = 0
    is_alive: bool = True

    @property
    def connection_duration(self) -> float:
        """Get connection duration in seconds"""
        return time.time() - self.connected_at

    @property
    def time_since_last_pong(self) -> float:
        """Get time since last pong in seconds"""
        return time.time() - self.last_pong

    @property
    def health_score(self) -> float:
        """Simple health score (0.0 to 1.0)"""
        if not self.is_alive:
            return 0.0

        # Message success rate
        total_messages = self.messages_sent + self.messages_failed
        if total_messages == 0:
            success_rate = 1.0
        else:
            success_rate = self.messages_sent / total_messages

        # Penalty for old pong (max 1 minute penalty)
        pong_penalty = min(self.time_since_last_pong / 60.0, 1.0)

        return max(0.0, success_rate - pong_penalty)
