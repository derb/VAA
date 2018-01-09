import string
import sys
import random
import socket
import logging
import json
import time
import math
from multiprocessing import Process


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

    # ____________________________ BEGIN: Election ___________________________________________________________________
    log_name = ""

    dc = Process

    is_coordinator = False
    election_handled = False
    will_be_coordinator = -1
    election_value = -1
    heard_first_election = -1
    election_msg_counter = 0
    election_echo_count = 0

    def init_election(self, m):
        self.time = random.randint(1, m)
        print "Start-Time: " + str(self.time)
        self.will_be_coordinator = random.randint(0, 1)
        print "\nelection value: " + str(self.will_be_coordinator)
        if self.will_be_coordinator == 1:
            self.election_handled = True
            self.election_value = self.id
            self.send_to_neighbours("expend_election", self.id)

    def expend_election(self, value, sender_id):
        if self.election_value < value:
            self.election_value = value
            self.election_msg_counter = 1
            self.election_handled = False
            self.heard_first_election = sender_id
        elif self.election_value == value:
            self.election_msg_counter += 1

            if self.election_msg_counter >= len(self.neighborNodes):
                self.send_msg_by_id(self.heard_first_election, "election_echo", self.election_value)

        if not self.election_handled:
            self.election_handled = True
            for i in range(len(self.neighborNodes)):
                current_node = self.neighborNodes[i]
                if current_node[0] != self.heard_first_election:
                    self.send_msg(current_node[1], current_node[2], "expend_election", self.election_value)

    def echo_election(self, value):
        if value == self.election_value:
            self.election_msg_counter += 1
            self.election_echo_count += 1
            if self.election_msg_counter >= len(self.neighborNodes):
                self.send_msg_by_id(self.heard_first_election, "election_echo", self.election_value)

            if self.election_echo_count == len(self.neighborNodes) and value == self.id:
                self.is_coordinator = True
                print "I am Coordinator"
                self.get_online_nodes()
                self.init_time_finding()
                self.dc = Process(target=self.double_counting_handler)
                self.dc.start()

    # ____________________________ END: Election  ____________________________________________________________________

    # ____________________________ BEGIN: Distributed Consensus ______________________________________________________
    time = 0

    s_value = 0
    p_value = 0
    a_max = 0

    is_elector = False
    rounds = 1
    p_list = []
    value_changed = False
    current_p_index = 0
    round_up = False

    msg_snd_count = 0
    msg_rec_count = 0

    def init_time_finding(self):
        if self.s_value > len(self.onlineNodes):
            self.s_value = len(self.onlineNodes)
        s_list = random.sample(self.onlineNodes, self.s_value)
        print s_list
        for i in range(len(s_list)):
            self.send_msg(s_list[i][1], s_list[i][2], "start_tf", "")

    def start_time_finding(self):
        self.is_elector = True
        self.p_list = random.sample(self.neighborNodes, self.p_value)
        print self.p_list
        self.send_time_finding()

    def send_time_finding(self):
        if self.rounds > self.a_max:
            return
        index = self.current_p_index
        self.msg_snd_count += 1
        logging.basicConfig(filename=self.log_name, level=logging.DEBUG)
        logging.info("Send_MSG to: " + str(self.p_list[index][0]) + "  msg: tf; " + str(self.time) +
                     "  msg_snd_count : " + str(self.msg_snd_count) + "  msg_rec_count : " + str(self.msg_rec_count) +
                     "  round: " + str(self.rounds))
        time.sleep(0.1)
        self.send_msg(self.p_list[index][1], self.p_list[index][2], "tf", self.time)
        self.current_p_index += 1
        if self.current_p_index == len(self.p_list):
            self.round_up = True
            self.current_p_index = 0

    def react_time_finding(self, new_time, sender_id):
        self.msg_rec_count += 1
        if not self.time == new_time:
            self.value_changed = True
            self.time = new_time
        if self.round_up and self.value_changed:
            self.round_up = False
            self.value_changed = False
            self.rounds += 1
        if self.round_up and not self.value_changed:
            self.round_up = False
            self.value_changed = False
            self.rounds += 1
            return
        logging.basicConfig(filename=self.log_name, level=logging.DEBUG)
        logging.info("Rec_MSG from: " + str(sender_id) + "  msg: tf_acc; " + str(new_time) +
                     "  msg_snd_count : " + str(self.msg_snd_count) + "  msg_rec_count : " + str(self.msg_rec_count) +
                     "  round: " + str(self.rounds))
        self.send_time_finding()

    def acc_time_finding(self, new_time, sender_id):
        logging.basicConfig(filename=self.log_name, level=logging.DEBUG)
        logging.info("Rec_MSG from: " + str(sender_id) + "  msg: tf; " + str(new_time) +
                     "  msg_snd_count : " + str(self.msg_snd_count) + "  msg_rec_count : " + str(self.msg_rec_count) +
                     "  round: " + str(self.rounds))
        self.msg_rec_count += 1
        print "self.time: " + str(self.time) + "  new.time: " + str(new_time)
        f_time = self.get_new_time(self.time, new_time)
        print "f_time: " + str(f_time)
        self.time = f_time
        self.msg_snd_count += 1
        logging.info("Send_MSG to: " + str(sender_id) + "  msg: tf_acc; " + str(f_time) +
                     "  msg_snd_count : " + str(self.msg_snd_count) + "  msg_rec_count : " + str(self.msg_rec_count) +
                     "  round: " + str(self.rounds))
        self.send_msg_by_id(sender_id, "tf_acc", f_time)

    @staticmethod
    def get_new_time(m_time, s_time):
        return int(math.ceil((m_time + s_time) / 2.0))

    # ____________________________ END: Distributed Consensus ________________________________________________________

    # ____________________________ BEGIN: Double Counting  ___________________________________________________________
    network_finished = False
    all_received = False
    current_nw_snd = 0
    current_nw_rec = 0
    old_nw_snd = 0
    old_nw_rec = 0
    feedback_counter = 0

    def double_counting_handler(self):
        while True:
            time.sleep(3)
            for i in range(len(self.onlineNodes)):
                self.send_msg(self.onlineNodes[i][1], self.onlineNodes[i][2], "dc", "")

    def double_counting_feedback_handler(self, msg_rec, msg_snd):
        self.current_nw_snd += msg_snd
        self.current_nw_rec += msg_rec
        self.feedback_counter += 1
        if self.feedback_counter == len(self.onlineNodes):
            self.current_nw_snd += self.msg_snd_count
            self.current_nw_rec += self.msg_rec_count
            if self.current_nw_snd == self.old_nw_snd and self.current_nw_rec == self.old_nw_rec:
                if self.current_nw_snd == self.current_nw_rec:
                    self.network_finished = True
                    print "Network finished"
                    self.dc.terminate()
                    self.init_collect_time()
                else:
                    print "Error occurred"
            else:
                self.old_nw_snd = self.current_nw_snd
                self.old_nw_rec = self.current_nw_rec
                self.current_nw_snd = 0
                self.current_nw_rec = 0
                self.all_received = False
                self.feedback_counter = 0

    def double_counting_acc(self, s_id):
        pl = json.dumps({'msg_rec': self.msg_rec_count, 'msg_snd': self.msg_snd_count})
        self.send_msg_by_uid(s_id, "dc_acc", pl)

    # ____________________________ END: Double Counting ______________________________________________________________

    # ____________________________ BEGIN: Time Echo __________________________________________________________________

    first_time_coll_id = -1
    time_coll_heard = 0
    time_coll_echo_heard = 0
    time_send = False
    echo_send = False

    collected_times = []
    final_time = -1

    def init_collect_time(self):
        self.send_to_neighbours("time_coll", "")

    def collect_time(self, sender_id):
        self.time_coll_heard += 1
        if self.first_time_coll_id == -1:
            self.first_time_coll_id = sender_id
        if self.time_coll_heard < len(self.neighborNodes) and not self.time_send:
            for i in range(len(self.neighborNodes)):
                node = self.neighborNodes[i]
                if not node[0] == self.first_time_coll_id:
                    self.time_send = True
                    self.send_msg(node[1], node[2], "time_coll", "")
        ref_val = self.time_coll_heard + self.time_coll_echo_heard
        if ref_val >= len(self.neighborNodes) and not self.echo_send:
            self.echo_send = True
            self.send_msg_by_id(self.first_time_coll_id, "time_coll_echo", self.time)

    def echo_collect_time(self, rec_time):
        if self.first_time_coll_id == -1:
            self.collected_times.append(rec_time)
        self.time_coll_echo_heard += 1
        ref_val = self.time_coll_heard + self.time_coll_echo_heard
        if ref_val >= len(self.neighborNodes) and not self.first_time_coll_id == -1 and not self.echo_send:
            self.echo_send = True
            if rec_time == self.time:
                self.send_msg_by_id(self.first_time_coll_id, "time_coll_echo", self.time)
            else:
                self.send_msg_by_id(self.first_time_coll_id, "time_coll_echo", "-1")
        elif ref_val >= len(self.neighborNodes) and self.first_time_coll_id == -1:
            self.eval_time()

    # ____________________________ END: Time Echo ____________________________________________________________________

    # ____________________________ BEGIN: Time Eval __________________________________________________________________

    def eval_time(self):
        time_found = True
        for i in range(len(self.collected_times) - 1):
            if time_found:
                if self.collected_times[i] == self.collected_times[i + 1]:
                    time_found = True
                else:
                    time_found = False
        if time_found:
            self.final_time = self.collected_times[0]
            time_msg = "Time found: " + str(self.final_time)
        else:
            time_msg = "No Time found"
        print time_msg
        self.propagate_time(time_msg)

    def propagate_time(self, msg):
        for i in range(len(self.onlineNodes)):
            node = self.onlineNodes[i]
            self.send_msg(node[1], node[2], "prop_time", msg)

    @staticmethod
    def receive_time(time_msg):
        print time_msg
    # ____________________________ END: Time Eval ____________________________________________________________________

    # ____________________________ BEGIN: Reset Philosopher Experiment _______________________________________________

    def reset_philosopher_exp(self):
        self.onlineNodes = []

        self.is_coordinator = False
        self.election_handled = False
        self.will_be_coordinator = -1
        self.election_value = -1
        self.heard_first_election = -1
        self.election_msg_counter = 0
        self.election_echo_count = 0

        self.time = 0
        self.s_value = 0
        self.p_value = 0
        self.a_max = 0
        self.is_elector = False
        self.rounds = 1
        self.p_list = []
        self.value_changed = False
        self.current_p_index = 0
        self.round_up = False
        self.msg_snd_count = 0
        self.msg_rec_count = 0

        self.network_finished = False
        self.all_received = False
        self.current_nw_snd = 0
        self.current_nw_rec = 0
        self.old_nw_snd = 0
        self.old_nw_rec = 0
        self.feedback_counter = 0

        self.first_time_coll_id = -1
        self.time_coll_heard = 0
        self.time_coll_echo_heard = 0
        self.time_send = False
        self.echo_send = False
        self.collected_times = []
        self.final_time = -1
    # ____________________________ END: Reset Philosopher Experiment _________________________________________________

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

    def get_online_nodes(self):
        config_file = open('config', 'r')
        current_entry = config_file.readline()

        while current_entry != "":

            blank_pos = string.find(current_entry, " ")
            colon_pos = string.find(current_entry, ":")

            ce_id = current_entry[0:blank_pos]
            ce_ip = current_entry[blank_pos + 1:colon_pos]
            ce_port = current_entry[colon_pos + 1:len(current_entry) - 1]

            if ce_id != "" and ce_id != self.id:
                self.onlineNodes.append((ce_id, ce_ip, ce_port))
            current_entry = config_file.readline()
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

    def send_msg_by_id(self, receiver_id, cmd, payload):
        for i in range(len(self.neighborNodes)):
            current_neighbour = self.neighborNodes[i]
            if current_neighbour[0] == receiver_id:
                self.send_msg(current_neighbour[1], current_neighbour[2], cmd, payload)

    def send_msg_by_uid(self, receiver_id, cmd, payload):
        node = self.get_params(receiver_id)
        self.send_msg(node[1], node[2], cmd, payload)
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

        # Distributed Consensus
        elif command == "start_exp":
            self.is_coordinator = False
            self.election_handled = False
            self.will_be_coordinator = -1
            self.election_value = -1
            self.heard_first_election = -1
            self.election_msg_counter = 0
            self.election_echo_count = 0

            pl = json.loads(json_msg["payload"])
            m = int(pl["m"])
            self.s_value = int(pl["s"])
            p = int(pl["p"])
            if p > len(self.neighborNodes):
                self.p_value = len(self.neighborNodes)
            else:
                self.p_value = p

            self.a_max = int(pl["a_max"])

            self.init_election(m)
        elif command == "expend_election":
            self.expend_election(json_msg["payload"], json_msg["sID"])
        elif command == "election_echo":
            self.echo_election(json_msg["payload"])

        elif command == "start_tf":
            self.start_time_finding()
        elif command == "tf":
            self.acc_time_finding(int(json_msg["payload"]), json_msg["sID"])
        elif command == "tf_acc":
            self.react_time_finding(int(json_msg["payload"]), json_msg["sID"])
        elif command == "dc":
            self.double_counting_acc(json_msg["sID"])
        elif command == "dc_acc":
            pl = json.loads(json_msg["payload"])
            msg_rec = int(pl["msg_rec"])
            msg_snd = int(pl["msg_snd"])
            self.double_counting_feedback_handler(msg_rec, msg_snd)

        elif command == "time_coll":
            self.collect_time(json_msg["sID"])
        elif command == "time_coll_echo":
            self.echo_collect_time(int(json_msg["payload"]))

        elif command == "prop_time":
            self.receive_time(json_msg["payload"])

        elif command == "reset_phil_exp":
            self.reset_philosopher_exp()
        # Other-Msg
        elif command == "msg":
            return
    # ____________________________ END: Message-Handling _____________________________________________________________

    # ____________________________ BEGIN: RUN & Stop _________________________________________________________________
    def stop(self):
        self.listen_socket.close()
        sys.exit(0)

    def run(self):
        self.log_name = "protocol/node_" + str(self.id)
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
        logging.critical(str(type(e)) + " : " + str(e.args), exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv)
