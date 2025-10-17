# async_widget.py

import asyncio
from typing import Any, Dict, List, Union, Optional
from fastpluggy.core.widgets.base import AbstractWidget

from .async_registry import register_widget, widget_queue

class AsyncWidget(AbstractWidget):
    """
    Wraps subwidgets so that:
      - On first render, we show a spinner + JS that calls safeRegisterHandler("async_widget", …).
      - We save (widget_id → config) in a registry & enqueue widget_id on widget_queue.
      - A background worker will call render_inner() and push HTML via WebSocket using msg.type="async_widget".
    """

    widget_type :str = "async"
    template_name :str = "ui_tools/extra_widget/async_ws_wrapper.html.j2"
    category :str = "async"
    description :str = "Asynchronously loads subwidgets (via safeRegisterHandler)."
    icon:str  = "sync-alt"

    def __init__(
        self,
        subwidgets: Optional[List[Union[AbstractWidget, Dict[str, Any]]]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.subwidgets = subwidgets or []

        # 1) Instead of generating a new UUID, use the inherited self.widget_id
        wid = self.widget_id

        # 2) Register this instance in the global registry under widget_id
        register_widget(wid, {
            "instance": self,
            "subwidgets": self.subwidgets,
        })

        # 3) Enqueue for background processing using widget_id
        try:
            widget_queue.put_nowait(wid)
        except asyncio.QueueFull:
            # Queue overflow; you can log or handle as needed
            pass

    def process(self, **kwargs) -> None:
        """
        On initial render, we do NOT process subwidgets. We only need self.widget_id
        so that the template can emit the spinner + safeRegisterHandler JS.
        """
        return

    def render_inner(self, **kwargs) -> str:
        """
        Called by the background worker to produce the final HTML:
         - Look up subwidgets from the registry under self.widget_id
         - Call .process() + .render() on each
         - Return the combined HTML string
        """
        config = register_widget(self.widget_id)  # or use a getter
        if not config:
            raise RuntimeError(f"No registry entry for AsyncWidget {self.widget_id}")

        html_parts: List[str] = []
        for item in config["subwidgets"]:
            if isinstance(item, AbstractWidget):
                w = item
                w.process(**kwargs)
                html_parts.append(w.render(**kwargs))
            elif isinstance(item, dict):
                w = item.pop("widget")
                w.process(**kwargs)
                html_parts.append(w.render(**kwargs))
            else:
                raise ValueError("Invalid subwidget type inside AsyncWidget")

        return "\n".join(html_parts)
