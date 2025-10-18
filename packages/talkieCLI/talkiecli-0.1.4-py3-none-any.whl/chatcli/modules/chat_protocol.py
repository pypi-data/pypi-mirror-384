import json

# -- color giving pkgs --

import colorama
from colorama import Fore, Back, Style, init

HOST_SERVER_NAME = "server"

init(autoreset=True)

def decode_message(data: bytes) -> dict:
    """Decodes raw bytes into a Python dictionary message."""
    return json.loads(data.decode())

def encode_message(msg_dict: dict) -> bytes:
    """Encodes a Python dictionary message into raw bytes."""
    return json.dumps(msg_dict).encode()

def create_server_message(color, message_text: str) -> dict:
    """Helper to create a standard server message."""
    return {"user": HOST_SERVER_NAME, "message": message_text, "color" : color}

def handle_incoming_message(
    msg: dict, 
    writer, 
    client_list: dict, 
    username: str,
    color: str
) -> tuple[bool, dict | list[tuple]]:
    """
    Processes a decoded message, handling commands or preparing for broadcast.

    Returns: 
        (should_exit: bool, response: dict or broadcast_list: list[tuple])
    """
    message_text = msg.get("message", "")

    chat_color = getattr(Fore, color.upper())
    
    if message_text == "/exit":
        return True, {}

    if message_text == "/list":
        # Command for a single client response
        user_list = ", ".join(client_list.values())
        reply = create_server_message(color, f"Online: {user_list}")
        print(username + " made a request to list online users")
        # print(reply)
        # Return a single response dict
        return False, reply 
    
    if message_text == "/ban":
        pass

    # Default: Message to be broadcast
    print(chat_color + username, " : ", message_text)
    broadcast_list = []
    
    # Prepare list of (writer, encoded_message) for broadcasting
    encoded_msg = encode_message(msg)
    for client_writer in list(client_list.keys()):
        if client_writer != writer:
            broadcast_list.append((client_writer, encoded_msg))
            
    # Return the list of (writer, data) tuples to send
    return False, broadcast_list
