import argparse
import socket
import threading


class Client(object):
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

    def send_message(self):
        while True:
            self.sock.send(input().encode('utf-8'))

    def receive_message(self):
        while True:
            data = self.sock.recv(1024).decode('utf-8')
            if not data:
                break
            print(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='', type=str)
    parser.add_argument('--port', default=10000, type=int)
    args = parser.parse_args()

    try:
        client = Client(args.host, args.port)
        threads = [threading.Thread(target=client.send_message, daemon=True),
                   threading.Thread(target=client.receive_message, daemon=True)]
        [thread.start() for thread in threads]
        [thread.join() for thread in threads]
    except KeyboardInterrupt:
        pass
