import threading
import time
import socket
import queue
import SDPTPTC


def initialisation():
    global home_address
    home_address = SDPTPTC.get_local_address()

    global ports
    ports = queue.Queue()
    for port in range(6113, 7112):
        ports.put(port)

    global connections
    connections = []

    global running
    running = True

    global update_list
    update_list = []

    global connections_transmission
    connections_transmission = ""

def connection_update():
    for connection in connections:
        connections_transmission = ""
        if connection[0] != "":
            connections_transmission += "{0},{1}/".format(connection[0], connection[1])
    for update in update_list:
        update[1] = True
    return connections_transmission

class RequestHandler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while running:
            request_handler_socket = socket.socket()
            request_sender_socket, request_sender_address = SDPTPTC.socket_binder(request_handler_socket,6112,home_address)
            port = ports.get()
            request_sender_socket.send(str(port).encode())
            request_sender_identity = request_sender_socket.recv(128).decode()
            request_sender_socket.shutdown(socket.SHUT_RDWR)
            request_handler_socket.close()
            request_sender_socket.close()
            conversation_starter(True, request_sender_address , port, request_sender_identity)

class Transmitter(threading.Thread):
    def __init__(self, address, port, receiver_identity):
        threading.Thread.__init__(self)
        self.port = port
        self.address = address
        self.receiver_identity = receiver_identity

    def run(self):
        transmitter_socket = socket.socket()
        transmitter_socket = SDPTPTC.fail_repeat_connector(transmitter_socket,self.address,self.port,self.receiver_identity)

        connections.append([self.address, self.receiver_identity])
        update_list.append([self.getName(), False])
        index = update_list.index([self.getName(), False])
        connections_transmission = connection_update()
        while True:
            try:
                if update_list[index][1]:
                    print("Updating {0} @ {1}".format(self.receiver_identity,self.address))
                    transmitter_socket.send(connections_transmission.encode())
                    update_list[index][1] = False
            except socket.error:
                print("Closing")
                connections[index] = ["",""]
                update_list[index] = ["",False]
                connections_transmission = connection_update()

                break
            time.sleep(15)



def conversation_starter(recipient, receiver_address, receiver_port, sender_identity):
    print("running")
    if recipient:
        receiver_address = receiver_address[0]
        transmitter_thread = Transmitter(receiver_address, receiver_port, sender_identity)
        transmitter_thread.start()


def main():
    initialisation()
    request_handler = RequestHandler()
    request_handler.start()

main()
