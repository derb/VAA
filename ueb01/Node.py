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

    # ____________________________ BEGIN: rumor experiment ___________________________________________________________
    first_heard = "-1"          # ID of Node, rumor first heard from
    rumor_handled = False       # True if rumor already spread

    rumor = ""                  # Rumor

    c_value = -1                # Value of how often rumor must be received to be believed
    rumor_heard = 0             # Value of how often rumor has been heard
    believe_rumor = False       # True if rumor is believed

    def spread_rumor(self, rumor_msg):
        self.rumor_handled = True
        for i in range(len(self.neighborNodes)):
            send_to = self.neighborNodes[i]
            if send_to[0] != self.first_heard:
                self.send_msg(send_to[1], send_to[2], "spreadRumor", rumor_msg)

    def hear_rumor(self, sender_id, rumor_msg):
        if self.first_heard == "-1":
            self.first_heard = sender_id
            self.rumor = rumor_msg
            self.rumor_heard += 1
        else:
            if rumor_msg == self.rumor:
                self.rumor_heard += 1
        if not self.rumor_handled:
            self.spread_rumor(self.rumor)
        if self.rumor_heard >= self.c_value:
            self.believe_rumor = True

    def initiate_rumor_experiment(self, c):
        self.c_value = int(c)
        # start rumor if initiator
        if self.isInitiator:
            self.rumor = str(random.randint(1, 11))
            self.believe_rumor = True  # Initiator always believe rumor
            time.sleep(random.randint(1, 4) * 0.1)
            self.spread_rumor(self.rumor)

    def rumor_status_feedback(self):
        msg = "Rumor: " + self.rumor + " -> Rumor heard: " + str(self.rumor_heard) + " -> believe: " + \
              str(self.believe_rumor) + "  [is Initiator:  " + str(self.isInitiator) + "]"
        self.send_msg(self.observerIP, self.observerPort, "rumorStat", msg)

    def reset_rumor_experiment(self):
        self.first_heard = "-1"
        self.rumor_handled = False
        self.rumor = ""
        self.c_value = -1
        self.rumor_heard = 0
        self.believe_rumor = False
    # ____________________________ END: rumor experiment _____________________________________________________________

    # ____________________________ BEGIN: get and set Node IDs, IPs & Ports __________________________________________
    @staticmethod
    def get_params(searched_id):
        config_file = open('config', 'r')
        not_found = True

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
                    return searched_id, ip, port

    def get_online_params(self, searched_id):
        for i in range(len(self.onlineNodes)):
            current_node = self.onlineNodes[i]
            if searched_id == current_node[0]:
                return {'id': current_node[0], 'ip': current_node[1], 'port': current_node[2]}
        return "-1"

    def set_owen_params(self):
        found_params = self.get_params(self.id)
        self.ip = found_params[1]
        self.port = found_params[2]
    # ____________________________ END: get and set Node IDs, IPs & Ports ____________________________________________

    # ____________________________ BEGIN: Network-Generation _________________________________________________________
    def clear_current_network(self):
        if len(self.neighborNodes) > 0:
            self.neighborNodes = []

    def generate_random_network(self):
        self.clear_current_network()
        payload = ""
        while len(self.neighborNodes) < 3:
            possible_node = self.onlineNodes[random.randint(0, len(self.onlineNodes) - 1)]
            if not self.is_in_neighbour_list(possible_node):
                self.neighborNodes.append(possible_node)
                payload += self.id + "," + self.ip + "," + self.port
                self.send_msg(possible_node[1], possible_node[2], "newNeighbour", payload)
        self.send_msg(self.observerIP, self.observerPort, "findNeighboursAck", "")

    def generate_network_by_graph(self, graph_file):
        self.clear_current_network()
        try:
            graph = open(graph_file, 'r')
            graph_neighbours = []
            finished = False

            while not finished:
                current_entry = graph.readline()
                if current_entry.startswith("}"):
                    finished = True
                else:
                    if not current_entry.startswith("graph"):
                        caller_callee = current_entry.split(" -- ")
                        caller_callee[1] = caller_callee[1].rstrip(';\n')
                        if caller_callee[0] == self.id:
                            graph_neighbours.append(caller_callee[1])
                        elif caller_callee[1] == self.id:
                            graph_neighbours.append(caller_callee[0])
            for i in range(len(graph_neighbours)):
                self.neighborNodes.append(self.get_params(graph_neighbours[i]))
        except IOError:
            print "not a valid Graph-File\n"
            pass
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

    def remove_finished_node(self, node_id):
        self.neighborNodes = [(n_id, ip, port) for n_id, ip, port in self.neighborNodes if n_id != node_id]

    # ____________________________ END: Node-Management-Functions ____________________________________________________

    # ____________________________ BEGIN: Send-Functions _____________________________________________________________
    def send_msg(self, receiver_ip, receiver_port, cmd, payload):
        json_msg = json.dumps({'sID': str(self.id), 'time': str(time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime())),
                               'cmd': str(cmd), 'payload': str(payload)})
        self.print_send_msg(json_msg, receiver_ip, receiver_port)
        self.send_socket.sendto(json_msg, (receiver_ip, int(receiver_port)))

    def send_to_neighbours(self, cmd, payload):
        for i in range(len(self.neighborNodes)):
            current_neighbour = self.neighborNodes[i]
            self.send_msg(current_neighbour[1], current_neighbour[2], cmd, payload)
    # ____________________________ END: Send-Functions _______________________________________________________________

    # ____________________________ BEGIN: Message-Handling ___________________________________________________________
    # Send-Message print
    @staticmethod
    def print_send_msg(msg, receiver_ip, receiver_port):
        json_msg = json.loads(msg)
        print ""
        print "________ Message - Sending ________"
        print "to:              " + str(receiver_ip + ":" + str(receiver_port))
        print "send time:       " + str(json_msg["time"])
        print "command:         " + str(json_msg["cmd"])
        print "payload:         " + str(json_msg["payload"])
        print ""

    # Receive-Message print
    @staticmethod
    def print_msg(msg):
        json_msg = json.loads(msg)
        print ""
        print "________ Message - Received ________"
        print "from:            " + str(json_msg["sID"])
        print "received time:   " + str(json_msg["time"])
        print "command:         " + str(json_msg["cmd"])
        print "payload:         " + str(json_msg["payload"])
        print ""

    # Handling of received Messages
    def msg_handling(self, msg):
        json_msg = json.loads(msg)

        command = str(json_msg["cmd"])

        # Node-Control-Msg
        if command == "end":
            # stop self
            self.send_to_neighbours("endedNeighbour", "")
            self.stop()
        elif command == "setInit":
            # set self as Initiator
            self.isInitiator = True
        elif command == "rmInit":
            # unset self as Initiator
            self.isInitiator = False

        # Network-Management-Msg
        elif command == "randNG":
            # generate random Network
            self.set_online_nodes(json_msg["payload"])
            self.generate_random_network()
        elif command == "graphNG":
            # generate Network from Graph
            self.generate_network_by_graph(json_msg["payload"])
        elif command == "genGraph":
            # generate Network-Graph
            self.network_graph_feedback()
        elif command == "endedNeighbour":
            # Neighbour has stopped
            self.remove_finished_node(json_msg["sID"])
        elif command == "newNeighbour":
            # Node is new Neighbour
            new_neighbour = str(json_msg["payload"]).split(",")
            self.neighborNodes.append((new_neighbour[0], new_neighbour[1], new_neighbour[2]))

        # Rumor-Experiment-Msg
        elif command == "startRumor":
            # Start Rumor Experiment
            self.initiate_rumor_experiment(json_msg["payload"])
        elif command == "spreadRumor":
            # hear Rumor
            self.hear_rumor(json_msg["sID"], json_msg["payload"])
        elif command == "getRumorStat":
            # send Rumor Experiment Status
            self.rumor_status_feedback()
        elif command == "resetRumorExperiment":
            # reset Rumor Experiment
            self.reset_rumor_experiment()
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
