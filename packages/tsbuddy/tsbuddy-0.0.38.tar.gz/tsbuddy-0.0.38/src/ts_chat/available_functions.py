# available_functions.py

from src.tsbuddy_version import update_package_safe as update_package
from src.tsbuddy_version import choice_form as upgrade_downgrade_choice
from src.tsbuddy import main as tsbuddy_main
from src.extracttar.extract_all import main as extract_all_main
from src.aosdl.aosdl import main as aosdl_main, lookup_ga_build, aosup
from src.logparser import main as logparser_main
from src.get_techsupport import main as get_techsupport_main
#from src.analyze.graph_hmon import main as graph_hmon_main

def get_weather(location="a specified location"):
    """Simulates getting the weather for a location."""
    print(f"🌦️  Fetching weather for {location}...")

def set_timer(duration_seconds=60, message="your reminder"):
    """Simulates setting a timer."""
    print(f"⏲️  Setting a timer for {duration_seconds} seconds with message: '{message}'")

def send_email(recipient="test@example.com", subject="Hello", body="This is a test."):
    """Simulates sending an email."""
    print(f"📧  Sending email to {recipient} with subject '{subject}'...")

def lookup_stock_price(ticker_symbol="GOOGL"):
    """Simulates looking up a stock price."""
    print(f"📈  Looking up stock price for {ticker_symbol}...")

def unknown_request():
    """Handles requests that don't match any other function."""
    print("🤔  Sorry, I'm not sure how to handle that request.")

# def aos_downloader(folder_name=None, reload_when_finished=False, found_ga_build=None):
#     aosdl_main(folder_name=folder_name, reload_when_finished=reload_when_finished, found_ga_build=found_ga_build)
#     """
#     print("\nNote: you can lookup the GA build with aosdl-ga CLI command.\n")
#     if not found_ga_build:
#         aos_major, aos_build, aos_release = get_aos_version_simple()
#     else:
#         parts = found_ga_build.split('.')
#         aos_major, aos_build, aos_release = [".".join(parts[:2]), parts[2], parts[3]]
#     print(f"Using AOS Version: {aos_major}.{aos_build}.{aos_release}")
#     """
#     print(f"Running AOS Downloader...")

# This dictionary maps the string name of the function to the actual function object.
# It's essential for the execution script.
FUNCTION_MAPPING = {
    # Simulated/demo functions
    "get_weather": get_weather,
    "set_timer": set_timer,
    "send_email": send_email,
    "lookup_stock_price": lookup_stock_price,
    "unknown_request": unknown_request,
    # Real tsbuddy functions
    "lookup_ga_build": lookup_ga_build,
    "get_techsupport_main": get_techsupport_main,
    "extract_all_main": extract_all_main,
    "tsbuddy_main": tsbuddy_main,
    "logparser_main": logparser_main,
    "aosup": aosup,
    "aos_downloader": aosdl_main,
    #"graph_hmon_main": graph_hmon_main,
    "upgrade_downgrade_choice": upgrade_downgrade_choice,
    "update_package": update_package,
}