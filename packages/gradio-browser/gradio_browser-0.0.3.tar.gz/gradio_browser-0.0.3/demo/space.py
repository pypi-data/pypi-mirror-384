
import gradio as gr
from app import demo as app
import os

_docs = {'Browser': {'description': 'Creates a browser component with navigation controls and iframe display.', 'members': {'__init__': {'value': {'type': 'str | Callable | None', 'default': 'None', 'description': 'URL to display in the browser iframe'}, 'url': {'type': 'str', 'default': '"https://example.com"', 'description': 'Initial URL to load in the browser'}, 'width': {'type': 'str', 'default': '"100%"', 'description': 'Width of the browser component'}, 'min_height': {'type': 'str', 'default': '"500px"', 'description': 'Minimum height of the browser component'}, 'show_hostname': {'type': 'bool', 'default': 'False', 'description': 'If True, shows full URL in address bar; if False, shows only path'}, 'placeholder': {'type': 'str | None', 'default': 'None', 'description': 'placeholder hint to provide behind textbox.'}, 'label': {'type': 'str | I18nData | None', 'default': 'None', 'description': 'the label for this component'}, 'every': {'type': 'Timer | float | None', 'default': 'None', 'description': 'Continously calls `value` to recalculate it if `value` is a function'}, 'inputs': {'type': 'Component | Sequence[Component] | set[Component] | None', 'default': 'None', 'description': 'Components that are used as inputs to calculate `value` if `value` is a function'}, 'show_label': {'type': 'bool | None', 'default': 'None', 'description': 'if True, will display label.'}, 'scale': {'type': 'int | None', 'default': 'None', 'description': 'relative size compared to adjacent Components'}, 'min_width': {'type': 'int', 'default': '160', 'description': 'minimum pixel width'}, 'interactive': {'type': 'bool | None', 'default': 'None', 'description': 'if True, will be rendered as an editable component'}, 'visible': {'type': 'bool | Literal["hidden"]', 'default': 'True', 'description': 'If False, component will be hidden'}, 'rtl': {'type': 'bool', 'default': 'False', 'description': 'If True, sets the direction of the text to right-to-left'}, 'elem_id': {'type': 'str | None', 'default': 'None', 'description': 'An optional string that is assigned as the id of this component in the HTML DOM'}, 'elem_classes': {'type': 'list[str] | str | None', 'default': 'None', 'description': 'An optional list of strings that are assigned as the classes of this component in the HTML DOM'}, 'render': {'type': 'bool', 'default': 'True', 'description': 'If False, component will not render be rendered in the Blocks context'}, 'key': {'type': 'int | str | tuple[int | str, ...] | None', 'default': 'None', 'description': 'in a gr.render, Components with the same key across re-renders are treated as the same component'}, 'preserved_by_key': {'type': 'list[str] | str | None', 'default': '"value"', 'description': "A list of parameters from this component's constructor"}}, 'postprocess': {'value': {'type': 'str | None', 'description': 'Expects a URL {str} to display in browser.'}}, 'preprocess': {'return': {'type': 'str | None', 'description': 'Passes URL value as a {str} into the function.'}, 'value': None}}, 'events': {'change': {'type': None, 'default': None, 'description': 'Triggered when the value of the Browser changes either because of user input (e.g. a user types in a textbox) OR because of a function update (e.g. an image receives a value from the output of an event trigger). See `.input()` for a listener that is only triggered by user input.'}, 'input': {'type': None, 'default': None, 'description': 'This listener is triggered when the user changes the value of the Browser.'}, 'submit': {'type': None, 'default': None, 'description': 'This listener is triggered when the user presses the Enter key while the Browser is focused.'}}}, '__meta__': {'additional_interfaces': {}, 'user_fn_refs': {'Browser': []}}}

abs_path = os.path.join(os.path.dirname(__file__), "css.css")

with gr.Blocks(
    css=abs_path,
    theme=gr.themes.Default(
        font_mono=[
            gr.themes.GoogleFont("Inconsolata"),
            "monospace",
        ],
    ),
) as demo:
    gr.Markdown(
"""
# `gradio_browser`

<div style="display: flex; gap: 7px;">
<a href="https://pypi.org/project/gradio_browser/" target="_blank"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/gradio_browser"></a>  
</div>

Python library for easily interacting with trained machine learning models
""", elem_classes=["md-custom"], header_links=True)
    app.render()
    gr.Markdown(
"""
## Installation

```bash
pip install gradio_browser
```

## Usage

```python
import gradio as gr
from gradio_browser import Browser

with gr.Blocks(title="Browser Component Demo", fill_height=True) as demo:
    gr.Markdown("# 🌐 Custom Browser Component")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Controls")
            url_input = gr.Textbox(
                label="Enter URL",
                value="https://www.gradio.app/",
                placeholder="https://www.gradio.app/",
            )

            show_hostname = gr.Checkbox(
                label="Show full hostname in address bar", value=True
            )

            gr.Markdown(
                \"\"\"
            ### Features:
            - ← → Navigation buttons with history
            - ↻ Refresh button  
            - ↗ Open in new tab button
            - Address bar supports both full URLs and paths
            - Enter key navigation
            \"\"\"
            )

            gr.Markdown("### Try these URLs:")

            gr.Button("Gradio.com").click(
                lambda: "https://www.gradio.app/", outputs=[url_input]
            )
            gr.Button("Example.com").click(
                lambda: "https://example.com", outputs=[url_input]
            )

        with gr.Column(scale=3):
            browser = Browser(
                url="https://example.com",
                show_hostname=True,
                min_height="600px",
                scale=1,
            )

    # Update browser when URL changes
    url_input.change(lambda url: url, inputs=[url_input], outputs=[browser])

    # Update show_hostname setting (requires component rebuild)
    show_hostname.change(
        lambda show_host, url: Browser(value=url, show_hostname=show_host),
        inputs=[show_hostname, url_input],
        outputs=[browser],
    )


if __name__ == "__main__":
    demo.launch()

```
""", elem_classes=["md-custom"], header_links=True)


    gr.Markdown("""
## `Browser`

### Initialization
""", elem_classes=["md-custom"], header_links=True)

    gr.ParamViewer(value=_docs["Browser"]["members"]["__init__"], linkify=[])


    gr.Markdown("### Events")
    gr.ParamViewer(value=_docs["Browser"]["events"], linkify=['Event'])




    gr.Markdown("""

### User function

The impact on the users predict function varies depending on whether the component is used as an input or output for an event (or both).

- When used as an Input, the component only impacts the input signature of the user function.
- When used as an output, the component only impacts the return signature of the user function.

The code snippet below is accurate in cases where the component is used as both an input and an output.

- **As input:** Is passed, passes URL value as a {str} into the function.
- **As output:** Should return, expects a URL {str} to display in browser.

 ```python
def predict(
    value: str | None
) -> str | None:
    return value
```
""", elem_classes=["md-custom", "Browser-user-fn"], header_links=True)




    demo.load(None, js=r"""function() {
    const refs = {};
    const user_fn_refs = {
          Browser: [], };
    requestAnimationFrame(() => {

        Object.entries(user_fn_refs).forEach(([key, refs]) => {
            if (refs.length > 0) {
                const el = document.querySelector(`.${key}-user-fn`);
                if (!el) return;
                refs.forEach(ref => {
                    el.innerHTML = el.innerHTML.replace(
                        new RegExp("\\b"+ref+"\\b", "g"),
                        `<a href="#h-${ref.toLowerCase()}">${ref}</a>`
                    );
                })
            }
        })

        Object.entries(refs).forEach(([key, refs]) => {
            if (refs.length > 0) {
                const el = document.querySelector(`.${key}`);
                if (!el) return;
                refs.forEach(ref => {
                    el.innerHTML = el.innerHTML.replace(
                        new RegExp("\\b"+ref+"\\b", "g"),
                        `<a href="#h-${ref.toLowerCase()}">${ref}</a>`
                    );
                })
            }
        })
    })
}

""")

demo.launch()
