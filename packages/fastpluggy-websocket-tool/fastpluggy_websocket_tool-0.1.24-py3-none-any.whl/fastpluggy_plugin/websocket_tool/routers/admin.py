# admin.py - Admin interface for WebSocket management
import inspect
import time

from fastapi import Request, Depends, APIRouter, Query
from starlette.responses import JSONResponse

from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.flash import FlashMessage
from fastpluggy.core.menu.decorator import menu_entry
from fastpluggy.core.widgets import TableWidget, AutoLinkWidget
from fastpluggy.core.widgets.categories.data.debug import DebugView

from fastpluggy.fastpluggy import FastPluggy
from fastpluggy_plugin.ui_tools.extra_widget.display.code import CodeWidget
from ..ws_manager import DisconnectReason
from fastpluggy_plugin.ui_tools.extra_widget.display.alert import AlertWidget
from fastpluggy_plugin.ui_tools.extra_widget.display.card import CardWidget
from fastpluggy_plugin.ui_tools.extra_widget.layout.grid import GridWidget
from fastpluggy.core.widgets.categories.data.raw import RawWidget

ws_admin_router = APIRouter()


@menu_entry(label="WS Clients", type='admin', icon="fa-solid fa-network-wired")
@ws_admin_router.get("/clients", name="websocket_clients_dashboard")
async def websocket_clients_dashboard(request: Request, view_builder=Depends(get_view_builder)):
    """WebSocket clients dashboard with health monitoring"""
    manager = FastPluggy.get_global("ws_manager")

    if manager is None:
        return view_builder.generate(
            request,
            title="WebSocket Clients",
            widgets=[
                AlertWidget(
                    content="WebSocket manager is not available",
                    alert_type="danger"
                )
            ]
        )

    # Get comprehensive data
    clients = manager.list_clients()
    stats = manager.get_stats()

    # Prepare enhanced client data for table
    enhanced_clients = []
    for client in clients:
        enhanced_client = {
            **client,
            "health_status": _get_health_status_badge(client["health_score"]),
            "connection_duration": f"{client['duration']:.1f}s",
            "message_stats": f"{client['messages_sent']}/{client['messages_failed']}",
            "last_seen": f"{client['time_since_pong']:.1f}s ago" if client.get('time_since_pong') else "N/A"
        }
        enhanced_clients.append(enhanced_client)

    # Create stats summary cards
    stats_cards = [
        CardWidget(
            title="Active Connections",
            content=f"<h3 class='text-primary'>{stats['total_active_connections']}</h3>",
            footer=f"Total ever: {stats['total_connections']}"
        ),
        CardWidget(
            title="Queue Status",
            content=f"<h3 class='text-info'>{stats['queue_size']}/{stats['max_queue_size']}</h3>",
            footer=f"Utilization: {stats['queue_utilization']:.1%}"
        ),
        CardWidget(
            title="Message Stats",
            content=f"<h3 class='text-success'>{stats['messages_sent']}</h3>",
            footer=f"Failed: {stats['messages_failed']}"
        ),
        CardWidget(
            title="Health Score",
            content=f"<h3 class='{_get_health_color(stats)}'>{_calculate_overall_health(clients):.1%}</h3>",
            footer=f"Timeouts: {stats['heartbeat_timeouts']}"
        )
    ]

    # Health alerts
    alerts = []
    if stats['queue_utilization'] > 0.8:
        alerts.append(AlertWidget(
            content=f"Queue utilization is high: {stats['queue_utilization']:.1%}",
            alert_type="warning"
        ))

    if stats['queue_overflows'] > 0:
        alerts.append(AlertWidget(
            content=f"Queue overflows detected: {stats['queue_overflows']} messages dropped",
            alert_type="danger"
        ))

    return view_builder.generate(
        request,
        title="WebSocket Management Dashboard",
        widgets=[
            GridWidget.create_responsive_grid(alerts, cols_md=2),
            GridWidget.create_responsive_grid(stats_cards, cols_md=2),
            TableWidget(
                title="Connected Clients",
                data=enhanced_clients,
                field_callbacks={
                    "client_id": lambda val: f"<code>{val}</code>",
                    "type": lambda val: f"<span class='badge bg-info'>{val}</span>",
                    "health_status": lambda val: val,
                    "is_alive": lambda
                        val: "<span class='badge bg-success'>Online</span>" if val else "<span class='badge bg-danger'>Offline</span>",
                    "health_score": lambda val: f"{val:.2f}",
                    "connection_duration": lambda val: val,
                    "message_stats": lambda val: f"<small>✓{val.split('/')[0]} ✗{val.split('/')[1]}</small>",
                    "last_seen": lambda val: f"<small>{val}</small>"
                },
                links=[
                    AutoLinkWidget(
                        label="Disconnect",
                        route_name="disconnect_client",
                        param_inputs={'client_id': '<client_id>'},
                        css_class="btn btn-sm btn-outline-danger"
                    )
                ],
                exclude_fields=['connected_at', 'last_ping', 'last_pong', 'messages_sent', 'messages_failed',
                                'duration', 'time_since_pong']
            ),
            DebugView(data={"clients": clients, "stats": stats}, collapsed=True),
            AutoLinkWidget(
                label="Websocket configured handlers",
                route_name="websocket_handlers_dashboard",
            )

        ]
    )


@ws_admin_router.post("/clients/{client_id}/disconnect", name="disconnect_client")
async def disconnect_client(
        request: Request,
        client_id: str,
        reason: str = Query("admin_disconnect", description="Disconnect reason")
):
    """Disconnect client with reason tracking"""
    manager = FastPluggy.get_global("ws_manager")

    if manager is None:
        FlashMessage.add(request, "WebSocket manager not available", "error")
        return JSONResponse(
            content={"success": False, "error": "Manager not available"},
            status_code=503
        )

    try:
        # Validate and convert reason
        disconnect_reason = DisconnectReason.SERVER_DISCONNECT
        if reason in [r.value for r in DisconnectReason]:
            disconnect_reason = DisconnectReason(reason)

        # Disconnect the client
        await manager.disconnect(client_id, disconnect_reason)

        FlashMessage.add(
            request,
            f"Client {client_id} disconnected successfully",
            "success"
        )

        return JSONResponse(content={
            "success": True,
            "client_id": client_id,
            "reason": disconnect_reason.value,
            "timestamp": time.time()
        })

    except Exception as e:
        error_msg = f"Failed to disconnect {client_id}: {str(e)}"
        FlashMessage.add(request, error_msg, "error")
        return JSONResponse(
            content={"success": False, "error": error_msg},
            status_code=500
        )


@ws_admin_router.post("/broadcast", name="admin_broadcast")
async def admin_broadcast_message(
        request: Request,
        message: str = Query(..., description="Message to broadcast"),
        level: str = Query("info", description="Message level")
):
    """Admin broadcast message endpoint"""
    manager = FastPluggy.get_global("ws_manager")

    if manager is None:
        FlashMessage.add(request, "WebSocket manager not available", "error")
        return JSONResponse(
            content={"success": False, "error": "Manager not available"},
            status_code=503
        )

    try:
        from ..schema.ws_message import WebSocketMessage

        ws_message = WebSocketMessage(
            type="admin_message",
            content=message,
            meta={
                "level": level,
                "timestamp": time.time(),
                "from": "admin"
            }
        )

        success = manager.notify(ws_message)

        if success:
            FlashMessage.add(request, "Message broadcasted successfully", "success")
            return JSONResponse(content={
                "success": True,
                "message": "Broadcast sent",
                "timestamp": time.time()
            })
        else:
            error_msg = "Failed to queue broadcast message"
            FlashMessage.add(request, error_msg, "error")
            return JSONResponse(
                content={"success": False, "error": error_msg},
                status_code=503
            )

    except Exception as e:
        error_msg = f"Error broadcasting message: {str(e)}"
        FlashMessage.add(request, error_msg, "error")
        return JSONResponse(
            content={"success": False, "error": error_msg},
            status_code=500
        )


# Helper functions for UI formatting
def _get_health_status_badge(health_score: float) -> str:
    """Generate health status badge HTML"""
    if health_score > 0.8:
        return "<span class='badge bg-success'>Healthy</span>"
    elif health_score > 0.5:
        return "<span class='badge bg-warning'>Warning</span>"
    else:
        return "<span class='badge bg-danger'>Unhealthy</span>"


def _get_health_color(stats: dict) -> str:
    """Get CSS color class based on overall system health"""
    if stats['queue_utilization'] > 0.9 or stats['queue_overflows'] > 0:
        return "text-danger"
    elif stats['queue_utilization'] > 0.7:
        return "text-warning"
    else:
        return "text-success"


def _calculate_overall_health(clients: list) -> float:
    """Calculate overall system health score"""
    if not clients:
        return 1.0

    total_health = sum(client['health_score'] for client in clients if client['is_alive'])
    active_clients = sum(1 for client in clients if client['is_alive'])

    return total_health / max(1, active_clients)


@ws_admin_router.get("/handlers", name="websocket_handlers_dashboard")
async def websocket_handlers_dashboard(request: Request, view_builder=Depends(get_view_builder)):
    """Dashboard showing registered WebSocket handlers in backend and frontend"""
    manager = FastPluggy.get_global("ws_manager")

    if manager is None:
        return view_builder.generate(
            request,
            title="WebSocket Handlers",
            widgets=[
                AlertWidget(
                    content="WebSocket manager is not available",
                    alert_type="danger"
                )
            ]
        )

    # Get backend handlers
    backend_handlers = []
    for msg_type, handler in manager.handlers.items():
        handler_info = {
            "type": msg_type,
            "handler": handler.__name__,
            "module": handler.__module__,
            "signature": str(inspect.signature(handler)),
            "doc": handler.__doc__ or "No documentation"
        }
        backend_handlers.append(handler_info)

    # JavaScript to fetch frontend handlers
    frontend_handlers_js = """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        if (window.WebSocketRegistry) {
            const types = window.WebSocketRegistry.getRegisteredTypes();
            const tableBody = document.getElementById('frontend-handlers-table').getElementsByTagName('tbody')[0];

            if (types.length === 0) {
                const row = tableBody.insertRow();
                const cell = row.insertCell(0);
                cell.colSpan = 2;
                cell.innerHTML = '<em>No frontend handlers registered</em>';
            } else {
                types.forEach(type => {
                    const handlers = window.WebSocketRegistry.handlers[type];
                    const row = tableBody.insertRow();
                    const typeCell = row.insertCell(0);
                    const countCell = row.insertCell(1);

                    typeCell.innerHTML = `<code>${type}</code>`;
                    countCell.innerHTML = handlers.length;
                });
            }
        } else {
            document.getElementById('frontend-handlers-container').innerHTML = 
                '<div class="alert alert-warning">WebSocketRegistry not available in this context</div>';
        }
    });
    </script>
    """

    # Frontend handlers table HTML
    frontend_handlers_html = f"""
    <div id="frontend-handlers-container">
        <h4>Frontend Handlers</h4>
        <p class="text-muted">Handlers registered in the browser's WebSocketRegistry</p>
        <table id="frontend-handlers-table" class="table table-striped">
            <thead>
                <tr>
                    <th>Message Type</th>
                    <th>Handler Count</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td colspan="2"><em>Loading...</em></td>
                </tr>
            </tbody>
        </table>
    </div>
    {frontend_handlers_js}
    """

    return view_builder.generate(
        request,
        title="WebSocket Handlers Registry",
        widgets=[
            AlertWidget(
                content="This page shows all registered WebSocket message handlers in both backend and frontend.",
                alert_type="info"
            ),
            TableWidget(
                title="Backend Handlers",
                data=backend_handlers,
                field_callbacks={
                    "type": lambda val: f"<code>{val}</code>",
                    "handler": lambda val: f"<code>{val}</code>",
                    "module": lambda val: f"<code>{val}</code>",
                    "signature": lambda val: f"<code>{val}</code>",
                    "doc": lambda val: f"<small>{val}</small>"
                }
            ),
            RawWidget(source=frontend_handlers_html),
            CodeWidget(
                title="How to Register Handlers",
                language="python",
                code="""
# Backend handler registration
from fastpluggy.fastpluggy import FastPluggy

async def handle_message(client_id: str, data: dict):
    # Handle the message
    print(f"Received message from {client_id}: {data}")

# Get the WebSocket manager
ws_manager = FastPluggy.get_global("ws_manager")

# Register the handler
ws_manager.register_handler("plugin.action", handle_message)
                """
            ),
            CodeWidget(
                title="Frontend Handler Registration",
                language="javascript",
                code="""
// Register a handler for a specific message type
function handleMessage(data) {
    console.log("Received message:", data);
}

// Using the safe registration method (recommended)
safeRegisterHandler("plugin.action", handleMessage);

// Or directly with WebSocketRegistry
window.WebSocketRegistry.registerHandler("plugin.action", handleMessage);
                """
            )
        ]
    )
