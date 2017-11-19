import string
import sys
import random
import socket
import logging
import json
import time


class Node:
    # Socket for Message-Receiving
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Socket for Message-Sending
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    observerID = 0              # Fix ID for the Network-Observer
    observerIP = "127.0.0.1"    # Fix IP for the Network-Observer
    observerPort = 5001         # Fix Port of the Network-Observer

    onlineNodes = []            # List of all online Nodes
    neighborNodes = []          # List of Neighbor Nodes

    id = -1                     # ID of the Node
    ip = -1                     # IP of the Node
    port = -1                   # Port-Number of the Node

    isInitiator = False         # True, if node is Initiator

    # ____________________________ BEGIN: init & del _________________________________________________________________
    def __init__(self, node_id):
        self.id = node_id
        self.set_owen_params()

    def __del__(self):
        self.listen_socket.close()
    # ____________________________ END: init & del ___________________________________________________________________

    # ____________________________ BEGIN: get and set Node IDs, IPs & Ports __________________________________________
    @staticmethod
    def get_params(searched_id):
        config_file = open('config', 'r')
        not_found = True
        print searched_id

        while not_found:
            current_entry = config_file.readline()

            if current_entry == "":
                print "Error: Cannot find Port for the ID " + str(searched_id)
                return "-1"
            else:
                blank_pos = string.find(current_entry, " ")
                colon_pos = string.find(current_entry, ":")

                ce_id = current_entry[0:blank_pos]
                ce_ip = current_entry[blank_pos + 1:colon_pos]
                ce_port = current_entry[colon_pos + 1:len(current_entry) - 1]

                if searched_id == ce_id:
                    ip = ce_ip
                    port = ce_port
                    return {'id': searched_id, 'ip': ip, 'port': port}

    def get_online_params(self, searched_id):
        for i in range(len(self.onlineNodes)):
            current_node = self.onlineNodes[i]
            if searched_id == current_node[0]:
                return {'id': current_node[0], 'ip': current_node[1], 'port': current_node[2]}
        return "-1"

    def set_owen_params(self):
        found_params = self.get_params(self.id)
        self.ip = found_params['ip']
        self.port = found_params['port']
    # ____________________________ END: get and set Node IDs, IPs & Ports ____________________________________________

    # ____________________________ BEGIN: Network-Generation _________________________________________________________
    def generate_random_network(self):
        payload = ""
        while len(self.neighborNodes) < 3:
            possible_node = self.onlineNodes[random.randint(0, len(self.onlineNodes) - 1)]
            if not self.is_in_neighbour_list(possible_node):
                self.neighborNodes.append(possible_node)
                payload += self.id + "," + self.ip + "," + self.port
                self.send_msg(possible_node[1], possible_node[2], "newNeighbour", payload)
        self.send_msg(self.observerIP, self.observerPort, "findNeighboursAck", "")

    def generate_network_by_graph(self, graph_file):
        graph = open(graph_file, 'r')
        graph_neighbours = []
        not_finished = True

        while not_finished:
            current_entry = graph.readline()
            if current_entry == "":
                not_finished = False
            elif current_entry.startswith(str(self.id)):
                graph_neighbours.append(current_entry[current_entry.rindex(' ') + 1:current_entry.rindex(';')])

        for i in graph_neighbours:
            self.neighborNodes.append(self.get_params(graph_neighbours[i]))
    # ____________________________ END: Network-Generation ___________________________________________________________

    # ____________________________ BEGIN: Network-Graph-Generation ___________________________________________________
    def network_graph_feedback(self):
        neighbour_str = ""
        for i in range(len(self.neighborNodes)):
            neighbour_str += self.neighborNodes[i][0] + ";"
        neighbour_str = neighbour_str[:-1]
        time.sleep(0.5)
        self.send_msg(self.observerIP, self.observerPort, "genGraphAck", neighbour_str)
    # ____________________________ END: Network-Graph-Generation _____________________________________________________

    # ____________________________ BEGIN: Node-Management-Functions __________________________________________________
    def is_in_neighbour_list(self, searched_node):
        for i in range(len(self.neighborNodes)):
            current_node = self.neighborNodes[i]
            if current_node[0] == searched_node[0]:
                return 1
        return 0

    def set_online_nodes(self, node_list_str):
        node_list = str(node_list_str).split(";")
        for i in range(len(node_list)):
            node = str(node_list[i]).split(",")
            if node[0] != str(self.id):
                self.onlineNodes.append((node[0], node[1], node[2]))
        return
    # ____________________________ END: Node-Management-Functions ____________________________________________________

    # ____________________________ BEGIN: Send-Functions _____________________________________________________________
    def send_msg(self, receiver_ip, receiver_port, cmd, payload):
        json_msg = json.dumps({'sID': str(self.id), 'time': str(time.strftime("%d-%m-%Y %H:%M:%S",
                                                                              time.gmtime())), 'cmd': str(cmd),
                               'payload': str(payload)})
        self.send_socket.sendto(json_msg, (receiver_ip, int(receiver_port)))

    def send_to_neighbours(self, cmd, payload):
        for i in range(len(self.neighborNodes)):
            current_neighbour = self.neighborNodes[i]
            self.send_msg(current_neighbour[1], current_neighbour[2], cmd, payload)
    # ____________________________ END: Send-Functions _______________________________________________________________

    # ____________________________ BEGIN: Message-Handling ___________________________________________________________
    # Message print
    @staticmethod
    def print_msg(msg):
        json_msg = json.loads(msg)
        print ""
        print "____ Message ____"
        print "from: " + str(json_msg["sID"])
        print "received time: " + str(json_msg["time"])
        print "command: " + str(json_msg["cmd"])
        print "payload: " + str(json_msg["payload"])
        print ""

    # Handling of received Messages
    def msg_handling(self, msg):
        json_msg = json.loads(msg)

        command = str(json_msg["cmd"])

        # Control-Msg
        if command == "end":
            self.stop()
        elif command == "setInit":
            self.isInitiator = True
        elif command == "rmInit":
            self.isInitiator = False
        elif command == "randNG":
            self.set_online_nodes(json_msg["payload"])
            self.generate_random_network()
        elif command == "graphNG":
            self.generate_network_by_graph(json_msg["payload"])
        # Network-Msg
        elif command == "nID":
            self.neighborNodes.append(self.get_params(json_msg["payload"]))
        elif command == "genGraph":
            self.network_graph_feedback()
        elif command == "newNeighbour":
            new_neighbour = str(json_msg["payload"]).split(",")
            self.neighborNodes.append((new_neighbour[0], new_neighbour[1], new_neighbour[2]))
        # Other-Msg
        elif command == "msg":
            return
    # ____________________________ END: Message-Handling _____________________________________________________________

    # ____________________________ BEGIN: RUN & Stop _________________________________________________________________
    def stop(self):
        self.listen_socket.close()
        sys.exit(0)

    def run(self):
        self.listen_socket.bind((self.ip, int(self.port)))
        print "Node: " + str(self.id) + " listens on Socket: " + str(self.port)
        while True:
            msg, addr = self.listen_socket.recvfrom(1024)  # Buffer-Size set to 1024 bytes
            self.print_msg(msg)
            self.msg_handling(msg)
    # ____________________________ END: RUN & Stop ___________________________________________________________________


def main(argv):
    if len(argv) == 1:
        print "To start Node, ID is required"
        sys.exit(1)
    try:
        node = Node(argv[1])
        node.run()
    except Exception as e:
        logging.basicConfig(filename='node.log', level=logging.DEBUG)
        logging.critical(str(type(e)) + " : " + str(e.args))
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv)
