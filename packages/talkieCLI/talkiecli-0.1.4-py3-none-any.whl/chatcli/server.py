import asyncio
import argparse
from chatcli.modules.connection_handler import handle_client

# -- color giving pkgs --

import colorama
from colorama import Fore, Back, Style, init

# --- Configuration and State ---
# HOST = "0.0.0.0"
# PORT = 65431
# Global state for connected clients
client_list = {} 
# client_list: {writer_object: username_string}

init(autoreset=True)

async def start_server(host, port):
    """
    Main function to start the asyncio server.
    """
    # Use a lambda to pass the global client_list to the handler function
    server_handler = lambda r, w: handle_client(r, w, client_list)
    
    server = await asyncio.start_server(server_handler, host, port)
    print(Fore.YELLOW + f"Server is listening on {host}:{port}")
    
    async with server:
        await server.serve_forever()

def main():  

    parser = argparse.ArgumentParser(description="Start an asyncio chat server.")
    parser.add_argument("--host", default="0.0.0.0", help="The host to bind the server to.")
    parser.add_argument("--port", type=int, default=65431, help="The port to listen on.")
    args = parser.parse_args()

    try:
        asyncio.run(start_server(args.host, args.port))
    except KeyboardInterrupt:
        print(Fore.RED + "\nServer shutting down.")


if __name__ == "__main__":
    main()