from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, Literal

from gradio.components.base import Component
from gradio.events import Events
from gradio.i18n import I18nData

if TYPE_CHECKING:
    from gradio.components import Timer


class Browser(Component):
    """
    Creates a browser component with navigation controls and iframe display.
    """

    EVENTS = [
        Events.change,
        Events.input,
        Events.submit,
    ]

    def __init__(
        self,
        value: str | Callable | None = None,
        *,
        url: str = "https://example.com",
        width: str = "100%",
        min_height: str = "500px",
        show_hostname: bool = False,
        placeholder: str | None = None,
        label: str | I18nData | None = None,
        every: Timer | float | None = None,
        inputs: Component | Sequence[Component] | set[Component] | None = None,
        show_label: bool | None = None,
        scale: int | None = None,
        min_width: int = 160,
        interactive: bool | None = None,
        visible: bool | Literal["hidden"] = True,
        rtl: bool = False,
        elem_id: str | None = None,
        elem_classes: list[str] | str | None = None,
        render: bool = True,
        key: int | str | tuple[int | str, ...] | None = None,
        preserved_by_key: list[str] | str | None = "value",
    ):
        """
        Parameters:
            value: URL to display in the browser iframe
            url: Initial URL to load in the browser
            width: Width of the browser component  
            min_height: Minimum height of the browser component
            show_hostname: If True, shows full URL in address bar; if False, shows only path
            placeholder: placeholder hint to provide behind textbox.
            label: the label for this component
            every: Continously calls `value` to recalculate it if `value` is a function
            inputs: Components that are used as inputs to calculate `value` if `value` is a function
            show_label: if True, will display label.
            scale: relative size compared to adjacent Components
            min_width: minimum pixel width
            interactive: if True, will be rendered as an editable component
            visible: If False, component will be hidden
            rtl: If True, sets the direction of the text to right-to-left
            elem_id: An optional string that is assigned as the id of this component in the HTML DOM
            elem_classes: An optional list of strings that are assigned as the classes of this component in the HTML DOM
            render: If False, component will not render be rendered in the Blocks context
            key: in a gr.render, Components with the same key across re-renders are treated as the same component
            preserved_by_key: A list of parameters from this component's constructor
        """
        self.url = url or value or "https://example.com"
        self.width = width
        self.min_height = min_height
        self.show_hostname = show_hostname
        self.placeholder = placeholder
        self.rtl = rtl
        super().__init__(
            label=label,
            every=every,
            inputs=inputs,
            show_label=show_label,
            scale=scale,
            min_width=min_width,
            interactive=interactive,
            visible=visible,
            elem_id=elem_id,
            elem_classes=elem_classes,
            value=value,
            render=render,
            key=key,
            preserved_by_key=preserved_by_key,
        )

    def preprocess(self, payload: str | None) -> str | None:
        """
        Parameters:
            payload: the URL entered.
        Returns:
            Passes URL value as a {str} into the function.
        """
        return None if payload is None else str(payload)

    def postprocess(self, value: str | None) -> str | None:
        """
        Parameters:
            value: Expects a URL {str} to display in browser.
        Returns:
            The URL to display in the browser iframe.
        """
        return None if value is None else str(value)

    def api_info(self) -> dict[str, Any]:
        return {"type": "string"}

    def example_payload(self) -> Any:
        return "https://example.com"

    def example_value(self) -> Any:
        return "https://example.com"
