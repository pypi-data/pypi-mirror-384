# async_registry.py

import asyncio
from typing import Dict, Any, Set

# -----------------------------------------------------------------------------
# 1) Registry mapping widget_id → configuration dict.
#    Each config dict should include at least:
#      - "instance": the AsyncWidget instance
#      - "subwidgets": list of its child widgets (if needed)
# -----------------------------------------------------------------------------
_WIDGET_REGISTRY: Dict[str, Dict[str, Any]] = {}

# -----------------------------------------------------------------------------
# 2) Global asyncio.Queue holding pending widget_ids for background processing.
# -----------------------------------------------------------------------------
widget_queue: asyncio.Queue[str] = asyncio.Queue()

# -----------------------------------------------------------------------------
# 3) Mapping of widget_id → set of connection_keys that have subscribed.
# -----------------------------------------------------------------------------
uuid_to_clients: Dict[str, Set[str]] = {}

# -----------------------------------------------------------------------------
# 4) Public API to register a widget’s configuration.
# -----------------------------------------------------------------------------
def register_widget(widget_id: str, config: Dict[str, Any]) -> None:
    """
    Store the given config under widget_id in the global registry.
    Call this when an AsyncWidget is instantiated (or first rendered).
    """
    _WIDGET_REGISTRY[widget_id] = config

    return True

# -----------------------------------------------------------------------------
# 5) Public API to retrieve a widget’s configuration by widget_id.
# -----------------------------------------------------------------------------
def get_widget_config(widget_id: str) -> Dict[str, Any]:
    """
    Fetch the configuration dict for the given widget_id.
    Returns None if no such entry exists.
    """
    return _WIDGET_REGISTRY.get(widget_id)

# -----------------------------------------------------------------------------
# 6) Public API to enqueue a widget_id for background processing.
# -----------------------------------------------------------------------------
def enqueue_widget(widget_id: str) -> None:
    """
    Put the widget_id onto the global widget_queue for the worker to pick up.
    """
    try:
        widget_queue.put_nowait(widget_id)
    except asyncio.QueueFull:
        # The queue is full; you may choose to log or handle overflow here.
        pass

# -----------------------------------------------------------------------------
# 7) Public API to add a subscriber (connection_key) for a given widget_id.
# -----------------------------------------------------------------------------
def subscribe_client(widget_id: str, connection_key: str) -> None:
    """
    Record that connection_key wants updates for widget_id.
    """
    subscribers = uuid_to_clients.setdefault(widget_id, set())
    subscribers.add(connection_key)

# -----------------------------------------------------------------------------
# 8) Public API to get all subscribers for a given widget_id.
# -----------------------------------------------------------------------------
def get_subscribers(widget_id: str) -> Set[str]:
    """
    Return the set of connection_keys subscribed to widget_id.
    If no one has subscribed yet, returns an empty set.
    """
    return uuid_to_clients.get(widget_id, set())

# -----------------------------------------------------------------------------
# 9) Public API to clear all subscribers after pushing an update.
# -----------------------------------------------------------------------------
def clear_subscribers(widget_id: str) -> None:
    """
    Remove the widget_id entry from uuid_to_clients, so we don’t resend.
    """
    uuid_to_clients.pop(widget_id, None)
