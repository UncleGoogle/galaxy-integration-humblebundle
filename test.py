import json
import os
from pathlib import Path
import asyncio


CREDENTIALS_FILE = "credentials.data"

class RpcChannel:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self._id = 0

    async def __call__(self, method, params=None):
        print(f'calling {method} {params}')
        msg = {
            "jsonrpc": "2.0",
            "id": "3",
            "method": method
        }
        if params is not None:
            msg['params'] = params

        encoded = json.dumps(msg).encode() + b"\n"
        self.writer.write(encoded)
        await self.writer.drain()
        response = await self.reader.readline()
        print("ret", response)
        return response


if __name__ == "__main__":

    async def run_server_connection(reader, writer):

        caller = RpcChannel(reader, writer)

        path = Path(CREDENTIALS_FILE)
        if not path.exists():
            path.touch()

        with open(CREDENTIALS_FILE, "r") as f:
            data = f.read()
            if data:
                credentials = json.loads(data)
            else:
                raise RuntimeError('No credentials found')

        await caller('initialize_cache', {"data": {}})
        await caller('init_authentication', {"stored_credentials": credentials})
        await caller('import_owned_games')
        await caller('import_local_games')
        # await caller('install_game')
        # await caller('launch_game', {"game_id": "annasquest_trove"})
        # await caller('uninstall_game' {"game_id": "annasquest_trove"})

    async def start_test():
        await asyncio.start_server(run_server_connection, "127.0.0.1", "7994")

    loop = asyncio.get_event_loop()
    loop.create_task(start_test())
    loop.run_forever()
