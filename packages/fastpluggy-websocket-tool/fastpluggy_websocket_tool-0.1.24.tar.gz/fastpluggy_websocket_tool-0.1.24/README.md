# WebSocketTool Plugin for FastPluggy

The WebSocketTool plugin provides real-time WebSocket communication capabilities for FastPluggy applications. It enables bidirectional communication between the server and clients, supports message broadcasting, targeted messaging, and integrates with the task worker system for real-time task monitoring.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Quick Start](#quick-start)
- [License](#license)

## Installation

### Requirements

- FastPluggy framework >=0.0.3
- UI Tools plugin >=0.0.3

### Quick Start & Installation 

```bash
pip install fastpluggy-websocket-tool
```

## Configuration

The WebSocketTool plugin can be configured through the `WebSocketSettings` class:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `max_queue_size` | int | 10000 | Maximum size of the message queue |
| `enable_heartbeat` | bool | True | Enable heartbeat mechanism to monitor connection health |
| `heartbeat_interval` | int | 30 | Seconds between heartbeat pings |
| `heartbeat_timeout` | int | 60 | Seconds before a connection is considered timed out |

## Documentation

The WebSocketTool plugin has comprehensive documentation available in the `docs` directory:

- [Quick Start Guide](docs/quick_start.md) - Basic examples to help you get started
- [Core Components](docs/core_components.md) - Details about ConnectionManager, WebSocketMessage, and AsyncWidget
- [WebSocket Handlers](docs/websocket_handlers.md) - Information about the handler registry system and event hooks
- [WebSocket Message Types](docs/ws.md) - Message types and naming conventions
- [API Reference](docs/api_reference.md) - WebSocket and REST API endpoints
- [Widgets](docs/widgets.md) - Available widgets including AsyncWidget and WebSocketDetailsWidget
- [Tasks Worker Integration](docs/tasks_worker_integration.md) - Integration with the Tasks Worker module
- [Advanced Usage](docs/advanced_usage.md) - Advanced usage, health monitoring, and troubleshooting

## Quick Start

For a quick introduction to using the WebSocketTool plugin, including client-side connection examples and basic server-side usage, see the [Quick Start Guide](docs/quick_start.md).

## License

This plugin is licensed under the same license as the FastPluggy framework.