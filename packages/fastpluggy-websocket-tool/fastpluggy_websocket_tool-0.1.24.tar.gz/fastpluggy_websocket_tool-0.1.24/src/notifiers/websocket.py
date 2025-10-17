# notifiers/websocket.py

from fastpluggy_plugin.tasks_worker.notifiers.base import BaseNotifier, LogStreamEvent, NotificationEvent
from fastpluggy_plugin.tasks_worker.schema.task_event import event_matches, TaskEvent
from ..schema.ws_message import WebSocketMessage


class WebSocketNotifier(BaseNotifier):
    name = "websocket_notifier"

    # def _safe_schedule(self, coro):
    #     from fastpluggy.fastpluggy import FastPluggy
    #     from websocket_tool.ws_manager import ConnectionManager
    #     manager : ConnectionManager= FastPluggy.get_global("ws_manager")
    #     if not manager:
    #         print("[WebSocketNotifier] No ws_manager; dropping message.")
    #         return
    #
    #     manager.process(coro)

    # loop = manager.get_loop()
    # # Only enqueue if the loop is still alive
    # if loop.is_running() and not loop.is_closed():
    #     loop.call_soon_threadsafe(loop.create_task, coro)
    # else:
    #     print(
    #         "[WebSocketNotifier] ws_manager.loop not running (closed=%s) (running=%s); dropping message.",
    #         loop.is_closed(), loop.is_running()
    #     )

    def on_task_init(self, task_id: str):
        # (no-op)
        ...

    def on_task_done(self, task_id: str):
        try:
            from fastpluggy.fastpluggy import FastPluggy
            manager = FastPluggy.get_global("ws_manager")
            if not manager:
                return

            msg = WebSocketMessage(
                type="tasks_worker." + TaskEvent.task_success,
                content="[END OF LOG]",
                meta={"event": "__TASK_DONE__", "task_id": task_id},
            )
            # self._safe_schedule(manager.broadcast(msg))
            self.push_to_queue('broadcast', msg)

        except Exception as e:
            print(f"[WebSocketNotifier] on_task_done failed for {task_id}: {e}")

    def handle_log(self, event: LogStreamEvent):
        try:
            # from fastpluggy.fastpluggy import FastPluggy
            # manager = FastPluggy.get_global("ws_manager")
            # if not manager:
            #     return

            msg = WebSocketMessage(
                type="tasks_worker." + TaskEvent.logs,
                content=event.record.getMessage(),
                meta={"task_id": event.task_id, "level": event.record.levelname},
            )
            #           self._safe_schedule(manager.broadcast(msg))
            self.push_to_queue('broadcast', msg)
        except Exception as e:
            # use print to avoid recursion
            print(f"[WebSocketNotifier] handle_log failed for {event.task_id}: {e}")

    def notify(self, event: NotificationEvent):
        if not event_matches(event_type=event.event_type, rule_events=self.events):
            return

        try:
            msg = WebSocketMessage(
                type="tasks_worker." + event.event_type,
                content=event.message,
                meta={
                    "task_id": event.task_id,
                    "event": event.event_type,
                    "function": event.function,
                    "success": event.success,
                    "error": event.error,
                    # "link": event.link,
                    "timestamp": event.timestamp.isoformat()
                }
            )
            self.push_to_queue(
                'send_to_client',
                msg,
                # client_id=getattr(event.context, "client_id", None) # todo: use auth to get client_id
            )
        except Exception as e:
            print(f"[WebSocketNotifier] notify failed for {event.task_id}: {e}")

    def push_to_queue(self, param, msg):
        from fastpluggy.fastpluggy import FastPluggy
        from ..ws_manager import ConnectionManager
        manager: ConnectionManager = FastPluggy.get_global("ws_manager")
        if not manager:
            return
        manager.notify(msg) # todo: client_id should come here
