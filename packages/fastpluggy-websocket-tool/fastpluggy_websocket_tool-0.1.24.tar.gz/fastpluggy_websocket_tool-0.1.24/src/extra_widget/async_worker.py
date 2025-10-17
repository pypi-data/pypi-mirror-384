# async_worker.py

import asyncio
from typing import Any, Dict, Set

from fastpluggy.fastpluggy import FastPluggy
from .async_registry import widget_queue, get_widget_config
from .async_widget import AsyncWidget
from ..schema.ws_message import WebSocketMessage
from ..ws_manager import ConnectionManager


async def widget_worker():
    """
    Continuously pull widget_id strings from widget_queue, render each AsyncWidget’s subwidgets,
    and then push the resulting HTML over WebSocket to any clients that subscribed for this widget_id.
    """
    while True:
        try:
            widget_id: str = await widget_queue.get()
        except asyncio.CancelledError:
            break

        config: Dict[str, Any] = get_widget_config(widget_id)
        if not config:
            # No registry entry—nothing to do
            widget_queue.task_done()
            continue

        async_widget: AsyncWidget = config.get("instance")
        if not async_widget:
            widget_queue.task_done()
            continue

        # 1) Render the inner HTML for this widget
        try:
            html: str = async_widget.render_inner()
        except Exception as exc:
            html = f"<div class='text-danger'>Error rendering widget: {exc}</div>"

        manager: ConnectionManager =  FastPluggy.get_global("ws_manager")
        # 2) Look up all WebSocket clients that subscribed to this widget_id
        #subscribers: Set[str] = manager.uuid_to_clients.get(widget_id, set())
        ll = manager.list_clients()
        subscribers: Set[str] = [item['client_id'] for item in ll if item['client_id'] in manager.uuid_to_clients]

        # 3) For each subscriber, send a WebSocketMessage of type "async_widget"
        for conn_key in subscribers:
            payload = WebSocketMessage(
                type="async_widget",
                content=None,
                meta={
                    "widget_id": widget_id,
                    "html": html
                }
            )
            await manager.send_to_client(payload, conn_key)

        # 4) Once pushed, remove those subscribers so we don’t resend
        #uuid_to_clients.pop(widget_id, None)

        widget_queue.task_done()

# async_worker_starter.py


def start_async_widget_worker():
    """
    Schedule widget_worker() on the same loop that ConnectionManager uses.
    Call this once at application startup, after initializing manager.loop.
    """
    # Ensure ConnectionManager has its loop set
    loop = asyncio.get_event_loop()

    # Schedule widget_worker() as a background task on manager.loop
    loop.create_task(widget_worker())