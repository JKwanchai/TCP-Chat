import queue
import socket
import threading
import time

import SDPTPTC


def initialisation():
    global instructions
    instructions = []

    global identity
    identity = input("Please input identity")

    global home_address
    home_address = SDPTPTC.get_local_address()

    global running
    running = True

    global conditional
    conditional = threading.Condition()

    global ports
    ports = queue.Queue()
    for port in range(5113, 6112):
        ports.put(port)

    global names
    names = []

    global input_barrier
    input_barrier = threading.Barrier(2)

    global commands
    commands = ['##C', '##H', '##I', '##S', '##T', '##F']

    global connections
    connections = []

    global server_address
    server_address = input("Input addressing server address")
    if server_address == "0":
        server_address = home_address


def server_connector():
    request = socket.socket()
    request = SDPTPTC.fail_repeat_connector(request, server_address, 6112, "Addressing Server")
    receiver_port = int((request.recv(128)).decode())
    request.send(identity.encode())
    request.shutdown(socket.SHUT_RDWR)
    request.close()
    addressing_receiver_thread = AddressingReceiver(receiver_port)
    addressing_receiver_thread.start()


def connections_string_array(connections_raw):
    for index in range(len(connections)):
        connections.pop(index)
    half_raw_connections = connections_raw.split("/")
    for connection in half_raw_connections:
        if connection != "":
            connections.append(connection.split(","))


def conversation_starter(recipient, receiver_address, receiver_port, sender_port, sender_identity, key):
    if recipient:
        receiver_address = receiver_address[0]
    elif not recipient:
        request = socket.socket()
        request = SDPTPTC.fail_repeat_connector(request, receiver_address, sender_port, sender_identity)
        sender_port = ports.get()
        request.send((str(sender_port) + ' ' + identity).encode())
        receiver_port = int((request.recv(128)).decode())
        key = SDPTPTC.key_generation_client(request)
        key = SDPTPTC.create_key(key)
        request.shutdown(socket.SHUT_RDWR)
        request.close()
    transmitter_thread = Transmitter(receiver_address, receiver_port, sender_identity, key)
    receiver_thread = Receiver(sender_port, key)
    transmitter_thread.start()
    receiver_thread.start()


def main():
    initialisation()
    server_connector()
    main_loop = MainLoop()
    request_handler = RequestHandler()
    conversation_handler = ConversationHandler()
    main_loop.start()
    request_handler.start()
    conversation_handler.start()


class MainLoop(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while running:
            # Lock all threads which read from instructions

            instruction = input()
            if instruction[:3] in commands:
                if instruction.startswith('##C'):
                    instructions.append([instruction])
                    input_barrier.wait()
                elif instruction.startswith('##S'):
                    instructions.append([instruction])
                    input_barrier.wait()
                elif instruction.startswith('##T'):
                    SDPTPTC.table_printer(connections)
                elif instruction.startswith('##H'):
                    SDPTPTC.help_command()
                elif instruction.startswith('##I'):
                    SDPTPTC.who_am_i(identity, home_address, server_address)
                elif instruction.startswith('##F'):
                    length = len(instructions)
                    for index in range(length):
                        instructions.pop(index)
                    print("Instruction buffer cleared of {0} instructions".format(length))
            elif instruction.startswith('#'):
                instructions.append([instruction])


class RequestHandler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while running:
            request_handler_socket = socket.socket()
            request_sender_socket, request_sender_address = SDPTPTC.socket_binder(request_handler_socket, 5112, server_address)
            port = ports.get()
            request_sender_socket.send(str(port).encode())
            request_sender_information = request_sender_socket.recv(128).decode()
            request_sender_port = int(request_sender_information[0:4])
            request_sender_identity = request_sender_information[5:]
            numerical_key = SDPTPTC.key_generation_server(request_sender_socket)
            key = SDPTPTC.create_key(numerical_key)

            request_sender_socket.shutdown(socket.SHUT_RDWR)
            request_handler_socket.close()
            request_sender_socket.close()
            conversation_starter(True, request_sender_address, request_sender_port, port, request_sender_identity, key)


class ConversationHandler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while running:

            # Wait for unlock prevent it from reading instructions

            input_barrier.wait()
            parameters = []
            split_instruction = (instructions.pop(0)[0].split())
            if split_instruction[0].startswith('##C'):
                parameters.append((split_instruction[2]))
                parameters.append(ports.get())
                parameters.append(5112)
                parameters.append(split_instruction[1])
                conversation_starter(False, parameters[0], parameters[1], parameters[2], parameters[3], 00)
            elif split_instruction[0].startswith('##S'):
                for connection in connections:
                    if connection[1] == split_instruction[1]:
                        parameters.append(connection[0])
                        parameters.append(ports.get())
                        parameters.append(5112)
                        parameters.append(connection[1])
                        conversation_starter(False, parameters[0], parameters[1], parameters[2], parameters[3], 00)


class Transmitter(threading.Thread):
    def __init__(self, address, port, receiver_identity, key):
        threading.Thread.__init__(self)
        self.port = port
        self.address = address
        self.receiver_identity = receiver_identity
        self.key = key

    def run(self):
        names.append(self.getName())
        transmitter_socket = socket.socket()
        transmitter_socket = SDPTPTC.fail_repeat_connector(transmitter_socket, self.address, self.port,
                                                           self.receiver_identity)
        commands.append("#{0}".format(self.receiver_identity))
        while True:
            while len(instructions) != 0:
                if instructions[0][0].startswith('#{0}'.format(self.receiver_identity)):
                    split_instruction = (instructions.pop(0)[0]).split(' ', 1)
                    message = SDPTPTC.encode(self.key, (identity + ': ' + split_instruction[1]))
                    transmitter_socket.send(message.encode())


class AddressingReceiver(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port

    def run(self):
        receiver_socket = socket.socket()
        receiver_socket.bind((home_address, self.port))
        receiver_socket.listen(5)
        while True:
            transmitter_socket, transmitter_address = receiver_socket.accept()

            while True:
                message = ""
                message += transmitter_socket.recv(4096).decode()
                current_length = len(connections)
                connections_string_array(message)
                new_length = len(connections)
                if new_length > current_length > 0:
                    print("New user has joined server {0} @ {1}".format(connections[-1][1], connections[-1][0]))
                time.sleep(15)


class Receiver(threading.Thread):
    def __init__(self, port, key):
        threading.Thread.__init__(self)
        self.port = port
        self.key = key

    def run(self):
        receiver_socket = socket.socket()
        receiver_socket.bind((home_address, self.port))
        receiver_socket.listen(5)
        while True:
            transmitter_socket, transmitter_address = receiver_socket.accept()
            while True:
                message = transmitter_socket.recv(4096).decode()
                if message != '':
                    print((SDPTPTC.decode(self.key, message) + '\t' + str(time.ctime())))


main()
