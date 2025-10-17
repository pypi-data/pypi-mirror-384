from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, Literal

from gradio.components.base import Component
from gradio.events import Events
from gradio.i18n import I18nData

if TYPE_CHECKING:
    from gradio.components import Timer


class AIContext(Component):
    """
    Creates an AI context visualization component showing message stack with token counts.
    """

    EVENTS = [
        Events.change,
    ]

    def __init__(
        self,
        value: list | dict | Callable | None = None,
        *,
        count_tokens_fn: Callable[[Any], int] | None = None,
        label: str | I18nData | None = "AI Context",
        every: Timer | float | None = None,
        inputs: Component | Sequence[Component] | set[Component] | None = None,
        scale: int | None = None,
        min_width: int = 160,
        interactive: bool | None = False,
        visible: bool | Literal["hidden"] = True,
        elem_id: str | None = None,
        elem_classes: list[str] | str | None = None,
        render: bool = True,
        key: int | str | tuple[int | str, ...] | None = None,
    ):
        """
        Parameters:
            value: list of messages or dict containing messages. If a function is provided, the function will be called each time the app loads to set the initial value of this component.
            count_tokens_fn: function to count tokens in a message. If None, uses character count / 4 heuristic.
            label: the label for this component, displayed above the component if `show_label` is `True`.
            every: Continously calls `value` to recalculate it if `value` is a function (has no effect otherwise).
            inputs: Components that are used as inputs to calculate `value` if `value` is a function (has no effect otherwise).
            show_label: if True, will display label.
            scale: relative size compared to adjacent Components.
            min_width: minimum pixel width.
            interactive: if True, will be rendered as interactive; if False, will be read-only.
            visible: If False, component will be hidden.
            elem_id: An optional string that is assigned as the id of this component in the HTML DOM.
            elem_classes: An optional list of strings that are assigned as the classes of this component in the HTML DOM.
            render: If False, component will not render be rendered in the Blocks context.
            key: in a gr.render, Components with the same key across re-renders are treated as the same component.
        """
        self.count_tokens_fn = count_tokens_fn
        super().__init__(
            label=label,
            every=every,
            inputs=inputs,
            show_label=False,
            scale=scale,
            min_width=min_width,
            interactive=interactive,
            visible=visible,
            elem_id=elem_id,
            elem_classes=elem_classes,
            value=value,
            render=render,
            key=key,
        )

    def preprocess(self, payload: Any) -> Any:
        """
        Parameters:
            payload: the data from the frontend.
        Returns:
            Passes the data through unchanged.
        """
        return payload

    def postprocess(self, value: Any) -> dict[str, Any] | None:
        """
        Parameters:
            value: messages list or dict containing messages.
        Returns:
            The formatted data for the frontend with token counts.
        """
        if value is None:
            return {"messages": [], "tokens_count": []}

        messages = []
        if isinstance(value, list):
            messages = value
        elif isinstance(value, dict) and "messages" in value:
            messages = value["messages"]
        else:
            messages = [value] if value else []

        tokens_count = [self._count_tokens(msg) for msg in messages]

        return {"messages": messages, "tokens_count": tokens_count}

    def _count_tokens(self, message: dict) -> int:
        """Count tokens in a message using the configured function or default heuristic."""
        if self.count_tokens_fn:
            return self.count_tokens_fn(message)

        import json

        content = json.dumps(message) if isinstance(message, dict) else str(message)
        return max(1, len(content) // 4)

    def api_info(self) -> dict[str, Any]:
        return {"type": "object"}

    def example_payload(self) -> Any:
        return {
            "messages": [
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        }

    def example_value(self) -> Any:
        return {
            "messages": [
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        }
