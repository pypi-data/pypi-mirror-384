import logging
from typing import Annotated, Any

from fastpluggy.core.module_base import FastPluggyBaseModule
from fastpluggy.core.tools.inspect_tools import InjectDependency
from fastpluggy.fastpluggy import FastPluggy
from .config import WebSocketSettings
from .extra_widget.websocket_details_widget import WebSocketDetailsWidget


def get_ws_router():
    from .routers import ws_tool_router
    return ws_tool_router


class WebSocketToolPlugin(FastPluggyBaseModule):
    module_name: str = "websocket_tool"
    module_version: str = "0.1.21"

    module_menu_name: str = "WebsocketTool"
    module_menu_icon: str = "fa-solid fa-rss"
    module_menu_type: str = "no"
    module_mount_url: str = ""

    module_router: Any = get_ws_router
    module_settings: Any = WebSocketSettings

    depends_on: dict = {'ui_tools': '>=0.0.5'}

    extra_js_files: list = [
        "/app_static/websocket_tool/websocket-client.js",
        "/app_static/websocket_tool/scripts.js",
    ]

    def on_load_complete(self, fast_pluggy: Annotated[FastPluggy, InjectDependency]) -> None:
        from .register_handlers import setup_websocket_handlers
        setup_websocket_handlers()

        try:
            if fast_pluggy.module_manager.is_module_loaded("tasks_worker"):
                #from fastpluggy_plugin.tasks_worker.notifiers.registry import register_notifier, \
                #    register_global_notification_rules
                #from fastpluggy_plugin.tasks_worker.schema.task_event import TaskEvent
                #from .notifiers.websocket import WebSocketNotifier

                #websocket = WebSocketNotifier(config={}, events=[TaskEvent.ALL])
                #register_notifier(websocket)
                pass
                # register_global_notification_rules([
                #     {
                #         "name": websocket.name,
                #         "events": ["*"]
                #     }
                # ])
            else:
                logging.info("Module 'tasks_worker' not loaded, skipping notifier setup.")

        except Exception as e:
            logging.exception("Error initializing notifier for WebSocketTool")

        #try:
        #    from .extra_widget.async_worker import start_async_widget_worker
        #    start_async_widget_worker()
        #except Exception as err:
        #    logging.exception(f"Error on start of start_async_widget_worker : {err}")
