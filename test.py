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
    
    async def _send_notification(self, name, params):
        await self.__call__(name, params, use_id=False)
    
    async def install_game(self, game_id):
        await self._send_notification('install_game', {'game_id': game_id})

    async def launch_game(self, game_id):
        await self._send_notification('launch_game', {'game_id': game_id})

    async def uninstall_game(self, game_id):
        await self._send_notification('uninstall_game', {'game_id': game_id})

    async def __call__(self, method, params=None, use_id=True):
        print(f'calling {method} {params}')
        msg = {
            "jsonrpc": "2.0",
            "method": method
        }
        if use_id:
            self._id += 1
            msg['id'] = self._id
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
        # await caller('import_owned_games')
        # await caller('import_local_games')
        await caller.install_game("annasquest_trove")
        # await caller.launch_game("annasquest_trove")
        # await caller.uninstall_game("annasquest_trove")

    async def start_test():
        await asyncio.start_server(run_server_connection, "127.0.0.1", "7994")

    loop = asyncio.get_event_loop()
    loop.create_task(start_test())
    loop.run_forever()
