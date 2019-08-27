import json
import os
from pathlib import Path
import asyncio


CREDENTIALS_FILE = "credentials.data"


if __name__ == "__main__":

    async def run_server_connection(reader, writer):

        credentials = ""
        path = Path(CREDENTIALS_FILE)
        if not path.exists():
            path.touch()

        with open(CREDENTIALS_FILE, "r") as f:
            data = f.read()
            if data:
                credentials = json.loads(data)
            else:
                credentials = None

        credentials_rpc = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "3",
                "method": "init_authentication",
                "params": {"stored_credentials": credentials},
            }
        ).encode()

        print('running_browser')
        writer.write(credentials_rpc + b"\n")
        await writer.drain()
        tokens = await reader.readline()
        print("ret", tokens)

        tokens = json.loads(tokens.decode())
        try:
            if 'method' in tokens and tokens['method'] == 'store_credentials':
                print(f'overwriting {CREDENTIALS_FILE}')
                with open(CREDENTIALS_FILE, 'w') as f:
                    f.write(json.dumps(tokens['params']))

                print("tokens", tokens)
                ret = await reader.readline()
                print("ret", ret)
        except Exception as e:
            print(f'{str(e)}.\n Probably you need refresh it?')


        print("owned")
        writer.write(b'{"jsonrpc": "2.0", "id": "3", "method": "import_owned_games"}\n')
        await writer.drain()
        ret = await reader.readline()
        print("ret", ret)

        # print("local")
        # writer.write(b'{"jsonrpc": "2.0", "id": "4", "method": "import_local_games"}\n')
        # await writer.drain()
        # ret = await reader.readline()
        # print("ret", ret)

        print("install_game")
        writer.write(b'{"jsonrpc": "2.0", "method": "install_game", "params":{"game_id": "machinarium_steam"}}\n')

        # print("launch_game")
        # writer.write(b'{"jsonrpc": "2.0", "method": "launch_game", "params":{"game_id": "annasquest_trove"}}\n')

        # print("uninstall_game")
        # writer.write(b'{"jsonrpc": "2.0", "method": "uninstall_game", "params":{"game_id": "annasquest_trove"}}\n')

    async def wakeup():
        while True:
            await asyncio.sleep(1)

    async def start_test():
        await asyncio.start_server(run_server_connection, "127.0.0.1", "7994")

    loop = asyncio.get_event_loop()
    loop.create_task(start_test())
    loop.create_task(wakeup())
    loop.run_forever()
