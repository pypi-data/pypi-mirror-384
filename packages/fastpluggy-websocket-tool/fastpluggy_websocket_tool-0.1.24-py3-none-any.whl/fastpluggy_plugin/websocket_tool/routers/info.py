# info.py - WebSocket information router
import logging
import time

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from fastpluggy.fastpluggy import FastPluggy
from ..schema.ws_message import WebSocketMessage
from ..ws_manager import DisconnectReason

# Create a new router with the prefix "/info"
info_router = APIRouter(
    prefix="/info",
    tags=["websocket_info"]
)


@info_router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket manager statistics"""
    manager = FastPluggy.get_global("ws_manager")

    if manager is None:
        raise HTTPException(status_code=503, detail="WebSocket manager not available")

    stats = manager.get_stats()

    # Add health indicators
    health_status = "healthy"
    issues = []

    if stats["queue_utilization"] > 0.9:
        health_status = "critical"
        issues.append("Queue nearly full")
    elif stats["queue_utilization"] > 0.7:
        health_status = "warning"
        issues.append("Queue usage high")

    if stats["queue_overflows"] > 0:
        health_status = "critical"
        issues.append("Queue overflows detected")

    if stats["messages_failed"] > stats["messages_sent"] * 0.1:
        health_status = "warning"
        issues.append("High message failure rate")

    return {
        "stats": stats,
        "health": {
            "status": health_status,
            "issues": issues,
            "message_success_rate": stats["messages_sent"] / max(1, stats["messages_sent"] + stats["messages_failed"])
        },
        "timestamp": time.time()
    }


@info_router.get("/clients")
async def list_websocket_clients():
    """List all connected WebSocket clients with metadata"""
    manager = FastPluggy.get_global("ws_manager")

    if manager is None:
        raise HTTPException(status_code=503, detail="WebSocket manager not available")

    clients = manager.list_clients()

    # Add summary
    summary = {
        "total_clients": len(clients),
        "named_clients": len([c for c in clients if c["type"] == "named"]),
        "anonymous_clients": len([c for c in clients if c["type"] == "anonymous"]),
        "healthy_clients": len([c for c in clients if c["health_score"] > 0.8])
    }

    return {
        "summary": summary,
        "clients": clients,
        "timestamp": time.time()
    }


@info_router.get("/health")
async def websocket_health_check():
    """Health check endpoint for monitoring"""
    manager = FastPluggy.get_global("ws_manager")

    if manager is None:
        return {
            "status": "critical",
            "issues": ["WebSocket manager not available"],
            "timestamp": time.time()
        }

    stats = manager.get_stats()

    # Determine health status
    issues = []
    status = "healthy"

    if stats["queue_utilization"] > 0.9:
        status = "critical"
        issues.append("Queue nearly full")
    elif stats["queue_utilization"] > 0.7:
        status = "warning"
        issues.append("Queue usage high")

    if stats["queue_overflows"] > 0:
        status = "critical"
        issues.append("Queue overflows detected")

    if stats["messages_failed"] > stats["messages_sent"] * 0.1:
        status = "warning"
        issues.append("High message failure rate")

    if stats["heartbeat_timeouts"] > stats["total_connections"] * 0.05:
        status = "warning"
        issues.append("High heartbeat timeout rate")

    return {
        "status": status,
        "issues": issues,
        "stats": {
            "active_connections": stats["total_active_connections"],
            "queue_utilization": stats["queue_utilization"],
            "message_success_rate": stats["messages_sent"] / max(1, stats["messages_sent"] + stats["messages_failed"]),
            "uptime_connections": stats["total_connections"]
        },
        "timestamp": time.time()
    }