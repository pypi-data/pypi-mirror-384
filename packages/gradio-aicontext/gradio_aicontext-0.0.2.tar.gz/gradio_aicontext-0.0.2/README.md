
---
title: Gradio AI Context
sdk: gradio
sdk_version: 5.49.0
app_file: app.py
pinned: false
---

# `gradio_aicontext`
<a href="https://pypi.org/project/gradio_aicontext/" target="_blank"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/gradio_aicontext"></a>  

Custom gradio component to visualize your ai context by colours and tokens' size.

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
    css="""
    .h-full { height: 100% !important; }
    .flex { display: flex; }
    .min-h-0 { min-height: 0; }
    
    #context-column {
        height: calc(100vh - 140px);
        max-height: calc(100vh - 140px);
        overflow: hidden;
    }
    """,
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

## `AIContext`

### Initialization

<table>
<thead>
<tr>
<th align="left">name</th>
<th align="left" style="width: 25%;">type</th>
<th align="left">default</th>
<th align="left">description</th>
</tr>
</thead>
<tbody>
<tr>
<td align="left"><code>value</code></td>
<td align="left" style="width: 25%;">

```python
list | dict | Callable | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">list of messages or dict containing messages. If a function is provided, the function will be called each time the app loads to set the initial value of this component.</td>
</tr>

<tr>
<td align="left"><code>count_tokens_fn</code></td>
<td align="left" style="width: 25%;">

```python
Callable[[Any], int] | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">function to count tokens in a message. If None, uses character count / 4 heuristic.</td>
</tr>

<tr>
<td align="left"><code>label</code></td>
<td align="left" style="width: 25%;">

```python
str | I18nData | None
```

</td>
<td align="left"><code>"AI Context"</code></td>
<td align="left">the label for this component, displayed above the component if `show_label` is `True`.</td>
</tr>

<tr>
<td align="left"><code>every</code></td>
<td align="left" style="width: 25%;">

```python
Timer | float | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">Continously calls `value` to recalculate it if `value` is a function (has no effect otherwise).</td>
</tr>

<tr>
<td align="left"><code>inputs</code></td>
<td align="left" style="width: 25%;">

```python
Component | Sequence[Component] | set[Component] | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">Components that are used as inputs to calculate `value` if `value` is a function (has no effect otherwise).</td>
</tr>

<tr>
<td align="left"><code>scale</code></td>
<td align="left" style="width: 25%;">

```python
int | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">relative size compared to adjacent Components.</td>
</tr>

<tr>
<td align="left"><code>min_width</code></td>
<td align="left" style="width: 25%;">

```python
int
```

</td>
<td align="left"><code>160</code></td>
<td align="left">minimum pixel width.</td>
</tr>

<tr>
<td align="left"><code>interactive</code></td>
<td align="left" style="width: 25%;">

```python
bool | None
```

</td>
<td align="left"><code>False</code></td>
<td align="left">if True, will be rendered as interactive; if False, will be read-only.</td>
</tr>

<tr>
<td align="left"><code>visible</code></td>
<td align="left" style="width: 25%;">

```python
bool | Literal["hidden"]
```

</td>
<td align="left"><code>True</code></td>
<td align="left">If False, component will be hidden.</td>
</tr>

<tr>
<td align="left"><code>elem_id</code></td>
<td align="left" style="width: 25%;">

```python
str | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">An optional string that is assigned as the id of this component in the HTML DOM.</td>
</tr>

<tr>
<td align="left"><code>elem_classes</code></td>
<td align="left" style="width: 25%;">

```python
list[str] | str | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">An optional list of strings that are assigned as the classes of this component in the HTML DOM.</td>
</tr>

<tr>
<td align="left"><code>render</code></td>
<td align="left" style="width: 25%;">

```python
bool
```

</td>
<td align="left"><code>True</code></td>
<td align="left">If False, component will not render be rendered in the Blocks context.</td>
</tr>

<tr>
<td align="left"><code>key</code></td>
<td align="left" style="width: 25%;">

```python
int | str | tuple[int | str, ...] | None
```

</td>
<td align="left"><code>None</code></td>
<td align="left">in a gr.render, Components with the same key across re-renders are treated as the same component.</td>
</tr>
</tbody></table>


### Events

| name | description |
|:-----|:------------|
| `change` | Triggered when the value of the AIContext changes either because of user input (e.g. a user types in a textbox) OR because of a function update (e.g. an image receives a value from the output of an event trigger). See `.input()` for a listener that is only triggered by user input. |



### User function

The impact on the users predict function varies depending on whether the component is used as an input or output for an event (or both).

- When used as an Input, the component only impacts the input signature of the user function.
- When used as an output, the component only impacts the return signature of the user function.

The code snippet below is accurate in cases where the component is used as both an input and an output.

- **As output:** Is passed, passes the data through unchanged.
- **As input:** Should return, messages list or dict containing messages.

 ```python
 def predict(
     value: typing.Any
 ) -> typing.Any:
     return value
 ```
 
