# Directory: app/utils/file_handler.py
import os
import json

CONN_FILE = os.path.expanduser("~/.data_profiler/connections.json")
os.makedirs(os.path.dirname(CONN_FILE), exist_ok=True)

def save_connection(name, conn_data):
    if os.path.exists(CONN_FILE):
        with open(CONN_FILE, 'r') as f:
            connections = json.load(f)
    else:
        connections = {}
    connections[name] = conn_data
    with open(CONN_FILE, 'w') as f:
        json.dump(connections, f, indent=2)

def load_connections():
    if os.path.exists(CONN_FILE):
        with open(CONN_FILE, 'r') as f:
            return json.load(f)
    return {}
