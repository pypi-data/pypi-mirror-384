import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional, Dict, Tuple, Callable, List, Annotated, Any

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from fastpluggy.core.tools.inspect_tools import call_with_injection, InjectDependency

from .schema import ConnectionMetadata, DisconnectReason
from .schema.ws_message import WebSocketMessage
from .config import WebSocketSettings


class ConnectionManager:
    def __init__(self):
        # Load configuration
        self.settings = WebSocketSettings()

        # Queue with size limit to prevent memory issues
        self.queue: asyncio.Queue[Tuple[WebSocketMessage, Optional[str]]] = asyncio.Queue(
            maxsize=self.settings.max_queue_size
        )
        self._consumer_task: asyncio.Task | None = None
        self._heartbeat_task: asyncio.Task | None = None

        # Unified connection storage with metadata
        self.active_connections: Dict[str, ConnectionMetadata] = {}

        # Event loop reference
        self.loop: asyncio.AbstractEventLoop | None = None

        # Simple statistics
        self.stats = {
            "total_connections": 0,
            "total_disconnections": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "queue_overflows": 0,
            "heartbeat_timeouts": 0
        }

        # Shutdown flag
        self._shutdown = False

        # Handler registry
        self.handlers: Dict[str, Callable] = {}

        # Event hooks
        self.on_client_connected_hooks: List[Callable] = []
        self.on_client_disconnected_hooks: List[Callable] = []
        self.on_message_received_hooks: List[Callable] = []
        self.on_message_failed_hooks: List[Callable] = []

    # ---------- Handler registry ----------
    def register_handler(self, msg_type: str, handler: Callable):
        """Register a handler for a specific message type"""
        logger.info(f"Registered WebSocket handler for type: {msg_type}")
        self.handlers[msg_type] = handler

    def get_handler(self, msg_type: str) -> Optional[Callable]:
        """Get the handler for a specific message type"""
        return self.handlers.get(msg_type)

    # ---------- Hook registration ----------
    def add_hook(self, event: str, hook: Callable):
        """Add a hook for a specific event"""
        if event == "client_connected":
            self.on_client_connected_hooks.append(hook)
        elif event == "client_disconnected":
            self.on_client_disconnected_hooks.append(hook)
        elif event == "message_received":
            self.on_message_received_hooks.append(hook)
        elif event == "message_failed":
            self.on_message_failed_hooks.append(hook)
        else:
            logger.warning(f"Unknown event type: {event}")

    async def _call_client_connected_hooks(self, connection_key: str):
        """Call all client connected hooks"""
        for hook in self.on_client_connected_hooks:
            try:
                await hook(connection_key)
            except Exception as e:
                logger.error(f"Error in client_connected hook: {e}")

    async def _call_client_disconnected_hooks(self, connection_key: str, reason: DisconnectReason):
        """Call all client disconnected hooks"""
        for hook in self.on_client_disconnected_hooks:
            try:
                await hook(connection_key, reason)
            except Exception as e:
                logger.error(f"Error in client_disconnected hook: {e}")

    async def _call_message_received_hooks(self, client_id: str, msg_type: str, payload: dict):
        """Call all message received hooks"""
        for hook in self.on_message_received_hooks:
            try:
                await hook(client_id, msg_type, payload)
            except Exception as e:
                logger.error(f"Error in message_received hook: {e}")

    async def _call_message_failed_hooks(self, client_id: str, msg_type: str, payload: dict):
        """Call all message failed hooks"""
        for hook in self.on_message_failed_hooks:
            try:
                await hook(client_id, msg_type, payload)
            except Exception as e:
                logger.error(f"Error in message_failed hook: {e}")

    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None):
        """Connect a new WebSocket client with metadata tracking"""
        if self._shutdown:
            logger.warning("Connection rejected: Manager is shutting down")
            return False

        # Initialize loop and background tasks on first connection
        if self.loop is None:
            self.loop = asyncio.get_event_loop()
            await self._start_background_tasks()

        try:
            await websocket.accept()

            # Create connection metadata
            metadata = ConnectionMetadata(websocket=websocket)

            # Determine connection key
            if client_id:
                #if client_id in self.active_connections:
                #    logger.warning(f"Duplicate client_id {client_id}, disconnecting old connection")
                #    await self._disconnect_client(client_id, DisconnectReason.DUPLICATE_CLIENT)
                connection_key = client_id
            else:
                connection_key = f"anon-{uuid.uuid4()}"

            # Store the connection_key in the websocket object for later use
            websocket.scope["client_id"] = connection_key

            self.active_connections[connection_key] = metadata
            self.stats["total_connections"] += 1
            logger.info(f"Client {connection_key} connected. Total: {len(self.active_connections)}")

            # Call client connected hooks
            await self._call_client_connected_hooks(connection_key)

            return True

        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {e}")
            return False

    async def disconnect(self, websocket_or_client_id, reason: DisconnectReason = DisconnectReason.SERVER_DISCONNECT):
        """Disconnect a WebSocket client with reason tracking"""
        if isinstance(websocket_or_client_id, str):
            await self._disconnect_client(websocket_or_client_id, reason)
        else:
            for key, metadata in list(self.active_connections.items()):
                if metadata.websocket == websocket_or_client_id:
                    await self._disconnect_client(key, reason)
                    break

    async def _disconnect_client(self, connection_key: str, reason: DisconnectReason):
        metadata = self.active_connections.pop(connection_key, None)
        if not metadata:
            return
        metadata.is_alive = False
        await self._close_websocket_safely(metadata.websocket)
        self.stats["total_disconnections"] += 1
        logger.info(f"Client {connection_key} disconnected ({reason.value}). Duration: {metadata.connection_duration:.1f}s")

        # Call client disconnected hooks
        await self._call_client_disconnected_hooks(connection_key, reason)

    async def _close_websocket_safely(self, websocket: WebSocket):
        try:
            await websocket.close()
        except Exception as e:
            logger.debug(f"Error closing WebSocket (expected): {e}")

    async def _send_ping_message(self, metadata: ConnectionMetadata, connection_key: str):
        ping_message = WebSocketMessage(
            type="ping",
            content="ping",
            meta={
                "timestamp": time.time(),
                "from": "server",
                "ping_id": f"ping_{int(time.time())}"
            }
        )
        try:
            await metadata.websocket.send_json(ping_message.to_json())
        except Exception as e:
            logger.error(f"Failed to send ping to {connection_key}: {e}")
            raise

    async def send_to_client(self, message: WebSocketMessage, connection_key: Optional[str] = None):
        if self._shutdown:
            return False
        if message.type == "pong" and connection_key in self.active_connections:
            self.active_connections[connection_key].last_pong = time.time()
            return True

        payload = message.to_json()
        if connection_key:
            metadata = self.active_connections.get(connection_key)
            if not metadata or not metadata.is_alive:
                return False
            try:
                await metadata.websocket.send_json(payload)
                metadata.messages_sent += 1
                self.stats["messages_sent"] += 1
                # Call message received hooks
                await self._call_message_received_hooks(connection_key, message.type, payload)
                return True
            except WebSocketDisconnect:
                await self._disconnect_client(connection_key, DisconnectReason.CLIENT_DISCONNECT)
                return False
            except Exception as e:
                metadata.messages_failed += 1
                self.stats["messages_failed"] += 1
                # Call message failed hooks
                await self._call_message_failed_hooks(connection_key, message.type, payload)
                await self._disconnect_client(connection_key, DisconnectReason.SEND_ERROR)
                return False
        else:
            await self.broadcast(message)
            return True

    async def broadcast(self, message: WebSocketMessage):
        if self._shutdown:
            return
        payload = message.to_json()
        tasks = [self._safe_send_with_metadata(key, meta, payload)
                 for key, meta in self.active_connections.items() if meta.is_alive]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successes = sum(1 for r in results if r is True)
        failures = len(results) - successes
        self.stats["messages_sent"] += successes
        self.stats["messages_failed"] += failures

    async def _safe_send_with_metadata(self, connection_key: str, metadata: ConnectionMetadata, payload: dict) -> bool:
        try:
            await metadata.websocket.send_json(payload)
            metadata.messages_sent += 1
            # Call message received hooks
            await self._call_message_received_hooks(connection_key, payload.get("type", "unknown"), payload)
            return True
        except WebSocketDisconnect:
            await self._disconnect_client(connection_key, DisconnectReason.CLIENT_DISCONNECT)
            return False
        except Exception as e:
            metadata.messages_failed += 1
            # Call message failed hooks
            await self._call_message_failed_hooks(connection_key, payload.get("type", "unknown"), payload)
            await self._disconnect_client(connection_key, DisconnectReason.SEND_ERROR)
            return False

    async def _start_background_tasks(self):
        if not self._consumer_task or self._consumer_task.done():
            self._consumer_task = self.loop.create_task(self._consumer())
        if self.settings.enable_heartbeat and (not self._heartbeat_task or self._heartbeat_task.done()):
            self._heartbeat_task = self.loop.create_task(self._heartbeat_monitor())

    async def _consumer(self):
        while not self._shutdown:
            try:
                message, connection_key = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                await self.send_to_client(message, connection_key)
                self.queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def _heartbeat_monitor(self):
        while not self._shutdown:
            await asyncio.sleep(self.settings.heartbeat_interval)
            if not self._shutdown:
                await self._check_all_connections()

    async def _check_all_connections(self):
        now = time.time()
        timeout_thresh = now - self.settings.heartbeat_timeout
        to_disconnect = []
        for key, meta in self.active_connections.items():
            if not meta.is_alive:
                continue
            if meta.last_pong < timeout_thresh:
                to_disconnect.append(key)
                continue
            try:
                await self._send_ping_message(meta, key)
                meta.last_ping = now
            except Exception:
                to_disconnect.append(key)
        for key in to_disconnect:
            self.stats["heartbeat_timeouts"] += 1
            await self._disconnect_client(key, DisconnectReason.HEARTBEAT_TIMEOUT)

    def notify(self, message: WebSocketMessage, connection_key: Optional[str] = None) -> bool:
        if self._shutdown or not self.loop:
            return False
        try:
            self.loop.call_soon_threadsafe(self._try_enqueue, message, connection_key)
            return True
        except Exception:
            return False

    def _try_enqueue(self, message: WebSocketMessage, connection_key: Optional[str]):
        try:
            self.queue.put_nowait((message, connection_key))
        except asyncio.QueueFull:
            self.stats["queue_overflows"] += 1

    def list_clients(self) -> list[dict]:
        return [
            {
                "client_id": key,
                "type": "anonymous" if key.startswith("anon-") else "named",
                "connected_at": meta.connected_at,
                "duration": meta.connection_duration,
                "last_ping": meta.last_ping,
                "last_pong": meta.last_pong,
                "messages_sent": meta.messages_sent,
                "messages_failed": meta.messages_failed,
                "health_score": meta.health_score,
                "is_alive": meta.is_alive,
                "time_since_pong": meta.time_since_last_pong
            }
            for key, meta in self.active_connections.items()
        ]

    async def process_message(self, websocket:WebSocket, client_id: str, data: Any) -> bool:
        """Process an incoming message using registered handlers"""
        try:
            # Parse the message
            msg_type = data.get("type", "unknown")

            # Check if message type follows the plugin.action format
            if msg_type != "unknown" and "." not in msg_type:
                logger.warning(f"Message type '{msg_type}' from {client_id} does not follow the recommended 'plugin.action' format")

                # Send a warning message back to the client
                try:
                    from .schema.ws_message import WebSocketMessage
                    warning_msg = WebSocketMessage(
                        type="error",
                        content=f"Message type '{msg_type}' does not follow the recommended 'plugin.action' format",
                        meta={
                            "original_type": msg_type,
                            "warning": "format"
                        }
                    )
                    await self.send_to_client(warning_msg, client_id)
                    logger.warning(f"Message type '{msg_type}' does not follow the recommended 'plugin.action' format")
                except Exception as e:
                    logger.exception(f"Failed to send format warning to {client_id}: {e}")

            # Get the handler for this message type
            handler = self.get_handler(msg_type)

            if handler:
                # Call the handler with dependency injection
                try:
                    # Create context dictionary with dependencies that can be injected
                    context_dict = {
                        WebSocket: websocket
                    }

                    # Call the handler with dependency injection
                    await call_with_injection(
                        handler, 
                        context_dict=context_dict, 
                        user_kwargs={
                          #  "websocket": websocket,
                            "client_id": client_id,
                            "data": data
                        }
                    )
                    return True
                except Exception as e:
                    logger.exception(f"Error in message handler for type {msg_type}: {e}")
                    return False
            else:
                logger.warning(f"No handler registered for message type: {msg_type}")

                # Send a warning message back to the client
                try:
                    from .schema.ws_message import WebSocketMessage
                    warning_msg = WebSocketMessage(
                        type="error",
                        content=f"No handler registered for message type: {msg_type}",
                        meta={
                            "original_type": msg_type,
                            "warning": "unhandled"
                        }
                    )
                    await self.send_to_client(warning_msg, client_id)
                    logger.warning(f"No handler registered for message type: {msg_type}")
                except Exception as e:
                    logger.exception(f"Failed to send unhandled warning to {client_id}: {e}")

                return False

        except json.JSONDecodeError:
            logger.warning(f"Received invalid JSON from {client_id}")
            return False
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            return False

    def get_stats(self) -> dict:
        live_named = sum(1 for k, m in self.active_connections.items() if m.is_alive and not k.startswith("anon-"))
        live_anon = sum(1 for k, m in self.active_connections.items() if m.is_alive and k.startswith("anon-"))
        return {
            **self.stats,
            "total_active_connections": live_named + live_anon,
            "active_named_connections": live_named,
            "active_anonymous_connections": live_anon,
            "queue_size": self.queue.qsize(),
            "max_queue_size": self.settings.max_queue_size,
            "queue_utilization": self.queue.qsize() / self.settings.max_queue_size,
            "is_shutdown": self._shutdown,
            "registered_handlers": len(self.handlers),
            "registered_hooks": {
                "client_connected": len(self.on_client_connected_hooks),
                "client_disconnected": len(self.on_client_disconnected_hooks),
                "message_received": len(self.on_message_received_hooks),
                "message_failed": len(self.on_message_failed_hooks)
            }
        }

    @asynccontextmanager
    async def connection_context(self, websocket: WebSocket, client_id: Optional[str] = None):
        connected = await self.connect(websocket, client_id)
        try:
            if not connected:
                raise Exception("Failed to establish connection")
            yield
        except WebSocketDisconnect:
            logger.info(f"Client {client_id or 'anonymous'} disconnected normally")
        except Exception as e:
            logger.error(f"Connection error for {client_id or 'anonymous'}: {e}")
        finally:
            if connected:
                await self.disconnect(client_id if client_id else websocket, DisconnectReason.CLIENT_DISCONNECT)

    async def shutdown(self, timeout: float = 30.0):
        self._shutdown = True
        tasks = [t for t in (self._consumer_task, self._heartbeat_task) if t and not t.done()]
        for t in tasks:
            t.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        for key in list(self.active_connections.keys()):
            await self._disconnect_client(key, DisconnectReason.SHUTDOWN)
        logger.info("WebSocket manager shutdown complete")
