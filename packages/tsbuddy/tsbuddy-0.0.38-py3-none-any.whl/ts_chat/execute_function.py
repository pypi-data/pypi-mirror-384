# execute_function.py

import sys
import ast
import os
from available_functions import FUNCTION_MAPPING


def parse_function_call(call_str):
    """
    Parses a function call string like 'set_timer(600, "check the oven")' or 'get_weather'.
    Returns (function_name, args, kwargs)
    """
    try:
        # Try to parse as an expression
        expr = ast.parse(call_str, mode='eval').body
        if isinstance(expr, ast.Call):
            func_name = expr.func.id
            args = [ast.literal_eval(arg) for arg in expr.args]
            kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in expr.keywords}
            return func_name, args, kwargs
        elif isinstance(expr, ast.Name):
            return expr.id, [], {}
        else:
            return call_str, [], {}
    except Exception:
        # Fallback: treat as just a function name
        return call_str, [], {}

def main():
    """
    Executes a function based on the command-line argument, with parameters if provided.
    """
    # Change working directory to script's directory for relative file access
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    if len(sys.argv) < 2:
        print("Usage: python execute_function.py <function_name>[params]")
        return

    call_str = sys.argv[1]
    # If the function call is passed as multiple args (e.g., with spaces), join them
    if len(sys.argv) > 2:
        call_str = ' '.join(sys.argv[1:])

    function_name, args, kwargs = parse_function_call(call_str)
    function_to_call = FUNCTION_MAPPING.get(function_name)

    if function_to_call:
        print(f"⚙️  Executing {function_name} with args={args} kwargs={kwargs}...")
        try:
            function_to_call(*args, **kwargs)
        except Exception as e:
            print(f"❌ Error executing function: {e}")
    else:
        print(f"❌ Error: Function '{function_name}' not found.")
        FUNCTION_MAPPING["unknown_request"]()

if __name__ == "__main__":
    main()