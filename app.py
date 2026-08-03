from openai import OpenAI
from context import TWIN_SYSTEM_PROMPT
from tools import tools, handle_tool_calls
from styles import CSS, JS, EXAMPLES
from dotenv import load_dotenv
import gradio as gr
import time
from collections import defaultdict

load_dotenv(override=True)

MODEL_NAME = "gpt-5.4-mini"

openai = OpenAI()

system = [{"role": "system", "content": TWIN_SYSTEM_PROMPT}]

# --- Rate limiting ---
MAX_MESSAGES = 10        
WINDOW_SECONDS = 3600

usage_log = defaultdict(list)

def is_rate_limited(ip):
    now = time.time()
    # remove old timestamps, outside window time
    usage_log[ip] = [t for t in usage_log[ip] if now - t < WINDOW_SECONDS]

    if len(usage_log[ip]) >= MAX_MESSAGES:
        return True

    usage_log[ip].append(now)
    return False


def chat(message, history, request: gr.Request):
    ip = request.client.host if request else "unknown"

    if is_rate_limited(ip):
        return "You have reach the maximum messages per day, try again later! 🙏"

    messages = system + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
    while response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        tool_calls = message.tool_calls
        results = handle_tool_calls(tool_calls)
        messages.append(message)
        messages.extend(results)
        response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
    return response.choices[0].message.content


if __name__ == "__main__":
    gr.ChatInterface(
        chat,
        examples=EXAMPLES,
        title="Digital Twin",
        description="Talk to my AI twin about my career",
        chatbot=gr.Chatbot(show_label=False),
    ).launch(css=CSS, js=JS, theme=gr.themes.Base())
