import argparse
import asyncio
import logging
import sys

logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)s %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger('client')
logger.setLevel(logging.DEBUG)


class AutocompleteClientProtocol(asyncio.Protocol):
    loop = None
    queue = None
    transport = None

    def __init__(self, event_loop):
        self.loop: asyncio.AbstractEventLoop = event_loop
        task = self.loop.create_task(self.prompt_loop())
        asyncio.ensure_future(task)

    def connection_made(self, transport: asyncio.Transport):
        self.transport: asyncio.Transport = transport
        logger.debug('Connected to server at {}:{}'.format(*self.transport.get_extra_info('peername')))

    def data_received(self, data: bytes):
        print(data.decode())

    def connection_lost(self, exc):
        self.transport.close()

    async def prompt_loop(self):
        reader = asyncio.StreamReader(loop=self.loop)
        reader_protocol = asyncio.StreamReaderProtocol(stream_reader=reader, loop=self.loop)
        await self.loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)
        while True:
            try:
                cmd = await reader.readline()
            except KeyboardInterrupt:
                break
            else:
                self.transport.write(cmd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0', type=str)
    parser.add_argument('--port', default=10000, type=int)
    args = parser.parse_args()

    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)

    coro = loop.create_connection(
        protocol_factory=lambda: AutocompleteClientProtocol(loop),
        host=args.host, port=args.port
    )
    loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    loop.close()
