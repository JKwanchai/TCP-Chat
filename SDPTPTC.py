import time
import socket
import secrets
import math


def fail_repeat_connector(socket_object, address, port, identity):
    error = False
    while not error:
        try:
            socket_object.connect((address, port))
            error = True
        except socket.error:
            error = False
            print("Connecting to {0} @ {1}".format(identity, address))
            time.sleep(1.5)
    print("Connected to {0} @ {1}".format(identity, address))
    return socket_object


def get_local_address():
    home_address = socket.gethostbyname(socket.gethostname())
    return home_address


def socket_binder(socket_object, port, home_address):
    socket_object.bind((home_address, port))
    print('request_handler_socket established on: {0}'.format(port))
    socket_object.listen(5)
    request_sender_socket, request_sender_address = socket_object.accept()
    return request_sender_socket, request_sender_address


def table_printer(connections):
    for row in connections:
        print("{1} - {0}".format(row[0], row[1]))


def help():
    print("""
Remeber when inputing commands seperate the different values using a space

Command\t##C\tUsage ##C Peer_Ident Peer_I.P._Address\tGuidance\tUsed to connect to another peer knowing their I.P address
Command\t##H\tUsage ##H                             \tGuidance\tIt's what your using Matty
Command\t##S\tUsage ##S Peer_Ident                  \tGuidance\tUsed to connect to another peer connected to the addressing server
Command\t##T\tUsage ##T                             \tGuidance\tUsed to view the list of active peers
Command\t##T\tUsage ##F                             \tGuidance\tUsed to clear the instruction buffer use in case of emergency, when you see lots of red text/error Matty

    """)


def who_am_i(identity, home_address, addressing_server_address):  # This is definitely not a refrence to Jackie Chan
    print("Identity is {0} @ {1} connected to an Addressing Server @ {2}".format(identity, home_address,
                                                                                 addressing_server_address))


def int_to_bytes(int_):
    bytes_ = int_.to_bytes(32, "big")
    return bytes_


def bytes_to_int(bytes_):
    int_ = int.from_bytes(bytes_, "big")
    return int_


# This is used to find sophia germain primes for added security


def key_generation_client(socket_object):
    s_g_primes = s_g_prime_generator(2 ** 12)
    s_g_prime = secrets.choice(s_g_primes)
    socket_object.send(int_to_bytes(s_g_prime))
    prim_root_modulo = bytes_to_int(socket_object.recv(32))
    secret_integer = secrets.randbits(16)
    client_public_integer = (prim_root_modulo ** secret_integer) % s_g_prime
    socket_object.send(int_to_bytes(client_public_integer))
    server_public_integer = bytes_to_int(socket_object.recv(32))
    shared_secret = (server_public_integer ** secret_integer) % s_g_prime
    return shared_secret


def key_generation_server(socket_object):
    time.sleep(2.5)
    s_g_prime = bytes_to_int(socket_object.recv(32))
    prime_root_modulo = secrets.choice(primeRoots(s_g_prime))
    socket_object.send(int_to_bytes(prime_root_modulo))
    secret_integer = secrets.randbits(16)
    server_public_integer = (prime_root_modulo ** secret_integer) % s_g_prime
    socket_object.send(int_to_bytes(server_public_integer))
    client_public_integer = bytes_to_int(socket_object.recv(32))
    shared_secret = (client_public_integer ** secret_integer) % s_g_prime
    return shared_secret


def primeRoots(modulo):
    roots = []
    required_set = set(num for num in range(1, modulo) if math.gcd(num, modulo) == 1)

    for g in range(1, modulo):
        actual_set = set(pow(g, powers, modulo) for powers in range(1, modulo))
        if required_set == actual_set:
            roots.append(g)
    return roots[30:]


def s_g_prime_generator(limit):
    i = 3
    q = [2]
    S_g = []
    while i < limit:
        p = 1
        for x in range(2, round(i ** 0.5) + 1):
            p = min(p, i % x)
        if p:
            q += [i]
            s = (i - 1) / 2
            if s in q:
                S_g.append(int(s))
        i += 2
    return S_g[10:]


def create_key(numerical_key):
    numerical_key = str(numerical_key)
    key = ""
    a_t = open('AIGD.txt', 'r')
    lines = a_t.readlines()
    for counter in range(16):
        key += lines[int(numerical_key[:1]) * counter * int(int(numerical_key[1:]) ** 0.5)][:2]

    return key


def encode(key, string):
    encoded_chars = []
    for i in range(len(string)):
        key_c = key[i % len(key)]
        encoded_c = chr(ord(string[i]) + ord(key_c) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = "".join(encoded_chars)
    return encoded_string


def decode(key, string):
    encoded_chars = []
    for i in range(len(string)):
        key_c = key[i % len(key)]
        encoded_c = chr(ord(string[i]) - ord(key_c) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = "".join(encoded_chars)
    return encoded_string
