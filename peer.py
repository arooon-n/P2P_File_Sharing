import socket
import threading
import os

HEADER = 64
PORT = 8000
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_PATH = "shared_files_peer"

if not os.path.exists(FILE_PATH):
    os.makedirs(FILE_PATH)

SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

peer_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
peer_server.bind(ADDR)

def handle_client(conn, addr):
    print(f"\n[NEW CONNECTION] {addr} connected.")
    try:
        while True:
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if not msg_length:
                break
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            
            if msg == DISCONNECT_MESSAGE:
                break

            command, *args = msg.split()
            if command == "UPLOAD" and len(args) == 1:
                handle_upload(conn, args[0])
            elif command == "DOWNLOAD" and len(args) == 1:
                handle_download(conn, args[0])
            else:
                conn.send("\nERROR: Invalid command.".encode(FORMAT))
    except Exception as e:
        print(f"\n[ERROR] Exception in client handler: {e}")
    finally:
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
    print(f"\n[UPLOAD] {filename} uploaded successfully.")

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
        print(f"\n[DOWNLOAD] {filename} downloaded successfully.")
    else:
        conn.send(f"\nERROR: {filename} not found.".encode(FORMAT))

def start_server():
    try:
        peer_server.listen()
        print(f"\n[LISTENING] Peer server is listening on {SERVER}")
        while True:
            conn, addr = peer_server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"\n[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Server is shutting down.")
    finally:
        peer_server.close()

def send_message(peer_client, msg):
    try:
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        peer_client.send(send_length)
        peer_client.send(message)
    except (ConnectionResetError, ConnectionAbortedError) as e:
        print(f"Connection error: {e}")

def upload_file(peer_client, filename):
    filepath = os.path.join(FILE_PATH, filename)
    if os.path.exists(filepath):
        send_message(peer_client, f"UPLOAD {filename}")
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                peer_client.send(data)
        peer_client.send(b"--END--")
        print(f"\n[UPLOAD] {filename} uploaded successfully.")
    else:
        print("File not found.")

def download_file(peer_client, filename):
    send_message(peer_client, f"DOWNLOAD {filename}")
    filepath = os.path.join(FILE_PATH, filename)
    temp_filepath = filepath + ".tmp"
    try:
        with open(temp_filepath, 'wb') as f:
            while True:
                data = peer_client.recv(1024)
                try:
                    if len(data) <= HEADER and data.decode(FORMAT).startswith("ERROR"):
                        print(data.decode(FORMAT))
                        f.close()
                        os.remove(temp_filepath)
                        return
                except UnicodeDecodeError:
                    pass
                if b"--END--" in data:
                    data, _ = data.split(b"--END--")
                    f.write(data)
                    break
                f.write(data)
        os.rename(temp_filepath, filepath)
        print(f"\n[DOWNLOAD] {filename} downloaded successfully.")
    except Exception as e:
        print(f"[ERROR] {e}")
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

def connect_to_peer(target_ip, port):
    peer_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_client.connect((target_ip, port))
    return peer_client

server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

while True:
    mode = input("\nEnter mode (CONNECT/DISCONNECT): ").strip().upper()
    if mode == "CONNECT":
        target_ip = input("Enter peer IP: ").strip()
        peer_client = connect_to_peer(target_ip, PORT)
        
        while True:
            command = input("Enter command (UPLOAD/DOWNLOAD/DISCONNECT): ").strip().upper()
            if command == "UPLOAD":
                filename = input("Enter filename to upload: ").strip()
                upload_file(peer_client, filename)
            elif command == "DOWNLOAD":
                filename = input("Enter filename to download: ").strip()
                download_file(peer_client, filename)
            elif command == "DISCONNECT":
                send_message(peer_client, DISCONNECT_MESSAGE)
                peer_client.close()
                break
            else:
                print("Invalid command.")
    elif mode == "DISCONNECT":
        break
    else:
        print("Invalid mode.")