import socket
import os

# Define constants
HEADER = 64
PORT = 8000
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "10.12.180.88"  # Use your actual server IP here
ADDR = (SERVER, PORT)
FILE_PATH = "shared_files"

# Ensure client files directory exists
if not os.path.exists(FILE_PATH):
    os.makedirs(FILE_PATH)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send_message(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)

def upload_file(filename):
    filepath = os.path.join(FILE_PATH, filename)
    if os.path.exists(filepath):
        send_message(f"UPLOAD {filename}")
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                client.send(data)
        client.send(b"--END--")
        print(f"[UPLOAD] {filename} uploaded successfully.")
    else:
        print("File not found.")

def download_file(filename):
    send_message(f"DOWNLOAD {filename}")
    filepath = os.path.join(FILE_PATH, filename)
    error = False
    with open(filepath, 'wb') as f:
        while True:
            data = client.recv(1024)
            try:
                # Attempt to decode small packets for error checking
                if len(data) <= HEADER and data.decode(FORMAT).startswith("ERROR"):
                    print(data.decode(FORMAT))
                    error = True
                    break
            except UnicodeDecodeError:
                # Skip decoding if data is binary
                pass

            if b"--END--" in data:
                data, _ = data.split(b"--END--")
                f.write(data)
                break

            f.write(data)
    if error:
        os.remove(filepath)
        return
    print(f"[DOWNLOAD] {filename} downloaded successfully.")


def disconnect():
    send_message(DISCONNECT_MESSAGE)


while True:
    command = input("Enter command (UPLOAD/DOWNLOAD/DISCONNECT): ").strip().upper()
    if command == "UPLOAD":
        filename = input("Enter filename to upload: ").strip()
        upload_file(filename)
    elif command == "DOWNLOAD":
        filename = input("Enter filename to download: ").strip()
        download_file(filename)
    elif command == "DISCONNECT":
        disconnect()
        break
    else:
        print("Invalid command.")