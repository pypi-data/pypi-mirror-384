import ast
import datetime
import os
import re
import shutil
import sys

# --- Core Configuration ---
LIBRARY_VERSION = "0.1.0"
LOG_FILE = "win32interfaces_log.txt"

def add_to_log(message):
    """Appends a timestamped message to the log file and prints a summary to the console."""
    # Log the full, detailed message to the file
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(force_safepath(LOG_FILE), 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

    # Print a user-friendly part of the message to the console
    parts = message.split(':', 1)
    if len(parts) > 1:
        # If there's a colon, print the part after it
        print(parts[1].strip())
    else:
        # Otherwise, just print the whole message
        print(message)

def invoke_exception(exception_message):
    """Logs an error message and then raises an exception to halt execution."""
    # The "CRITICAL ERROR" prefix is for the log file; the part after the colon is for the console.
    add_to_log(f"CRITICAL ERROR: {exception_message}")
    raise Exception(exception_message)

