import sys
import logging
import socket
import string
import json
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

    currentNetworkGraph = ""    # Graph of current Network if requested

    # ____________________________ BEGIN: init & del _________________________________________________________________
    def __init__(self):
        self.get_online_nodes()

    def __del__(self):
        self.listen_socket.close()
    # ____________________________ END: init & del ___________________________________________________________________

    # ____________________________ BEGIN: Send- & Receive-Functions __________________________________________________
    def listen(self):
        self.listen_socket.bind((self.observerIP, int(self.port)))
        print "Observer: " + str(self.id) + " listens on Socket: " + str(self.port)
        while True:
            msg, addr = self.listen_socket.recvfrom(1024)  # Buffer-Size set to 1024 bytes
            break
        self.handle_msg(msg)

    def send_msg(self, receiver_ip, receiver_port, cmd, payload):
        json_msg = json.dumps({'sID': str(self.id), 'time': str(time.strftime("%d-%m-%Y %H:%M:%S",
                                                                              time.gmtime())), 'cmd': str(cmd),
                               'payload': str(payload)})
        self.send_socket.sendto(json_msg, (receiver_ip, int(receiver_port)))
    # ____________________________ END: Send- & Receive-Functions ____________________________________________________

    # ____________________________ BEGIN: Node-Management-Functions __________________________________________________
    def get_node_by_id(self, node_id):
        for i in range(len(self.onlineNodes)):
            if self.onlineNodes[i][0] == node_id:
                return self.onlineNodes[i]
            else:
                return "-1"

    def get_online_nodes(self):
        config_file = open('config', 'r')
        current_entry = config_file.readline()

        while current_entry != "":

            blank_pos = string.find(current_entry, " ")
            colon_pos = string.find(current_entry, ":")

            ce_id = current_entry[0:blank_pos]
            ce_ip = current_entry[blank_pos + 1:colon_pos]
            ce_port = current_entry[colon_pos + 1:len(current_entry) - 1]

            if ce_id != "":
                self.onlineNodes.append((ce_id, ce_ip, ce_port))
            current_entry = config_file.readline()
    # ____________________________ END: Node-Management-Functions ____________________________________________________

    # ____________________________ BEGIN: Logic ______________________________________________________________________
    def initiate_rand_network(self):
        payload = ""
        for i in range(len(self.onlineNodes)):
            current_node = self.onlineNodes[i]
            payload += str(current_node[0]) + "," + str(current_node[1]) + "," + str(current_node[2]) + ";"
        payload = payload[:-1]

        for i in range(len(self.onlineNodes)):
            current_node = self.onlineNodes[i]
            self.send_msg(current_node[1], current_node[2], "randNG", payload)
            time.sleep(2)

    def generate_graph_file(self, caller, callee_list):
        if self.currentNetworkGraph == "":
            self.currentNetworkGraph = "graph G {\n"
        else:
            self.currentNetworkGraph = self.currentNetworkGraph[:-1]

        callees = str(callee_list).split(";")
        for i in range(len(callees)):
            self.currentNetworkGraph += caller + " -- " + callees[i] + "\n"
        self.currentNetworkGraph += "}"

    def request_network_graph(self):
        for i in range(len(self.onlineNodes)):
            current_node = self.onlineNodes[i]
            self.send_msg(current_node[1], current_node[2], "genGraph", "")
            self.listen()
        print self.currentNetworkGraph
    # ____________________________ END: Logic ________________________________________________________________________

    # ____________________________ BEGIN: RUN & MSG-Handling _________________________________________________________
    def handle_msg(self, msg):
        json_msg = json.loads(msg)

        command = str(json_msg["cmd"])
        if command == "genGraphAck":
            self.generate_graph_file(json_msg["sID"], json_msg["payload"])

    @staticmethod
    def print_commands():
        print "EXIT:                    0" + "\n" + \
              "List all Nodes:          1" + "\n" + \
              "End Node by ID:          2" + "\n" + \
              "End all Nodes:           3" + "\n" + \
              "Initiate random Network: 4" + "\n" + \
              "Get Network-Graph:       5"

    def run(self):
        while True:
            print self.print_commands()
            input_str = raw_input("Command: ")

            if input_str == "0":
                    sys.exit(0)
            elif input_str == "1":
                print self.onlineNodes
            elif input_str == "2":
                node_id = raw_input("Node ID: ")
                node_to_stop = self.get_node_by_id(node_id)
                if node_to_stop == "-1":
                    print "Could not find Node by this ID"
                else:
                    self.send_msg(node_to_stop[1], node_to_stop[2], "end", "")
            elif input_str == "3":
                for i in range(len(self.onlineNodes)):
                    self.send_msg(self.onlineNodes[i][1], self.onlineNodes[i][2], "end", "")
            elif input_str == "4":
                self.initiate_rand_network()
            elif input_str == "5":
                self.request_network_graph()
            else:
                print "\nNo such command\n\n"
    # ____________________________ END: RUN &  MSG-Handling __________________________________________________________


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
