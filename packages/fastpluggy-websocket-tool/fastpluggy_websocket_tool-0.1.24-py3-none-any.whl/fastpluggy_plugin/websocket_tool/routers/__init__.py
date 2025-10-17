import logging
import os

from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import FileResponse

from fastpluggy.core.dependency import get_module_manager
from .admin import ws_admin_router
from .ws import ws_router
from .info import info_router

ws_tool_router = APIRouter(
    tags=["websocket"]
)

ws_tool_router.include_router(ws_router)
ws_tool_router.include_router(ws_admin_router)
ws_tool_router.include_router(info_router)


@ws_tool_router.get("/sw_info.json")
async def get_sw_info(module_manager=Depends(get_module_manager)):
    from ..plugin import WebSocketToolPlugin
    module = WebSocketToolPlugin()
    module_version =module.module_version
    return {"version": module_version}


@ws_tool_router.get("/service-worker.js")
async def service_worker(v: str = Query(None)):
    """Serve the service worker JavaScript file"""
    logging.info(f"Service worker {v} requested")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "../static/service-worker.js")

    if not os.path.exists(file_path):
        logging.error(f"Service worker file not found: {file_path}")
        raise HTTPException(status_code=404, detail="Service worker file not found")

    response = FileResponse(file_path)
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response
