import sqlite3
import threading
import os
import socket
import logic_server
from utils import *
from setting import *

class CServerBL:

    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._server_socket = None
        self._is_srv_running = True
        self._client_handlers = []

    def stop_server(self):
        try:
            self._is_srv_running = False
            # Close server socket
            if self._server_socket is not None:
                self._server_socket.close()
                self._server_socket = None

            if len(self._client_handlers) > 0:
                # Waiting to close all opened threads
                for client_thread in self._client_handlers:
                    client_thread.join()

        except Exception as e:
            print(e)

    def start_server(self):
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.bind((self._host, self._port))
            self._server_socket.listen(5)
            while self._is_srv_running and self._server_socket is not None:

                # Accept socket request for connection
                client_socket, address = self._server_socket.accept()

                # Start Thread
                cl_handler = CClientHandler(client_socket, address)
                cl_handler.start()
                self._client_handlers.append(cl_handler)
        finally:
            print(f"[SERVER_BL] Server thread is DONE")

class CClientHandler(threading.Thread):

    _client_socket = None
    _address = None

    def __init__(self, client_socket, address):
        super().__init__()

        self._client_socket = client_socket
        self._address = address

    def run(self):
        # This code run in separate thread for every client
        connected = True
        while connected:
            # 1. Get message from socket and check it
            valid_msg, msg = receive_msg(self._client_socket)
            # print(msg)
            if valid_msg:
                # Handle DISCONNECT command
                if msg == DISCONNECT_MSG:
                    connected = False
                    break
                self._client_socket.send(make_msg(logic_server.response(msg)).encode(FORMAT))
            else:
                self._client_socket.send(make_msg("404").encode(FORMAT))

        self._client_socket.close()


if __name__ == "__main__":

    # Подключение к базе данных (если файла нет, он будет создан)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Создаем таблицу users
    cursor.execute('''
               CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   login TEXT NOT NULL UNIQUE,
                   password TEXT NOT NULL,
                   coins INTEGER DEFAULT 50 NOT NULL
               )
           ''')

    # Создание таблицы posts
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auth_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        image TEXT,
        FOREIGN KEY (auth_id) REFERENCES users(id)
    )
    ''')

    # Создание таблицы comments
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        auth_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        FOREIGN KEY (post_id) REFERENCES posts(id),
        FOREIGN KEY (auth_id) REFERENCES users(id)
    )
    ''')

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()

    print("Таблицы успешно созданы!")
    server = CServerBL(SERVER_HOST, PORT)
    server.start_server()