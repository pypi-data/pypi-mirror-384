# ws.py - WebSocket router with core functionality
import json
import logging
import os
import time
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi import Body, Query
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from starlette.responses import JSONResponse

from fastpluggy.core.flash import FlashMessage
from fastpluggy.core.tools.fastapi import redirect_to_previous
from fastpluggy.fastpluggy import FastPluggy
from ..schema.ws_message import WebSocketMessage
from ..ws_manager import DisconnectReason

ws_router = APIRouter(
    prefix="/ws",
    tags=["websocket"]
)


@ws_router.websocket("/{client_id}")
@ws_router.websocket("")  # fallback if no client_id
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    """Example WebSocket endpoint using handler registry and hooks"""
    manager = FastPluggy.get_global("ws_manager")
    if not manager:
        logging.error("WebSocket manager not available")
        await websocket.close(code=1011, reason="Server error")
        return

    # Extract client_id from query params if not provided
    if client_id is None:
        client_id = websocket.query_params.get("clientId")
    if client_id is None:
        client_id = websocket.scope.get("client_id")

    logging.info(f"WebSocket connection attempt: {client_id}")

    # Use the connection context manager for automatic cleanup
    async with manager.connection_context(websocket, client_id):
        try:
            while True:
                # Receive message
                message = await websocket.receive()
                message_type = message.get("type", "")

                # If a disconnect message is received, exit the loop gracefully before calling receive() again
                if message_type in ("websocket.disconnect", "websocket.close"):
                    logging.info(f"Client {client_id or 'anonymous'} sent disconnect ({message_type}), closing loop")
                    break

                if message_type == "websocket.receive" and "text" in message:
                    # Process text message
                    data = message["text"]
                    logging.debug(f"Received text from {client_id or 'anonymous'}: {data}")
                    data = json.loads(data)

                    # Process message using handler registry
                    success = await manager.process_message(websocket, client_id, data)
                elif message_type == "websocket.receive" and "bytes" in message:
                    # Process binary data
                    binary_data = message["bytes"]
                    logging.debug(f"Received binary data from {client_id or 'anonymous'}: {len(binary_data)} bytes")

                    # For binary data, we just acknowledge receipt
                    success = await manager.process_message(websocket, client_id, binary_data)
                else:
                    # Only warn for truly unknown types, ignore disconnect which is handled above
                    logging.warning(f"Received unknown message type from {client_id or 'anonymous'}: {message_type}")
                    success = False

                if not success and message_type == "websocket.receive" and "text" in message:
                    # Fallback for unhandled text message types
                    try:
                        payload = json.loads(data)
                        reply = WebSocketMessage(
                            type="error",
                            content="Unhandled message type",
                            meta={
                                "original_type": payload.get("type", "unknown")
                            }
                        )
                        await manager.send_to_client(reply, client_id)
                    except json.JSONDecodeError:
                        logging.warning(f"Received invalid JSON from {client_id}")

        except WebSocketDisconnect:
            logging.info(f"Client {client_id or 'anonymous'} disconnected normally")
        except Exception as e:
            logging.exception(f"WebSocket error for {client_id or 'anonymous'}: {e}")


@ws_router.post("/send-message")
async def send_message(
        request: Request,
        payload: WebSocketMessage = Body(...),
        method: str = Query('web', description="Response method: 'web' or 'api'"),
        client_id: Optional[str] = Query(None, description="Target specific client (None for broadcast)")
):
    """Send message with improved error handling"""
    manager = FastPluggy.get_global("ws_manager")

    if manager is None:
        error_msg = "WebSocket manager not available"
        if method == "web":
            FlashMessage.add(request=request, message=error_msg, category='error')
            return redirect_to_previous(request)
        else:
            raise HTTPException(status_code=503, detail=error_msg)

    # Get current stats
    stats = manager.get_stats()

    if stats["total_active_connections"] == 0:
        error_msg = "No active WebSocket connections"
        if method == "web":
            FlashMessage.add(request=request, message=error_msg, category='error')
            return redirect_to_previous(request)
        else:
            raise HTTPException(status_code=404, detail=error_msg)

    try:
        # Use thread-safe notify method
        success = manager.notify(payload, client_id)

        if not success:
            error_msg = "Failed to queue message"
            if method == "web":
                FlashMessage.add(request=request, message=error_msg, category='error')
                return redirect_to_previous(request)
            else:
                raise HTTPException(status_code=503, detail=error_msg)

        # Success message
        target_desc = f"client {client_id}" if client_id else "all connected clients"
        success_msg = f"Message queued for {target_desc}"

        if method == "web":
            FlashMessage.add(request=request, message=success_msg, category="success")
            return redirect_to_previous(request)
        else:
            return JSONResponse(content={
                "success": True,
                "message": success_msg,
                "target": client_id,
                "stats": {
                    "active_connections": stats["total_active_connections"],
                    "queue_size": stats["queue_size"]
                }
            })

    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        logging.error(error_msg)

        if method == "web":
            FlashMessage.add(request=request, message=error_msg, category='error')
            return redirect_to_previous(request)
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@ws_router.delete("/clients/{client_id}")
async def disconnect_websocket_client(
        client_id: str,
        reason: str = Query("admin_disconnect", description="Reason for disconnection")
):
    """Administratively disconnect a specific client"""
    manager = FastPluggy.get_global("ws_manager")

    if manager is None:
        raise HTTPException(status_code=503, detail="WebSocket manager not available")

    # Validate disconnect reason
    try:
        disconnect_reason = DisconnectReason(reason) if reason in [r.value for r in
                                                                   DisconnectReason] else DisconnectReason.SERVER_DISCONNECT
    except ValueError:
        disconnect_reason = DisconnectReason.SERVER_DISCONNECT

    try:
        await manager.disconnect(client_id, disconnect_reason)
        return {
            "success": True,
            "message": f"Client {client_id} disconnected",
            "reason": disconnect_reason.value,
            "timestamp": time.time()
        }
    except Exception as e:
        logging.error(f"Failed to disconnect client {client_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect client: {str(e)}")


# Health check endpoint moved to info.py
# @ws_router.get("/health")
# async def websocket_health_check():
#     """Health check endpoint for monitoring"""
#     # Implementation moved to info.py

#
# @ws_router.get("/service-worker.js")
# async def service_worker(v: str = Query(None)):
#     """Serve the service worker JavaScript file"""
#     logging.info(f"Service worker {v} requested")
#     base_dir = os.path.dirname(os.path.abspath(__file__))
#     file_path = f"{base_dir}/../static/js/service-worker.js"
#
#     if not os.path.exists(file_path):
#         logging.error(f"Service worker file not found: {file_path}")
#         raise HTTPException(status_code=404, detail="Service worker file not found")
#
#     response = FileResponse(file_path)
#     response.headers["Service-Worker-Allowed"] = "/"
#     response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
#     return response
