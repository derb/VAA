import sys
import logging
import socket
import json
import thread
from SendMsg import SendMsg


class NetworkObserver:
    # Socket for Message-Receiving
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    id = 0                      # Fix ID for the Network-Observer
    observerIP = "127.0.0.1"    # Fix IP for the Network-Observer
    port = 5001                 # Fix Port of the Network-Observer

    onlineNodes = []            # List of all online Nodes

    def __init__(self):
        pass

    def run(self):
        self.listen_socket.bind((self.ip, int(self.port)))
        print "Observer: " + str(self.id) + " listens on Socket: " + str(self.port)
        while True:
            msg, addr = self.listen_socket.recvfrom(1024)  # Buffer-Size set to 1024 bytes
            thread.start_new_thread(self.handle_msg(msg))

    def handle_msg(self, msg):
        print str(msg)


def main(argv):
    if len(argv) == 1:
        print "To start Node, ID is required"
        sys.exit(1)
    try:
        observer = NetworkObserver()
        thread.start_new_thread(observer.run(), ())
    except Exception as e:
        logging.basicConfig(filename='network_observer.log', level=logging.DEBUG)
        logging.critical(str(type(e)) + " : " + str(e.args))
    while True:
        inputStr = raw_input("Command: ")


if __name__ == "__main__":
    main(sys.argv)
