import asyncio
import json
from .chat_protocol import decode_message, encode_message, handle_incoming_message

# -- color giving pkgs --

import colorama
from colorama import Fore, Back, Style, init

init(autoreset=True)

async def handle_client(reader, writer, client_list: dict):
    """
    Core coroutine to handle a single client connection lifecycle.
    """
    addr = writer.get_extra_info('peername')
    username = None
    # print(f"{addr} connected")

    try:
        # --- 1. Login Phase ---
        login_data = await reader.read(1024)
        if not login_data:
            return

        login_msg = decode_message(login_data)
        # Safely assign username
        username = login_msg.get("user", f"user{len(client_list) + 1}")
        client_list[writer] = username
        chat_color = getattr(Fore, login_msg["color"].upper())
        print(chat_color + f"{username} logged in")

        # --- 2. Main Message Loop ---
        while True:
            data = await reader.read(1024)
            if not data:
                break
            
            msg = decode_message(data)
            
            # Delegate command/message handling to the protocol module
            should_exit, response_or_broadcast = handle_incoming_message(
                msg, writer, client_list, username, login_msg["color"]
            )

            if should_exit:
                print(f"{username} left the chat")
                break
                
            if isinstance(response_or_broadcast, dict):
                # This is a single client response (e.g., /list command)
                writer.write(encode_message(response_or_broadcast))
                await writer.drain()
            elif isinstance(response_or_broadcast, list):
                # This is a broadcast list
                for client_writer, encoded_msg in response_or_broadcast:
                    client_writer.write(encoded_msg)
                    await client_writer.drain()

    except Exception as e:
        print(f"Error with {addr} : {e}")
    
    finally:
        # --- 3. Cleanup Phase ---
        if writer in client_list:
            del client_list[writer]
        writer.close()
        await writer.wait_closed()
