import string
import sys
import random
import socket
import logging
import json
import time
import Queue
import threading


class ReqObj:
    def __init__(self, prio=0, sid=0, rid=0):
        self.prio = prio
        self.sid = sid
        self.rid = rid

    def __str__(self):
        return str(self.prio) + ";" + str(self.sid) + ";" + str(self.rid)

    def __repr__(self):
        return str(self.prio) + ";" + str(self.sid) + ";" + str(self.rid)

    def ro(self, reg_str):
        tmp = str(reg_str).split(";")
        self.prio = int(tmp[0])
        self.sid = int(tmp[1])
        self.rid = int(tmp[2])
        return self

    def __cmp__(self, other):
        if int(self.prio) == int(other.prio):
            return cmp(int(self.sid), int(other.sid))
        return cmp(int(self.prio), int(other.prio))

    def __lt__(self, other):
        if int(self.prio) == int(other.prio):
            return int(self.sid) < int(other.sid)
        return int(self.prio) < int(other.prio)

    def __gt__(self, other):
        if int(self.prio) == int(other.prio):
            return int(self.sid) > int(other.sid)
        return int(self.prio) > int(other.prio)

    def __le__(self, other):
        if int(self.prio) == int(other.prio):
            return int(self.sid) <= int(other.sid)
        return int(self.prio) <= int(other.prio)

    def __ge__(self, other):
        if int(self.prio) == int(other.prio):
            return int(self.sid) >= int(other.sid)
        return int(self.prio) >= int(other.prio)

    def __eq__(self, other):
        if int(self.prio) == int(other.prio):
            if int(self.sid) == int(other.sid):
                return int(self.rid) == int(other.rid)
        return False


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

    # ____________________________ BEGIN: Bank _______________________________________________________________________
    def sort_pq(self):
        tmp = []
        while not self.lock_queue.empty():
            lq_ob = self.lock_queue.get()
            tmp.append(lq_ob)
        tmp.sort()
        for i in range(len(tmp)):
            self.lock_queue.put(tmp[i])

    sum_nodes = 0
    lock_queue = Queue.PriorityQueue()
    flood_fh_id = 0
    money = 0
    my_req = Queue.Queue()
    rel_list = []
    flood_msgs = []
    my_id = -1
    lock_ok_rec = 0
    percent = 0

    @staticmethod
    def gen_request():
        req_time = int(time.time())
        generated = False
        value = 0
        while not generated:
            value = random.randint(1, sum_nodes)
            if value == int(my_id):
                generated = False
            else:
                generated = True
        return ReqObj(req_time, my_id, value)

    def init_lock(self):
        req_ob = self.my_req.get()
        self.my_req.put(req_ob)
        req_str = str(req_ob.prio) + ";" + str(req_ob.sid) + ";" + str(req_ob.rid)
        self.flood_msgs.append(req_str)
        self.send_to_neighbours("flood_lock", req_str)

    def flood_lock(self, msg, sid):
        if msg in self.rel_list:
            tmp = str(msg).split(";")
            port = 6000 + int(tmp[1])
            self.send_msg("127.0.0.1", port, "lock_ok", "")
        if msg not in self.flood_msgs:
            self.flood_fh_id = sid
            self.flood_msgs.append(msg)
            for i in range(len(self.neighborNodes)):
                current_node = self.neighborNodes[i]
                if not current_node[0] == self.flood_fh_id:
                    self.send_msg(current_node[1], current_node[2], "flood_lock", msg)
            self.handle_locking(msg)

    def free_lock(self):
        time.sleep(0.5)
        free_ob = self.lock_queue.get()
        for i in range(sum_nodes):
            port = 6001 + i
            print port
            if not i == my_id:
                self.send_msg("127.0.0.1", port, "free_lock", str(free_ob))
        port = 6000 + int(free_ob.sid)
        self.send_msg("127.0.0.1", port, "lock_ok", "")
        self.my_req.get()
        print "Lock_Queue: " + str(self.lock_queue.queue)
        self.start_bank()

    def free_lock_acc(self, to_free):
        self.rel_list.append(str(to_free))
        if self.lock_queue.empty():
            return
        ob = self.lock_queue.get()
        if to_free == ob:
            port = 6000 + int(to_free.sid)
            self.send_msg("127.0.0.1", port, "lock_ok", "")
            return
        else:
            self.lock_queue.put(ob)
            self.sort_pq()

    def handle_locking(self, msg):
        tmp = str(msg).split(";")
        port = 6000 + int(tmp[1])
        req_ob = ReqObj().ro(msg)
        my_req_ob = self.my_req.get()
        self.my_req.put(my_req_ob)

        if int(my_req_ob.prio) == 0:
            self.send_msg("127.0.0.1", port, "lock_ok", "")
            return
        print "my_req_ob: " + str(my_req_ob)
        print "req_ob:    " + str(req_ob)
        if my_req_ob < req_ob:
            self.lock_queue.put(req_ob)
            self.sort_pq()
        else:
            self.send_msg("127.0.0.1", port, "lock_ok", "")
        print "Lock_Queue: " + str(self.lock_queue.queue)

    def locking_acc(self):
        self.lock_ok_rec += 1
        print "Current Lock ok: " + str(self.lock_ok_rec)
        if self.lock_ok_rec == (sum_nodes - 1):
            print "Lock ok"
            self.init_transaction()
            self.lock_ok_rec = 0

    def init_transaction(self):
        # lock for money_req
        self.money_locked.put(True)
        global percent
        percent = random.randint(0, 100)
        req_ob = self.my_req.get()
        self.my_req.put(req_ob)
        port = 6000 + int(req_ob.rid)
        json_msg = json.dumps({'B': str(money), 'p': str(percent)})
        self.send_msg("127.0.0.1", port, "transaction", json_msg)

    def transaction_rec(self, b, p, sid):
        # lock for money_req
        self.money_locked.put(True)
        global money
        port = 6000 + sid
        json_msg = json.dumps({'B': str(money)})
        self.send_msg("127.0.0.1", port, "transaction_acc", json_msg)
        if b >= money:
            money = round((money + (b * p / 100))*100)/100
        else:
            money = round((money - (money * p / 100))*100)/100
        print "New Money: " + str(money)
        # free lock for money_req
        self.money_locked.queue.clear()

    def transaction_acc(self, b):
        # free lock for money_req
        self.money_locked.queue.clear()
        global percent
        global money
        if b >= money:
            money = round((money + (b * percent / 100))*100)/100
        else:
            money = round((money - (money * percent / 100))*100)/100
        print "New Money: " + str(money)
        self.lock_ok_rec = 0
        self.free_lock()

    def run_bank(self):
        self.my_req.put(self.gen_request())
        time_wait = random.randint(0, 3)
        print "Wait_time: " + str(time_wait)
        time.sleep(time_wait)
        self.init_lock()

    def start_bank(self):
        bank_t = threading.Thread(target=self.run_bank(), args=self.lock_queue)
        bank_t.setDaemon(True)
        bank_t.start()
    # ____________________________ END: Bank _________________________________________________________________________

    # ____________________________ BEGIN: Money Status _______________________________________________________________
    money_locked = Queue.Queue()
    money_init_node = -1
    money_req_msg_sum = 0
    money_req_echo_sum = 0
    money_req_spread = Queue.Queue()
    msg_str_queue = Queue.Queue()

    def init_money_stat(self):
        self.send_to_neighbours("get_money_stat", "")
        self.money_req_spread.put(True)

    def spread_money_status(self, sid):
        self.money_req_msg_sum += 1
        if self.money_init_node == -1:
            self.money_init_node = int(sid)
        if self.money_req_spread.empty():
            self.money_req_spread.put(True)
            for i in range(len(self.neighborNodes)):
                node = self.neighborNodes[i]
                to_send = int(node[0]) == int(self.money_init_node)
                if not to_send:
                    self.send_msg(node[1], node[2], "get_money_stat", "")
        # heard all requests:
        if self.money_req_msg_sum == len(self.neighborNodes):
            self.start_money_eval(self.money_init_node)

    def echo_money_status(self, msg):
        self.money_req_echo_sum += 1
        if self.msg_str_queue.empty():
            self.msg_str_queue.put(msg)
        else:
            tmp_msg = self.msg_str_queue.get()
            tmp_msg += ";" + msg
            self.msg_str_queue.put(tmp_msg)
        ref_val = self.money_req_msg_sum + self.money_req_echo_sum
        if ref_val == len(self.neighborNodes):
            # for coordinator:
            if self.is_coordinator:
                my_money_eval = threading.Thread(target=self.eval_coordinator_money(self.id))
                my_money_eval.setDaemon(True)
                my_money_eval.start()
            else:
                self.start_money_eval(self.money_init_node)

    def start_money_eval(self, to_id):
        money_eval = threading.Thread(target=self.eval_money(to_id))
        money_eval.setDaemon(True)
        money_eval.start()

    def eval_money(self, to_id):
        pl = ""
        if not self.msg_str_queue.empty():
            pl = self.msg_str_queue.get() + ";"
        while True:
            if self.money_locked.empty():
                pl += str(self.id) + ":" + str(money)
                port = 6000 + to_id
                self.send_msg("127.0.0.1", port, "get_money_echo", pl)
                return

    def eval_coordinator_money(self, self_id):
        pl = ""
        if not self.msg_str_queue.empty():
            pl = self.msg_str_queue.get() + ";"
        while True:
            if self.money_locked.empty():
                pl += str(self_id) + ":" + str(money)
                self.msg_str_queue.put(pl)

                value = str(self.msg_str_queue.get())
                values = value.split(";")
                for i in range(len(values)):
                    print values[i]
                break
        # process values
        full_money = 0.0
        for i in range(len(values)):
            tmp_val = values[i].split(":")
            full_money += float(tmp_val[1])
        print "Full Money: " + str(full_money)
        msg = json.dumps({'full_money': str(full_money), 'list': value})
        self.send_msg("127.0.0.1", 5001, "capital_status", msg)

    def reset_money_evaluation(self):
        self.money_locked.queue.clear()
        self.money_init_node = -1
        self.money_req_msg_sum = 0
        self.money_req_echo_sum = 0
        self.money_req_spread.queue.clear()
        self.msg_str_queue.queue.clear()
        # for coordinator
        if self.is_coordinator:
            money_reval = threading.Thread(target=self.re_init_money_stat(self.neighborNodes))
            money_reval.setDaemon(True)
            money_reval.start()

    def re_init_money_stat(self, node_list):
        ref_time = int(time.time()) + 7
        while True:
            if time.time() > ref_time:
                break
        for i in range(len(node_list)):
            self.send_msg(node_list[i][1], node_list[i][2], "get_money_stat", "")
        self.money_req_spread.put(True)

    # ____________________________ END: Money Status _________________________________________________________________

    # ____________________________ BEGIN: Election ___________________________________________________________________
    is_coordinator = False
    election_handled = False
    will_be_coordinator = -1
    election_value = -1
    heard_first_election = -1
    election_msg_counter = 0
    election_echo_count = 0

    def init_election(self, on_nodes):
        global sum_nodes
        sum_nodes = on_nodes
        print str(sum_nodes)
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
                self.get_online_nodes()
                print "I am Coordinator"
                self.init_money_stat()
                # for i in range(len(self.onlineNodes)):
                #     self.send_msg(self.onlineNodes[i][1], self.onlineNodes[i][2], "start_bank", "")
                # self.start_bank()

    # ____________________________ END: Election  ____________________________________________________________________

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

        # Bank Expermiment
        elif command == "start_exp":
            self.is_coordinator = False
            self.election_handled = False
            self.will_be_coordinator = -1
            self.election_value = -1
            self.heard_first_election = -1
            self.election_msg_counter = 0
            self.election_echo_count = 0
            global my_id
            my_id = self.id
            global money
            money = random.randint(0, 100000) * 1.0
            print "Start-Capital: " + str(money)
            self.init_election(int(json_msg["payload"]))
        elif command == "expend_election":
            self.expend_election(json_msg["payload"], json_msg["sID"])
        elif command == "election_echo":
            self.echo_election(json_msg["payload"])
        elif command == "start_bank":
            self.start_bank()
        elif command == "flood_lock":
            self.flood_lock(json_msg["payload"], json_msg["sID"])
        elif command == "lock_ok":
            self.locking_acc()
        elif command == "transaction":
            msg = json.loads(json_msg["payload"])
            self.transaction_rec(float(msg["B"]), int(msg["p"]), int(json_msg["sID"]))
        elif command == "transaction_acc":
            msg = json.loads(json_msg["payload"])
            self.transaction_acc(float(msg["B"]))
        elif command == "free_lock":
            self.free_lock_acc(ReqObj().ro(json_msg["payload"]))
        elif command == "get_money_stat":
            self.spread_money_status(json_msg["sID"])
        elif command == "get_money_echo":
            self.echo_money_status(str(json_msg["payload"]))
        elif command == "rme":
            self.reset_money_evaluation()

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
        logging.critical(str(type(e)) + " : " + str(e.args), exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv)
