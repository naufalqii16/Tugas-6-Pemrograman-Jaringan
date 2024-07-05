from socket import *
import socket
import threading
import json
import logging
import sys
sys.path.append('../')
from chat import Chat

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address, chatserver, server_id):
        self.connection = connection
        self.address = address
        self.chatserver = chatserver
        self.server_id = server_id
        threading.Thread.__init__(self)

    def run(self):
        rcv = ""
        while True:
            data = self.connection.recv(10000)
            if data:
                d = data.decode()
                rcv = rcv+d
                if rcv[-2:] == '\r\n':
                    # end of command, proses string
                    logging.warning("data dari client: {}" . format(rcv))
                    hasil = self.chatserver.proses(rcv, self.server_id)
                    hasil = hasil+"\r\n\r\n"
                    logging.warning("balas ke  client: {}" . format(hasil))
                    self.connection.sendall(hasil.encode())
                    rcv = ""
            else:
                break
        self.connection.close()


class Server(threading.Thread):
    def __init__(self):
        self.the_clients = []
        self.chatserver = Chat()
        self.server_id = self.chatserver.get_realm_id()
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        self.my_socket.bind(('localhost', 9010))
        self.my_socket.listen(1)
        while True:
            self.connection, self.client_address = self.my_socket.accept()
            logging.warning("connection from {}" . format(self.client_address))

            clt = ProcessTheClient(self.connection, self.client_address, self.chatserver, self.server_id)
            clt.start()
            self.the_clients.append(clt)


def main():
    svr = Server()
    svr.start()
    logging.warning(' REALM1: running server on port 9010')


if __name__ == "__main__":
    main()
