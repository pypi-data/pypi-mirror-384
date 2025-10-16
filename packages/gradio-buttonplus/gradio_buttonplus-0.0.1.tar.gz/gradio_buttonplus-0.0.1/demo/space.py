
import gradio as gr
from app import demo as app
import os

_docs = {'ButtonPlus': {'description': 'Creates a button that can be assigned arbitrary .click() events. The value (label) of the button can be used as an input to the function (rarely used) or set via the output of a function.', 'members': {'__init__': {'value': {'type': 'str | I18nData | Callable', 'default': '"Run"', 'description': 'default text for the button to display. If a function is provided, the function will be called each time the app loads to set the initial value of this component.'}, 'every': {'type': 'Timer | float | None', 'default': 'None', 'description': 'continuously calls `value` to recalculate it if `value` is a function (has no effect otherwise). Can provide a Timer whose tick resets `value`, or a float that provides the regular interval for the reset Timer.'}, 'inputs': {'type': 'Component | Sequence[Component] | set[Component] | None', 'default': 'None', 'description': 'components that are used as inputs to calculate `value` if `value` is a function (has no effect otherwise). `value` is recalculated any time the inputs change.'}, 'variant': {'type': 'Literal["primary", "secondary", "stop", "huggingface"]', 'default': '"secondary"', 'description': "sets the background and text color of the button. Use 'primary' for main call-to-action buttons, 'secondary' for a more subdued style, 'stop' for a stop button, 'huggingface' for a black background with white text, consistent with Hugging Face's button styles."}, 'size': {'type': 'Literal["sm", "md", "lg"]', 'default': '"lg"', 'description': 'size of the button. Can be "sm", "md", or "lg".'}, 'icon': {'type': 'str | Path | None', 'default': 'None', 'description': 'URL or path to the icon file to display within the button. If None, no icon will be displayed.'}, 'link': {'type': 'str | None', 'default': 'None', 'description': 'URL to open when the button is clicked. If None, no link will be used.'}, 'visible': {'type': 'bool | Literal["hidden"]', 'default': 'True', 'description': 'If False, component will be hidden. If "hidden", component will be visually hidden and not take up space in the layout but still exist in the DOM.'}, 'interactive': {'type': 'bool', 'default': 'True', 'description': 'if False, the ButtonPlus will be in a disabled state.'}, 'elem_id': {'type': 'str | None', 'default': 'None', 'description': 'an optional string that is assigned as the id of this component in the HTML DOM. Can be used for targeting CSS styles.'}, 'elem_classes': {'type': 'list[str] | str | None', 'default': 'None', 'description': 'an optional list of strings that are assigned as the classes of this component in the HTML DOM. Can be used for targeting CSS styles.'}, 'render': {'type': 'bool', 'default': 'True', 'description': 'if False, component will not render be rendered in the Blocks context. Should be used if the intention is to assign event listeners now but render the component later.'}, 'key': {'type': 'int | str | tuple[int | str, ...] | None', 'default': 'None', 'description': "in a gr.render, Components with the same key across re-renders are treated as the same component, not a new component. Properties set in 'preserved_by_key' are not reset across a re-render."}, 'preserved_by_key': {'type': 'list[str] | str | None', 'default': '"value"', 'description': "A list of parameters from this component's constructor. Inside a gr.render() function, if a component is re-rendered with the same key, these (and only these) parameters will be preserved in the UI (if they have been changed by the user or an event listener) instead of re-rendered based on the values provided during constructor."}, 'scale': {'type': 'int | None', 'default': 'None', 'description': 'relative size compared to adjacent Components. For example if Components A and B are in a Row, and A has scale=2, and B has scale=1, A will be twice as wide as B. Should be an integer. scale applies in Rows, and to top-level Components in Blocks where fill_height=True.'}, 'min_width': {'type': 'int | None', 'default': 'None', 'description': 'minimum pixel width, will wrap if not sufficient screen space to satisfy this value. If a certain scale value results in this Component being narrower than min_width, the min_width parameter will be respected first.'}, 'help': {'type': 'str | I18nData | None', 'default': 'None', 'description': 'A string of help text to display in a tooltip when hovering over the button.'}}, 'postprocess': {'value': {'type': 'str | None', 'description': 'string corresponding to the button label'}}, 'preprocess': {'return': {'type': 'str | None', 'description': '(Rarely used) the `str` corresponding to the button label when the button is clicked'}, 'value': None}}, 'events': {'click': {'type': None, 'default': None, 'description': 'Triggered when the ButtonPlus is clicked.'}}}, '__meta__': {'additional_interfaces': {}, 'user_fn_refs': {'ButtonPlus': []}}}

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
# `gradio_buttonplus`

<div style="display: flex; gap: 7px;">
<img alt="Static Badge" src="https://img.shields.io/badge/version%20-%200.0.1%20-%20orange">  
</div>

Advanced Button Component for Gradio UI
""", elem_classes=["md-custom"], header_links=True)
    app.render()
    gr.Markdown(
"""
## Installation

```bash
pip install gradio_buttonplus
```

## Usage

```python

import gradio as gr
from gradio_buttonplus import ButtonPlus


with gr.Blocks(theme=gr.themes.Ocean()) as demo:
    gr.HTML("<h1><center>ButtonPlus Component Demo</center></h1>")
    with gr.Row():
        with gr.Column():
            btn = ButtonPlus("⚙️", help="This button triggers an action.")        
            btn_2 = ButtonPlus("Another Test", help="This is a demo test")
        


if __name__ == "__main__":
    demo.launch()

```
""", elem_classes=["md-custom"], header_links=True)


    gr.Markdown("""
## `ButtonPlus`

### Initialization
""", elem_classes=["md-custom"], header_links=True)

    gr.ParamViewer(value=_docs["ButtonPlus"]["members"]["__init__"], linkify=[])


    gr.Markdown("### Events")
    gr.ParamViewer(value=_docs["ButtonPlus"]["events"], linkify=['Event'])




    gr.Markdown("""

### User function

The impact on the users predict function varies depending on whether the component is used as an input or output for an event (or both).

- When used as an Input, the component only impacts the input signature of the user function.
- When used as an output, the component only impacts the return signature of the user function.

The code snippet below is accurate in cases where the component is used as both an input and an output.

- **As input:** Is passed, (Rarely used) the `str` corresponding to the button label when the button is clicked.
- **As output:** Should return, string corresponding to the button label.

 ```python
def predict(
    value: str | None
) -> str | None:
    return value
```
""", elem_classes=["md-custom", "ButtonPlus-user-fn"], header_links=True)




    demo.load(None, js=r"""function() {
    const refs = {};
    const user_fn_refs = {
          ButtonPlus: [], };
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
