import logging
import time

from fastpluggy.fastpluggy import FastPluggy

from .schema.ws_message import WebSocketMessage
from .ws_manager import ConnectionManager


async def handle_pong(websocket, payload):
    client_id = websocket.query_params.get("clientId", "anonymous")
    echo_pong = payload.get("meta", {}).get("ping_id", "unk_ping_id")

    reply = WebSocketMessage(
        type="echo",
        content=f"Echo: {echo_pong}",
        meta={
            "timestamp": time.time(),
            "from": client_id
        }
    )

    manager = FastPluggy.get_global("ws_manager")
    await manager.send_to_client(reply, client_id)

async def on_client_connected(client_id: str):
    """Hook called when a client connects"""
    logging.info(f"Client connected hook: {client_id}")
    manager = FastPluggy.get_global("ws_manager")

    # Send welcome message
    welcome_msg = WebSocketMessage(
        type="system.client_connected",
        content=f"Welcome {client_id}!",
        meta={
            "event": "connected"
        }
    )

    await manager.send_to_client(welcome_msg, client_id)


async def on_client_disconnected(client_id: str, reason):
    """Hook called when a client disconnects"""
    logging.info(f"Client disconnected hook: {client_id}, reason: {reason}")

async def on_message_received(client_id: str, msg_type: str, payload: dict):
    """Hook called when a message is successfully sent"""

    logging.debug(f"Message sent to {client_id}, type: {msg_type}")

def setup_websocket_handlers():
    """Register handlers and hooks with the connection manager"""
    ws_manager = ConnectionManager()

    # Register message handlers
    #ws_manager.register_handler("ping", handle_ping)
    #ws_manager.register_handler("chat", handle_chat)
    ws_manager.register_handler("system.pong", handle_pong)

    # Register event hooks
    ws_manager.add_hook("client_connected", on_client_connected)
    ws_manager.add_hook("client_disconnected", on_client_disconnected)

    FastPluggy.register_global("ws_manager", ws_manager)

    logging.info("WebSocket handlers and hooks registered")
