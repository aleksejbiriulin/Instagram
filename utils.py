import socket
from setting import *

def receive_msg(my_socket: socket) -> (bool, str):
    """Extract message from protocol, without the length field
       If length field does not include a number, returns False, "Error" """
    str_header = my_socket.recv(HEADER_LEN).decode(FORMAT)
    if len(str_header) == 0:
        return True, DISCONNECT_MSG
    length = int(str_header)
    if length > 0:
        buf = my_socket.recv(length).decode(FORMAT)
    else:
        return False, "Error"

    return True, buf

def make_msg(msg: str):
    msg = str(msg)
    return f"{len(msg):010d}{msg}"
