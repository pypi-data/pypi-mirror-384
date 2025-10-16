# main_api_caller.py

import os
import subprocess

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

import openai

# Initialize the OpenAI client
# It will automatically look for the OPENAI_API_KEY environment variable
try:
    client = openai.OpenAI()
except openai.APIError:
    print("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    exit()

def get_function_name_from_gpt(user_prompt: str, system_prompt: str) -> str:
    """
    Sends the user prompt and system prompt to the API and gets the function name.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-5-nano",  # Or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=1, # Set to 0 for deterministic, rule-based output
        )
        # The response from the API should be just the function name
        function_name = response.choices[0].message.content.strip()
        return function_name
    except Exception as e:
        print(f"An error occurred with the API call: {e}")
        return "unknown_request"

def main():
    # Load the prompt from the file (relative to this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(script_dir, "system_prompt.txt")
    try:
        with open(prompt_path, "r") as f:
            system_prompt_content = f.read()
    except FileNotFoundError:
        print(f"Error: {prompt_path} not found. Please create it.")
        exit()

    print("🤖 Hello! What can I help you with today? (Type 'exit' to quit)")

    # Main loop to interact with the user
    while True:
        user_input = input("> ")
        if user_input.lower() == 'exit':
            break

        print("🧠 Thinking...")
        
        # Get the chosen function name from the API
        chosen_function = get_function_name_from_gpt(user_input, system_prompt_content)
        
        print(f"✅ GPT decided to run: {chosen_function}")

        # Use subprocess to call the execution script with the function name
        # Note: We pass the original user input as well, in a real scenario
        # the executor might use it to parse arguments.
        execute_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "execute_function.py")
        subprocess.run(["python", execute_script, chosen_function])
        print("-" * 20)

if __name__ == "__main__":
    main()