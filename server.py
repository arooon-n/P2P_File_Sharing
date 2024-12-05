import socket
import threading
import os

# Define constants
HEADER = 64
PORT = 8000
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_PATH = "shared_files"

SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

# Ensure shared files directory exists
if not os.path.exists(FILE_PATH):
    os.makedirs(FILE_PATH)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                connected = False
            else:
                command, filename = msg.split()
                if command == "UPLOAD":
                    handle_upload(conn, filename)
                elif command == "DOWNLOAD":
                    handle_download(conn, filename)
    conn.close()

def handle_upload(conn, filename):
    filepath = os.path.join(FILE_PATH, filename)
    with open(filepath, 'wb') as f:
        while True:
            data = conn.recv(1024)
            if b"--END--" in data:
                data, _ = data.split(b"--END--")
                f.write(data)
                break
            f.write(data)
    print(f"[UPLOAD] {filename} uploaded successfully.")

def handle_download(conn, filename):
    filepath = os.path.join(FILE_PATH, filename)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                conn.send(data)
        conn.send(b"--END--")
        print(f"[DOWNLOAD] {filename} downloaded successfully.")
    else:
        conn.send("ERROR: File not found.".encode(FORMAT))

def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

print("[STARTING] Server is starting...")
start()