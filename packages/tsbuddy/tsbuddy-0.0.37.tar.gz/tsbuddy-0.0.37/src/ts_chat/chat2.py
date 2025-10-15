from openai import OpenAI
import json
import os

from src.tsbuddy import main as tsbuddy_main
from src.extracttar.extract_all import main as extract_all_main
from src.aosdl.aosdl import main as aosdl_main, lookup_ga_build, aosup
from src.logparser import main as logparser_main
from src.get_techsupport import main as get_techsupport_main
#from src.analyze.graph_hmon import main as graph_hmon_main

ENV_FILE = os.path.join(os.path.expanduser("~"), ".tsbuddy_secrets")

def load_env_file():
    """Load key-value pairs from .env into os.environ"""
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, sep, value = line.strip().partition("=")
                    if sep:  # Only set if '=' was found
                        os.environ.setdefault(key, value)

def append_to_env_file(key, value):
    """Append a new key=value to .env"""
    with open(ENV_FILE, "a") as f:
        f.write(f"{key}={value}\n")

# Load .env into environment
load_env_file()

# Prompt if API key not set
if "OPENAI_API_KEY" not in os.environ:
    api_key = input("Enter your OpenAI API key: ").strip()
    os.environ["OPENAI_API_KEY"] = api_key
    append_to_env_file("OPENAI_API_KEY", api_key)

# Use the key
# openai.api_key = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# Define your function wrappers
def function_router(name, args=None):
    print(f"Calling function: {name}")
    if name == "lookup_ga_build":
        return lookup_ga_build()
    elif name == "get_techsupport_main":
        return get_techsupport_main()
    elif name == "extract_all_main":
        return extract_all_main()
    elif name == "tsbuddy_main":
        return tsbuddy_main()
    elif name == "logparser_main":
        return logparser_main()
    elif name == "aosup":
        return aosup()
    elif name == "aosdl_main":
        return aosdl_main()
    elif name == "graph_hmon_main":
        return graph_hmon_main()
    elif name == "change_directory":
        return change_directory()
    elif name == "upgrade_downgrade_choice":
        return upgrade_downgrade_choice()
    elif name == "print_help":
        return print_help()
    else:
        return "Unknown function."

# Register functions for OpenAI API
functions = [
    {
        "name": "lookup_ga_build",
        "description": "Get GA Build, Family, or Upgrade (aosga)",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_techsupport_main",
        "description": "Run tech support gatherer (ts-get)",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "extract_all_main",
        "description": "Run tech_support_complete.tar extractor (ts-extract)",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "tsbuddy_main",
        "description": "Run tech_support.log to CSV converter (ts-csv)",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "logparser_main",
        "description": "Run swlog parser to CSV & JSON (ts-log)",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "aosup",
        "description": "Run AOS Upgrader (aosup)",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "aosdl_main",
        "description": "Run AOS Downloader (aosdl)",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "graph_hmon_main",
        "description": "Run HMON Graph tool (ts-graph-hmon)",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "change_directory",
        "description": "Change current working directory",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "upgrade_downgrade_choice",
        "description": "Upgrade or downgrade tsbuddy",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "print_help",
        "description": "Show help info",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }
]

# Main chatbot loop
def main():
    print("💬 Chatbot is ready. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            break

        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": user_input}],
            functions=functions,
            function_call="auto"
        )
        message = response.choices[0].message
        if message.function_call:
            fn_name = message.function_call.name
            args = json.loads(message.function_call.arguments or "{}")
            result = function_router(fn_name, args)
            print(f"🤖 Result: {result}")
        else:
            print("🤖", message["content"])

if __name__ == "__main__":
    main()
