import argparse
import typing
from collections import namedtuple
from socketserver import ThreadingTCPServer, BaseRequestHandler

WordFrequency = namedtuple('WordFrequency', ['word', 'frequency'])


class Server(ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, request_handler_class, word_freq_file_path):
        super(Server, self).__init__(server_address, request_handler_class)
        self.word_freq_set = set()
        self.get_word_freq_set_from_txt(word_freq_file_path)

    def get_word_freq_set_from_txt(self, path):
        with open(path, 'r') as f:
            [self.word_freq_set.add(WordFrequency(*line.split(' ')[:2]))
             for line in f.readlines()]


class AutocompleteRequestHandler(BaseRequestHandler):
    def handle(self):
        while True:
            try:
                data = self.request.recv(1024).decode('utf-8').strip().lower()
                if data == '/quit':
                    break
                try:
                    command, prefix, *_ = data.split(' ')
                    if not command or command != 'get':
                        self.send_message('Command should be set and equal to \'get\'\n')
                        continue
                    if not prefix or 15 < len(prefix) <= 0:
                        self.send_message('Prefix is required. Its length should be in between 1 and 15 characters.\n')
                        continue

                    suggestions = self.get_suggestions(prefix)
                    if suggestions and len(suggestions) > 0:
                        self.send_message(self.prepare_suggestions_response(suggestions))
                        continue
                    else:
                        self.send_message('No suggestions.\n')

                except ValueError:
                    self.send_message('ValueError. Please, try again.\n')
                    continue
            except ConnectionError:
                break
            except UnicodeDecodeError:
                self.send_message('UnicodeDecodeError. Please, try again.\n')
                continue

        self.request.close()

    def send_message(self, message):
        self.request.send(message.encode('utf-8'))

    def get_suggestions(self, prefix: str):
        _filter = filter(lambda i: i.word.startswith(prefix.lower()), self.server.word_freq_set)
        _sorted = sorted(_filter, key=lambda i: (-int(i[1]), i[0]))
        return _sorted[:10]

    @staticmethod
    def prepare_suggestions_response(sugggestions: typing.List[WordFrequency]):
        return ''.join(['-> %s\n' % item.word for item in sugggestions])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', default='word_freq.txt', type=str)
    parser.add_argument('--port', default=10000, type=int)
    args = parser.parse_args()

    server = Server(('', args.port), AutocompleteRequestHandler, args.filename)
    try:
        print('Server running at {}:{}'.format(server.server_address[0], server.server_address[1]))
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        print('Server stopped')
