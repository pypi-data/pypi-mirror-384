# pyshare/network_utils.py

import json

def send_json(sock, data):
    """Sends JSON data over a socket."""
    json_data = json.dumps(data).encode('utf-8')
    sock.sendall(len(json_data).to_bytes(4, 'big'))
    sock.sendall(json_data)

def recv_json(sock):
    """Receives JSON data from a socket."""
    try:
        data_len = int.from_bytes(sock.recv(4), 'big')
        if not data_len:
            return None
        return json.loads(sock.recv(data_len))
    except (ConnectionResetError, OSError):
        return None