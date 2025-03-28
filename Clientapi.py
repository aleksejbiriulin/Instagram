import socket
from setting import *
from utils import *


class CClientBL:

    def __init__(self, host: str, port: int):

        self._client_socket = None
        self._host = host
        self._port = port

    def connect(self) -> socket:
        try:
            self._client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self._client_socket.connect((self._host,self._port))
            return self._client_socket
        except Exception as e:
            return None

    def disconnect(self) -> bool:
        try:
            self.send_data(DISCONNECT_MSG)
            self._client_socket.close()
            return True
        except Exception as e:
            return False

    def send_data(self, msg: str) -> bool:
        msg = make_msg(msg)
        message = msg.encode(FORMAT)
        self._client_socket.send(message)
        return True
        try:
            msg = make_msg(msg)
            message = msg.encode(FORMAT)
            self._client_socket.send(message)
            return True
        except Exception as e:
            return False

    def receive_data(self) -> str:
        try:
            (bres, msg) = receive_msg(self._client_socket)
            if bres:
                return msg
            else:
                return "Invalid msg"
        except Exception as e:
            return ""