import time
import socket

def fail_repeat_connector(socket_object,address,port,identity):
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

def socket_binder(socket_object,port,home_address):
        socket_object.bind((home_address, port))
        print('request_handler_socket established on: {0}'.format(port))
        socket_object.listen(5)
        request_sender_socket, request_sender_address = socket_object.accept()
        return request_sender_socket, request_sender_address


def table_printer(connections):
    for row in connections:
        print("{1} - {0}".format(row[0],row[1]))

def help():
    print("""
Remeber when inputing commands seperate the different values using a space

Command\t##C\tUsage ##C Peer_Ident Peer_I.P._Address\tGuidance\tUsed to connect to another peer knowing their I.P address
Command\t##H\tUsage ##H                             \tGuidance\tIt's what your using Matty
Command\t##S\tUsage ##S Peer_Ident                  \tGuidance\tUsed to connect to another peer connected to the addressing server
Command\t##T\tUsage ##T                             \tGuidance\tUsed to view the list of active peers
Command\t##T\tUsage ##F                             \tGuidance\tUsed to clear the instruction buffer use in case of emergency, when you see lots of red text/error Matty

    """)

def who_am_i(identity,home_address,addressing_server_address):#This is definitely not a refrence to Jackie Chan 
    print("Identity is {0} @ {1} connected to an Addressing Server @ {2}".format(identity,home_address,addressing_server_address))
