
import gradio as gr
from app import demo as app
import os

_docs = {'AIContext': {'description': 'Creates an AI context visualization component showing message stack with token counts.', 'members': {'__init__': {'value': {'type': 'list | dict | Callable | None', 'default': 'None', 'description': 'list of messages or dict containing messages. If a function is provided, the function will be called each time the app loads to set the initial value of this component.'}, 'count_tokens_fn': {'type': 'Callable[[Any], int] | None', 'default': 'None', 'description': 'function to count tokens in a message. If None, uses character count / 4 heuristic.'}, 'label': {'type': 'str | I18nData | None', 'default': '"AI Context"', 'description': 'the label for this component, displayed above the component if `show_label` is `True`.'}, 'every': {'type': 'Timer | float | None', 'default': 'None', 'description': 'Continously calls `value` to recalculate it if `value` is a function (has no effect otherwise).'}, 'inputs': {'type': 'Component | Sequence[Component] | set[Component] | None', 'default': 'None', 'description': 'Components that are used as inputs to calculate `value` if `value` is a function (has no effect otherwise).'}, 'scale': {'type': 'int | None', 'default': 'None', 'description': 'relative size compared to adjacent Components.'}, 'min_width': {'type': 'int', 'default': '160', 'description': 'minimum pixel width.'}, 'interactive': {'type': 'bool | None', 'default': 'False', 'description': 'if True, will be rendered as interactive; if False, will be read-only.'}, 'visible': {'type': 'bool | Literal["hidden"]', 'default': 'True', 'description': 'If False, component will be hidden.'}, 'elem_id': {'type': 'str | None', 'default': 'None', 'description': 'An optional string that is assigned as the id of this component in the HTML DOM.'}, 'elem_classes': {'type': 'list[str] | str | None', 'default': 'None', 'description': 'An optional list of strings that are assigned as the classes of this component in the HTML DOM.'}, 'render': {'type': 'bool', 'default': 'True', 'description': 'If False, component will not render be rendered in the Blocks context.'}, 'key': {'type': 'int | str | tuple[int | str, ...] | None', 'default': 'None', 'description': 'in a gr.render, Components with the same key across re-renders are treated as the same component.'}}, 'postprocess': {'value': {'type': 'typing.Any', 'description': 'messages list or dict containing messages.'}}, 'preprocess': {'return': {'type': 'typing.Any', 'description': 'Passes the data through unchanged.'}, 'value': None}}, 'events': {'change': {'type': None, 'default': None, 'description': 'Triggered when the value of the AIContext changes either because of user input (e.g. a user types in a textbox) OR because of a function update (e.g. an image receives a value from the output of an event trigger). See `.input()` for a listener that is only triggered by user input.'}}}, '__meta__': {'additional_interfaces': {}, 'user_fn_refs': {'AIContext': []}}}

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
# `gradio_aicontext`

<div style="display: flex; gap: 7px;">
<a href="https://pypi.org/project/gradio_aicontext/" target="_blank"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/gradio_aicontext"></a>  
</div>

Custom gradio component to visualize your ai context by colours and tokens' size.
""", elem_classes=["md-custom"], header_links=True)
    app.render()
    gr.Markdown(
"""
## Installation

```bash
pip install gradio_aicontext
```

## Usage

```python
import gradio as gr
from gradio_aicontext import AIContext
import json
import tiktoken


def count_tokens(message: dict) -> int:
    encoding = tiktoken.encoding_for_model("gpt-4")
    return encoding.encode(json.dumps([message])).__len__()


initial_messages = [
    {
        "role": "system",
        "content": "You are a helpful AI assistant skilled in Python programming and data analysis.",
    },
    {
        "role": "user",
        "content": "Can you help me write a function to calculate the factorial of a number?",
    },
    {
        "role": "assistant",
        "content": "I'll help you create a factorial function. Here are two approaches:\n\n```python\n# Recursive approach\ndef factorial_recursive(n):\n    if n <= 1:\n        return 1\n    return n * factorial_recursive(n - 1)\n\n# Iterative approach  \ndef factorial_iterative(n):\n    result = 1\n    for i in range(1, n + 1):\n        result *= i\n    return result\n\n# Example usage\nprint(factorial_recursive(5))  # 120\nprint(factorial_iterative(5))  # 120\n```\n\nBoth functions work well, but the iterative version is more memory efficient for large numbers.",
    },
    {"role": "user", "content": "What about using math.factorial()?"},
    {
        "role": "assistant",
        "content": "Great point! Python's built-in `math.factorial()` is the most efficient option:\n\n```python\nimport math\n\nresult = math.factorial(5)  # 120\n```\n\nIt's optimized, handles edge cases, and is the recommended approach for production code. Use custom implementations mainly for learning or when you need specific behavior.",
    },
    {"role": "user", "content": "What's the weather like in New York today?"},
    {
        "type": "function_call",
        "name": "get_weather",
        "call_id": "call_weather_123",
        "arguments": '{"location": "New York, NY", "units": "fahrenheit"}',
    },
    {
        "type": "function_call_output",
        "call_id": "call_weather_123",
        "output": '{"location": "New York, NY", "temperature": 72, "condition": "Partly Cloudy", "humidity": 65, "wind_speed": 8, "visibility": 10, "uv_index": 6, "feels_like": 75}',
    },
    {
        "role": "assistant",
        "content": "The weather in New York today is quite pleasant! Here are the details:\n\n🌤️ **Partly Cloudy** - 72°F (feels like 75°F)\n💨 Wind: 8 mph\n💧 Humidity: 65%\n👁️ Visibility: 10 miles\n☀️ UV Index: 6 (moderate)\n\nIt's a nice day to be outside!",
    },
    {
        "role": "user",
        "content": "Can you also check the forecast for tomorrow and send me an email reminder?",
    },
    {
        "type": "function_call",
        "name": "get_weather_forecast",
        "call_id": "call_forecast_456",
        "arguments": '{"location": "New York, NY", "days": 1}',
    },
    {
        "type": "function_call_output",
        "call_id": "call_forecast_456",
        "output": '{"location": "New York, NY", "forecast": [{"date": "2024-10-17", "high": 68, "low": 58, "condition": "Light Rain", "precipitation_chance": 80, "wind_speed": 12}]}',
    },
    {
        "type": "function_call",
        "name": "send_email",
        "call_id": "call_email_789",
        "arguments": '{"to": "user@example.com", "subject": "Weather Reminder: Bring an Umbrella Tomorrow!", "body": "Tomorrow\'s forecast for New York: Light rain expected with 80% chance of precipitation. High: 68°F, Low: 58°F. Don\'t forget your umbrella!"}',
    },
    {
        "type": "function_call_output",
        "call_id": "call_email_789",
        "output": '{"status": "sent", "message_id": "msg_12345", "delivered_at": "2024-10-16T20:45:30Z"}',
    },
    {
        "type": "function_call_output",
        "call_id": "call_forecast_456",
        "output": '{"location": "New York, NY", "forecast": [{"date": "2024-10-17", "high": 68, "low": 58, "condition": "Light Rain", "precipitation_chance": 80, "wind_speed": 12}]}',
    },
    {
        "type": "function_call",
        "name": "send_email",
        "call_id": "call_email_789",
        "arguments": '{"to": "user@example.com", "subject": "Weather Reminder: Bring an Umbrella Tomorrow!", "body": "Tomorrow\'s forecast for New York: Light rain expected with 80% chance of precipitation. High: 68°F, Low: 58°F. Don\'t forget your umbrella!"}',
    },
    {
        "type": "function_call_output",
        "call_id": "call_email_789",
        "output": '{"status": "sent", "message_id": "msg_12345", "delivered_at": "2024-10-16T20:45:30Z"}',
    },
    {
        "type": "function_call_output",
        "call_id": "call_forecast_456",
        "output": '{"location": "New York, NY", "forecast": [{"date": "2024-10-17", "high": 68, "low": 58, "condition": "Light Rain", "precipitation_chance": 80, "wind_speed": 12}]}',
    },
    {
        "type": "function_call",
        "name": "send_email",
        "call_id": "call_email_789",
        "arguments": '{"to": "user@example.com", "subject": "Weather Reminder: Bring an Umbrella Tomorrow!", "body": "Tomorrow\'s forecast for New York: Light rain expected with 80% chance of precipitation. High: 68°F, Low: 58°F. Don\'t forget your umbrella!"}',
    },
    {
        "type": "function_call_output",
        "call_id": "call_email_789",
        "output": '{"status": "sent", "message_id": "msg_12345", "delivered_at": "2024-10-16T20:45:30Z"}',
    },
    {
        "type": "function_call_output",
        "call_id": "call_forecast_456",
        "output": '{"location": "New York, NY", "forecast": [{"date": "2024-10-17", "high": 68, "low": 58, "condition": "Light Rain", "precipitation_chance": 80, "wind_speed": 12}]}',
    },
    {
        "type": "function_call",
        "name": "send_email",
        "call_id": "call_email_789",
        "arguments": '{"to": "user@example.com", "subject": "Weather Reminder: Bring an Umbrella Tomorrow!", "body": "Tomorrow\'s forecast for New York: Light rain expected with 80% chance of precipitation. High: 68°F, Low: 58°F. Don\'t forget your umbrella!"}',
    },
    {
        "type": "function_call_output",
        "call_id": "call_email_789",
        "output": '{"status": "sent", "message_id": "msg_12345", "delivered_at": "2024-10-16T20:45:30Z"}',
    },
    {
        "type": "function_call_output",
        "call_id": "call_forecast_456",
        "output": '{"location": "New York, NY", "forecast": [{"date": "2024-10-17", "high": 68, "low": 58, "condition": "Light Rain", "precipitation_chance": 80, "wind_speed": 12}]}',
    },
    {
        "type": "function_call",
        "name": "send_email",
        "call_id": "call_email_789",
        "arguments": '{"to": "user@example.com", "subject": "Weather Reminder: Bring an Umbrella Tomorrow!", "body": "Tomorrow\'s forecast for New York: Light rain expected with 80% chance of precipitation. High: 68°F, Low: 58°F. Don\'t forget your umbrella!"}',
    },
    {
        "type": "function_call_output",
        "call_id": "call_email_789",
        "output": '{"status": "sent", "message_id": "msg_12345", "delivered_at": "2024-10-16T20:45:30Z"}',
    },
]

with gr.Blocks(
    title="AI Context Visualization Demo",
    fill_height=True,
    css=\"\"\"
    .h-full { height: 100% !important; }
    .flex { display: flex; }
    .min-h-0 { min-height: 0; }
    
    #context-column {
        height: calc(100vh - 140px);
        max-height: calc(100vh - 140px);
        overflow: hidden;
    }
    \"\"\",
) as demo:
    gr.Markdown("# AI Context Component Demo")
    gr.Markdown("Shows token visualization for OpenAI-style conversation messages")

    with gr.Row():
        with gr.Column(scale=2):
            json_editor = gr.JSON(
                value=initial_messages, label="Raw Messages (Editable)", show_label=True
            )

        with gr.Column(scale=1, elem_id="context-column"):
            context_viz = AIContext(
                value=initial_messages,
                count_tokens_fn=count_tokens,
                elem_classes="h-full flex min-h-0",
            )

    json_editor.change(fn=lambda x: x, inputs=[json_editor], outputs=[context_viz])


if __name__ == "__main__":
    demo.launch()

```
""", elem_classes=["md-custom"], header_links=True)


    gr.Markdown("""
## `AIContext`

### Initialization
""", elem_classes=["md-custom"], header_links=True)

    gr.ParamViewer(value=_docs["AIContext"]["members"]["__init__"], linkify=[])


    gr.Markdown("### Events")
    gr.ParamViewer(value=_docs["AIContext"]["events"], linkify=['Event'])




    gr.Markdown("""

### User function

The impact on the users predict function varies depending on whether the component is used as an input or output for an event (or both).

- When used as an Input, the component only impacts the input signature of the user function.
- When used as an output, the component only impacts the return signature of the user function.

The code snippet below is accurate in cases where the component is used as both an input and an output.

- **As input:** Is passed, passes the data through unchanged.
- **As output:** Should return, messages list or dict containing messages.

 ```python
def predict(
    value: typing.Any
) -> typing.Any:
    return value
```
""", elem_classes=["md-custom", "AIContext-user-fn"], header_links=True)




    demo.load(None, js=r"""function() {
    const refs = {};
    const user_fn_refs = {
          AIContext: [], };
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
