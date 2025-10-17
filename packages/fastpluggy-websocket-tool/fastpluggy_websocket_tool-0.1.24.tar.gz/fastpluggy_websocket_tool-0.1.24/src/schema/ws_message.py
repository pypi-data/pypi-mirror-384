from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
from datetime import datetime

from fastpluggy.core.tools.serialize_tools import serialize_value


@dataclass
class WebSocketMessage:
    type: str  # e.g. "log", "status", "message", "heartbeat"
    content: Any  # Main message content, varies by type of message
    meta: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        return asdict(self)

    def to_json(self) -> dict:
        return {
            "type": self.type,
            "content": serialize_value(self.content),
            "meta": serialize_value(self.meta),
            "timestamp": self.timestamp.isoformat(),
        }