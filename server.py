import argparse
import asyncio
import logging
import re
import sys
import typing
from functools import lru_cache

logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)s %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger('server')
logger.setLevel(logging.DEBUG)

WordFrequency = typing.NamedTuple('WordFrequency', [('word', str), ('frequency', int)])


class CommandParseError(Exception):
    def __init__(self, message):
        self.message: str = message


class SuggestionsNotFoundError(Exception):
    def __init__(self, message):
        self.message: str = message


class AutocompleteServerProtocol(asyncio.Protocol):
    transport: asyncio.Transport = None

    def __init__(self, word_freq_file_path: str):
        self.word_freq_set = self.get_word_freq_set_from_txt(path=word_freq_file_path)

    def connection_made(self, transport):
        self.transport: asyncio.Transport = transport
        logger.debug('Connected {}:{}'.format(*self.transport.get_extra_info('peername')))
        self.write('This is autocomplete service.\n'
                   'Service accepts commands, which\n'
                   'matches \'get <prefix>\' pattern')

    def data_received(self, data: bytes):
        logger.debug('Data received: {}'.format(data.decode()))
        try:
            command, prefix = self.parse_command(data)
        except CommandParseError as error:
            self.write(error.message)
        except:
            self.write('Something gone wrong, please try again')
        else:
            try:
                suggestions = self.get_suggestions(prefix)
            except SuggestionsNotFoundError as error:
                self.write(error.message)
            else:
                self.write(suggestions)
        logger.debug('Cache info: {}'.format(self._get_suggestions.cache_info()))

    def connection_lost(self, exc):
        logger.debug('Disconnected {}:{}'.format(*self.transport.get_extra_info('peername')))
        self.transport.close()

    def write(self, message: str):
        end = '' if message.endswith('\n') else '\n'
        self.transport.write(f'{message}{end}'.encode())

    @staticmethod
    def parse_command(data: bytes) -> typing.Tuple[str, str]:
        pattern = r'^(get) ([a-zA-Z]{1,15})$'
        data = data.decode().strip()
        match = re.match(pattern, data, re.IGNORECASE)
        if not match:
            raise CommandParseError('Command should match patter \'get <prefix:str>\'')
        return match.group(1, 2)

    @staticmethod
    @lru_cache()
    def _get_suggestions(prefix: str, word_freq_set: typing.FrozenSet[WordFrequency]):
        _filter = filter(lambda i: i.word.startswith(prefix), word_freq_set)
        _sorted = sorted(_filter, key=lambda i: (-i.frequency, i.word))
        return _sorted[:10]

    def get_suggestions(self, prefix: str) -> str:
        suggestions = self._get_suggestions(prefix, self.word_freq_set)
        if len(suggestions) < 1:
            raise SuggestionsNotFoundError('Suggestions not found')
        return '\n'.join(f'-> {item.word}' for item in suggestions)

    @staticmethod
    def get_word_freq_from_line(line: str) -> WordFrequency:
        word, freq, *_ = line.split(' ')
        freq = int(freq)
        return WordFrequency(word, freq)

    def get_word_freq_set_from_txt(self, path: str) -> typing.FrozenSet[WordFrequency]:
        result = set()
        with open(path, 'r') as f:
            [result.add(self.get_word_freq_from_line(line))
             for line in f.readlines()]
        return frozenset(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', default='word_freq.txt', type=str)
    parser.add_argument('--port', default=10000, type=int)
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    # loop.set_debug(enabled=True)

    coro = loop.create_server(
        protocol_factory=lambda: AutocompleteServerProtocol(word_freq_file_path=args.filename),
        host='0.0.0.0', port=args.port
    )
    server = loop.run_until_complete(coro)

    for socket in server.sockets:
        logger.debug('Server running {}:{}'.format(*socket.getsockname()))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.run_until_complete(server.wait_closed())

    loop.close()
