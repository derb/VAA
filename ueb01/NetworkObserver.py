import sys
import logging
import socket
import string
import json
import time
import threading


class NetworkObserver:
    # Socket for Message-Receiving
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Socket for Message-Sending
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    id = 0                      # Fix ID for the Network-Observer
    observerIP = "127.0.0.1"    # Fix IP for the Network-Observer
    port = 5001                 # Fix Port of the Network-Observer

    onlineNodes = []            # List of all online Nodes

    graph_list = []             # Graph of current Network if requested

    sum_received = 0
    akk_received = False

    # ____________________________ BEGIN: init & del _________________________________________________________________
    def __init__(self):
        self.get_online_nodes()
        listener = threading.Thread(target=self.listen)
        listener.setDaemon(True)
        listener.start()

    def __del__(self):
        self.listen_socket.close()
        sys.exit(0)
    # ____________________________ END: init & del ___________________________________________________________________

    # ____________________________ BEGIN: Send- & Receive-Functions __________________________________________________
    def listen(self):
        self.listen_socket.bind((self.observerIP, int(self.port)))
        while True:
            msg, addr = self.listen_socket.recvfrom(1024)  # Buffer-Size set to 1024 bytes
            self.handle_msg(msg)

    def send_msg(self, receiver_ip, receiver_port, cmd, payload):
        json_msg = json.dumps({'sID': str(self.id), 'time': str(time.strftime("%d-%m-%Y %H:%M:%S",
                                                                              time.gmtime())), 'cmd': str(cmd),
                               'payload': str(payload)})
        self.send_socket.sendto(json_msg, (receiver_ip, int(receiver_port)))

    def send_msg_to_all(self, cmd, payload):
        json_msg = json.dumps({'sID': str(self.id), 'time': str(time.strftime("%d-%m-%Y %H:%M:%S",
                                                                              time.gmtime())), 'cmd': str(cmd),
                               'payload': str(payload)})
        for i in range(len(self.onlineNodes)):
            receiver = self.onlineNodes[i]
            self.send_socket.sendto(json_msg, (receiver[1], int(receiver[2])))
    # ____________________________ END: Send- & Receive-Functions ____________________________________________________

    # ____________________________ BEGIN: Node-Management-Functions __________________________________________________
    def get_node_by_id(self, node_id):
        for i in range(len(self.onlineNodes)):
            if self.onlineNodes[i][0] == node_id:
                return self.onlineNodes[i]
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
            while not self.akk_received:
                time.sleep(0.1)
            self.akk_received = False

    def initiate_network_by_graph(self):
        graph_file = raw_input("\nGraph-File: ")
        for i in range(len(self.onlineNodes)):
            current_node = self.onlineNodes[i]
            self.send_msg(current_node[1], current_node[2], "graphNG", graph_file)

    def clean_graph_list(self):
        tmp_list = []
        self.graph_list.sort(key=lambda x: x[0])
        for i in range(len(self.graph_list)):
            found = False
            current_element = self.graph_list[i]
            for j in range(len(tmp_list)):
                tmp_element = tmp_list[j]
                if tmp_element[1] == current_element[0]:
                    if tmp_element[0] == current_element[1]:
                        found = True
            if not found:
                tmp_list.append(current_element)
        self.graph_list = tmp_list

    def generate_graph_file(self, caller, callee_list):
        callees = str(callee_list).split(";")
        for i in range(len(callees)):
            self.graph_list.append((caller, callees[i]))
        if self.sum_received == len(self.onlineNodes):
            self.clean_graph_list()
            graph_str = "graph G {\n"
            for i in range(len(self.graph_list)):
                current_element = self.graph_list[i]
                graph_str += current_element[0] + " -- " + current_element[1] + ";\n"
            graph_str += "}"
            graph_file = open("graph.dot", "w")
            graph_file.write(graph_str)
            graph_file.close()
            self.sum_received = 0

    def request_network_graph(self):
        for i in range(len(self.onlineNodes)):
            current_node = self.onlineNodes[i]
            self.send_msg(current_node[1], current_node[2], "genGraph", "")

    def remove_finished_node(self, node_id):
        self.onlineNodes = [(n_id, ip, port) for n_id, ip, port in self.onlineNodes if n_id != node_id]
    # ____________________________ END: Logic ________________________________________________________________________

    # ____________________________ BEGIN: RUN & MSG-Handling _________________________________________________________
    def handle_msg(self, msg):
        json_msg = json.loads(msg)

        command = str(json_msg["cmd"])
        if command == "genGraphAck":
            self.sum_received += 1
            self.generate_graph_file(json_msg["sID"], json_msg["payload"])
        if command == "findNeighboursAck":
            self.akk_received = True
        if command == "rumorStat":
            print json_msg["sID"] + " --> " + json_msg["payload"]

    @staticmethod
    def print_commands():
        print "\n"                                      \
              "EXIT:                        0" + "\n" + \
              "List all Nodes:              1" + "\n" + \
              "End Node by ID:              2" + "\n" + \
              "End all Nodes:               3" + "\n" + \
              "Initiate random Network:     4" + "\n" + \
              "Initiate Network by Graph:   5" + "\n" + \
              "Get Network-Graph:           6" + "\n\n" + \
              "______ Rumor Experiment ______" + "\n" + \
              "Set Node as Initiator:       7" + "\n" + \
              "Unset Node as Initiator:     8" + "\n" + \
              "Start Rumor Experiment:      9" + "\n" + \
              "Rumor Experiment Status:    10" + "\n" + \
              "reset Rumor Experiment:     11" + "\n" + \
              ""

    def run(self):
        while True:
            self.print_commands()
            input_str = raw_input("Command: ")
            if input_str == "0":
                self.__del__()
            elif input_str == "1":
                print self.onlineNodes
            elif input_str == "2":
                node_id = raw_input("Node ID: ")
                node_to_stop = self.get_node_by_id(node_id)
                if node_to_stop == "-1":
                    print "Could not find Node by this ID"
                else:
                    self.send_msg(node_to_stop[1], node_to_stop[2], "end", "")
                    self.remove_finished_node(node_id)
            elif input_str == "3":
                for i in range(len(self.onlineNodes)):
                    self.send_msg(self.onlineNodes[i][1], self.onlineNodes[i][2], "end", "")
            elif input_str == "4":
                self.initiate_rand_network()
            elif input_str == "5":
                self.initiate_network_by_graph()
            elif input_str == "6":
                self.graph_list = []
                self.request_network_graph()

            # Rumor Experiment
            elif input_str == "7":
                node_id = raw_input("Node ID: ")
                node_to_set_initiator = self.get_node_by_id(node_id)
                if node_to_set_initiator == "-1":
                    print "Could not find Node by this ID"
                else:
                    self.send_msg(node_to_set_initiator[1], node_to_set_initiator[2], "setInit", "")
            elif input_str == "8":
                node_id = raw_input("Node ID: ")
                node_to_unset_initiator = self.get_node_by_id(node_id)
                if node_to_unset_initiator == "-1":
                    print "Could not find Node by this ID"
                else:
                    self.send_msg(node_to_unset_initiator[1], node_to_unset_initiator[2], "rmInit", "")
            elif input_str == "9":
                c_value = raw_input("c: ")
                try:
                    int(c_value)
                    is_int = True
                except ValueError:
                    is_int = False
                if is_int:
                    self.send_msg_to_all("startRumor", c_value)
                else:
                    print "c not a valid int"
            elif input_str == "10":
                self.send_msg_to_all("getRumorStat", "")
            elif input_str == "11":
                self.send_msg_to_all("resetRumorExperiment", "")
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
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv)
