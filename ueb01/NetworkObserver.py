import sys
import logging
import socket
import string
import json
import thread
import time


class NetworkObserver:
    # Socket for Message-Receiving
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Socket for Message-Sending
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    id = 0                      # Fix ID for the Network-Observer
    observerIP = "127.0.0.1"    # Fix IP for the Network-Observer
    port = 5001                 # Fix Port of the Network-Observer

    onlineNodes = []            # List of all online Nodes

    def __init__(self):
        self.get_online_nodes()

    def __del__(self):
        self.listen_socket.close()

    def get_online_nodes(self):
        config_file = open('config', 'r')
        current_entry = config_file.readline()

        while current_entry != "":
            current_entry = config_file.readline()

            blank_pos = string.find(current_entry, " ")
            colon_pos = string.find(current_entry, ":")

            ce_id = current_entry[0:blank_pos]
            ce_ip = current_entry[blank_pos + 1:colon_pos]
            ce_port = current_entry[colon_pos + 1:len(current_entry) - 1]

            if ce_id != "":
                self.onlineNodes.append((ce_id, ce_ip, ce_port))

    @staticmethod
    def print_commands():
        print "EXIT:                    0" + "\n" + \
              "List all Nodes:          1" + "\n" + \
              "End Node by ID:          2" + "\n" + \
              "End all Nodes:           3" + "\n" + \
              "Initiate random Network: 4" + "\n" + \
              "Get Network-Graph:       5"

    def listen(self):
        self.listen_socket.bind((self.observerIP, int(self.port)))
        print "Observer: " + str(self.id) + " listens on Socket: " + str(self.port)
        while True:
            msg, addr = self.listen_socket.recvfrom(1024)  # Buffer-Size set to 1024 bytes
            thread.start_new_thread(self.handle_msg(msg), ())

    def send_msg(self, receiver_ip, receiver_port, cmd, payload):
        json_msg = json.dumps({'sID': str(self.id), 'time': str(time.strftime("%d-%m-%Y %H:%M:%S",
                                                                              time.gmtime())), 'cmd': str(cmd),
                               'payload': str(payload)})
        self.send_socket.sendto(json_msg, (receiver_ip, int(receiver_port)))

    def handle_msg(self, msg):
        print str(msg)

    def run(self):
        while True:
            print self.print_commands()
            input_str = raw_input("Command: ")

            if input_str == "0":
                    sys.exit(0)
            elif input_str == "ls":
                print self.onlineNodes
            elif input_str == "listen":
                thread.start_new_thread(self.listen(), ())
            elif input_str == "fa":
                for i in range(len(self.onlineNodes)):
                    self.send_msg(self.onlineNodes[i][1], self.onlineNodes[i][2], "end", "")


def main(argv):
    if len(argv) > 1:
        print "To many arguments"
        sys.exit(1)
    try:
        observer = NetworkObserver()
        observer.run()
    except Exception as e:
        logging.basicConfig(filename='network_observer.log', level=logging.DEBUG)
        logging.critical(str(type(e)) + " : " + str(e.args))
        sys.exit(6)


if __name__ == "__main__":
    main(sys.argv)
