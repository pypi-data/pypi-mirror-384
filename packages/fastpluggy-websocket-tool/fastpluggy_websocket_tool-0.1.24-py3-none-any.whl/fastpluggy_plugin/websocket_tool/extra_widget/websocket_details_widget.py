# websocket_details_widget.py

from fastpluggy.core.widgets.base import AbstractWidget


class WebSocketDetailsWidget(AbstractWidget):
    """
    Widget that displays WebSocket connection details including:
    - Connection status
    - Health score
    - Messages sent
    - Connection duration

    This widget fetches data from the WebSocket stats and clients endpoints
    and updates the UI every 5 seconds.
    """

    widget_type = "websocket_details"
    template_name = "websocket_tool/websocket_details.html.j2"
    category = "websocket"
    description = "Displays WebSocket connection details"
    icon = "rss"

    def __init__(self, **kwargs):
        """Initialize the WebSocket details widget."""
        super().__init__(**kwargs)
        self.title = kwargs.get('title', 'WebSocket Details')

    def process(self, **kwargs) -> None:
        """
        Process the widget data and prepare for rendering.
        This widget doesn't require any processing as it fetches data client-side.
        """
        pass
