# import socket
import json
import asyncio
import argparse

# -- color giving pkgs --

import colorama
from colorama import Fore, Back, Style, init

init(autoreset=True)

client_list = {}  # writer -> username

async def tcp_client(host, port, color):
    reader, writer = await asyncio.open_connection (host, port)

    username = input(Back.BLACK + Fore.YELLOW + "Login with a username :" + Style.RESET_ALL + " ")
    print("ready to chat\n")

    login_msg = {"type" : "login", "user": username, "color" : color}
    writer.write(json.dumps(login_msg).encode())
    await writer.drain()

    async def listen():
        while True:
            data = await reader.read(1024)
            if not data:
                break
            try:
                msg = json.loads(data.decode())
                chat_color = getattr(Fore, msg["color"].upper())
                # print(msg)
                print(chat_color + f"\n{msg['user']} ", ":" ,f" {msg['message']}")
            except Exception as e:
                print("Error reading message:", e)

    asyncio.create_task(listen())

    while True:
        msg_text = await asyncio.to_thread(input, "")
        msg_dict = {"message" : msg_text, "user" : username, "type" : "text", "color" : color}
        writer.write(json.dumps(msg_dict).encode())
        await writer.drain()

        if msg_text == "/exit":
            print(Fore.RED + "Exiting the chat...")
            break
    writer.close()
    await writer.wait_closed()

def main():  # synchronous entry point for pyproject.toml

    parser = argparse.ArgumentParser(description="Start an asyncio chat client.")
    parser.add_argument("--host", default="0.0.0.0", help="The host to bind the client to.")
    parser.add_argument("--port", type=int, default=65431, help="The port that server is running on.")
    parser.add_argument("--color", default="WHITE", help="The color you want to use for your chats.")
    args = parser.parse_args()

    asyncio.run(tcp_client(args.host, args.port, args.color))

if __name__ == "__main__":
    main()
