import json
import time
import socket


class SendMsg:
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sender_id = -1
    send_time = time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime())

    receiver_id = -1
    receiver_ip = ""
    receiver_port = -1

    command = ""

    payload = ""

    def send_msg(self):
        self.send_socket.sendto(str(self.build_msg()), (self.receiver_ip, int(self.receiver_port)))

    def build_msg(self):
        json_msg = json.dumps({'sID': str(self.sender_id), 'time': str(time), 'cmd': str(self.command),
                               'payload': str(self.payload)})
        return json_msg

    def __init__(self, sID, rID, rIP, rPort, cmd, payload):
        self.sender_id = sID
        self.receiver_id = rID
        self.receiver_ip = rIP
        self.receiver_port = rPort
        self.command = cmd
        self.payload = payload
        self.send_msg()
