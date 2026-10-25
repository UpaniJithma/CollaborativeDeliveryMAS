import asyncio

from pyjabber.server import Server
from pyjabber.server_parameters import Parameters


async def main():
    parameters = Parameters(
        host="localhost",
        client_port=5222,
        server_port=5269,
        database_path="pyjabber.db",
        database_in_memory=True,
        verbose=True,
    )

    server = Server(parameters)

    print("Starting local PyJabber XMPP server...")
    print("Client address: 127.0.0.1:5222")

    try:
        await server.start()
    except KeyboardInterrupt:
        print("Stopping PyJabber server...")


if __name__ == "__main__":
    asyncio.run(main())
