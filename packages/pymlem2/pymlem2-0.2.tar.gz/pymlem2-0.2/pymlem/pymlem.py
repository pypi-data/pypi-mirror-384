class PyMlem2:
    def __init__(self):
        pass

    def multi_server(self):
        return """
import socket
import threading

clients = []

def handle_client(client_socket, addr):
    print(f"[+] New connection from {addr}")
    while True:
        try:
            msg = client_socket.recv(1024).decode()
            if not msg:
                break  # Client disconnected
            print(f"[{addr}] {msg}")
            broadcast(msg, client_socket)
        except:
            break
    if client_socket in clients:
        clients.remove(client_socket)
    client_socket.close()
    print(f"[-] Connection closed from {addr}")

def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message.encode())
            except:
                client.close()
                clients.remove(client)

def start_server():
    host = '127.0.0.1'  # Localhost, change if needed
    port = 5000
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[*] Server listening on {host}:{port}...")

    while True:
        client_socket, addr = server.accept()
        clients.append(client_socket)
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()

if __name__ == "__main__":
    start_server()

"""

    def multi_client(self):
        return """
import socket
import threading

def receive_messages(client):
    while True:
        try:
            msg = client.recv(1024).decode()
            if msg:
                print(f">> {msg}")
        except:
            print("[!] Connection lost.")
            break

def start_client():
    host = '127.0.0.1'  # Change this to the server IP if connecting remotely
    port = 5000

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect((host, port))
        print(f"Connected to server at {host}:{port}")
    except:
        print("[!] Could not connect to the server.")
        return

    # Start a thread to receive messages
    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    # Main loop to send messages
    while True:
        msg = input()
        if msg.strip() == "":
            continue
        try:
            client.send(msg.encode())
            print(f"You: {msg}")
        except:
            print("[!] Failed to send message.")
            break

if __name__ == "__main__":
    start_client()

"""
    
    def token_ring(self):
        return """
import socket
import threading
import time
import sys

# Define the ring structure: each process knows the next one
NEXT_PORT = {
    5001: 5002,
    5002: 5003,
    5003: 5001
}

# This function runs in a thread and listens for the token
def listen(my_port):
    server = socket.socket()
    server.bind(('localhost', my_port))
    server.listen()
    print(f"[{my_port}] Listening for token...")

    while True:
        conn, _ = server.accept()
        msg = conn.recv(1024).decode()
        conn.close()

        if msg == "TOKEN":
            print(f"[{my_port}] Received TOKEN.")
            enter_critical_section(my_port)
            send_token(NEXT_PORT[my_port])

# This simulates the critical section
def enter_critical_section(my_port):
    print(f"[{my_port}] >>> Entering Critical Section...")
    time.sleep(2)  # simulate doing something important
    print(f"[{my_port}] <<< Exiting Critical Section.")

# This sends the token to the next process
def send_token(next_port):
    time.sleep(1)  # simulate some delay
    try:
        s = socket.socket()
        s.connect(('localhost', next_port))
        s.send("TOKEN".encode())
        s.close()
        print(f"[{next_port}] <- Token sent")
    except Exception as e:
        print(f"[!] Failed to send token to {next_port}: {e}")

# Main function to start a process
def run(my_port, start_token=False):
    # Start listening thread
    threading.Thread(target=listen, args=(my_port,), daemon=True).start()

    # If this process is starting with the token, send it to itself after delay
    if start_token:
        time.sleep(2)
        send_token(my_port)

    # Keep the main thread alive
    while True:
        time.sleep(1)

# Run with: python token_ring.py <port> [start]
if __name__ == "__main__":
    port = int(sys.argv[1])
    start_token = len(sys.argv) > 2 and sys.argv[2] == "start"
    run(port, start_token)
"""

    def mutual_exclusion_coordinator(self):
        return """
import socket
import threading

# Global lock to track whether the critical section is in use
CS_LOCKED = False

# Handle incoming requests from clients
def handle_client(conn):
    global CS_LOCKED
    try:
        msg = conn.recv(1024).decode()
        if msg == "REQUEST":
            if not CS_LOCKED:
                print("[Coordinator] GRANTing access.")
                conn.send("GRANT".encode())
                CS_LOCKED = True
            else:
                print("[Coordinator] DENYing access (CS locked).")
                conn.send("DENY".encode())
        elif msg == "RELEASE":
            CS_LOCKED = False
            print("[Coordinator] Released lock.")
    except Exception as e:
        print("[Coordinator] Error handling client:", e)
    finally:
        conn.close()

# Start the coordinator server
def run():
    server = socket.socket()
    server.bind(('localhost', 6000))  # Fixed port for coordinator
    server.listen()
    print("[Coordinator] Running on port 6000...")

    while True:
        conn, _ = server.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    run()
"""

    def mutual_exclusion_client(self):
        return """
import socket
import time
import sys

# Send a request to enter the critical section
def request_cs():
    try:
        s = socket.socket()
        s.connect(('localhost', 6000))  # Coordinator's fixed port
        s.send("REQUEST".encode())
        reply = s.recv(1024).decode()
        s.close()
        return reply
    except Exception as e:
        print("[Client] Error requesting CS:", e)
        return "ERROR"

# Notify the coordinator that CS is released
def release_cs():
    try:
        s = socket.socket()
        s.connect(('localhost', 6000))
        s.send("RELEASE".encode())
        s.close()
    except Exception as e:
        print("[Client] Error releasing CS:", e)

# Main client loop
def run(pid):
    while True:
        input(f"[Client {pid}] Press Enter to request critical section...")
        reply = request_cs()
        if reply == "GRANT":
            print(f"[Client {pid}] >>> Entering Critical Section")
            time.sleep(2)  # Simulate work in CS
            print(f"[Client {pid}] <<< Exiting Critical Section")
            release_cs()
        elif reply == "DENY":
            print(f"[Client {pid}] Access Denied. Try again later.")
        else:
            print(f"[Client {pid}] Unexpected reply: {reply}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python centralized_client.py <client_id>")
        sys.exit(1)

    run(sys.argv[1])

"""

    def ricart_agrawala(self):
        return """
import socket
import threading
import time
import sys

# List of all process ports in the system (update as needed)
ALL_PORTS = [5001, 5002, 5003]

# Lamport timestamp
clock = 0
requesting = False
our_request_time = None
deferred_replies = []

replies_received = 0
lock = threading.Lock()

def send_message(port, message):
    try:
        s = socket.socket()
        s.connect(('localhost', port))
        s.send(message.encode())
        s.close()
    except:
        print(f"[{my_port}] Could not send to {port}")

def multicast_request():
    global clock, our_request_time, requesting, replies_received

    with lock:
        clock += 1
        our_request_time = clock
        requesting = True
        replies_received = 0

    msg = f"REQUEST:{our_request_time}:{my_port}"
    for port in ALL_PORTS:
        if port != my_port:
            send_message(port, msg)

def handle_message(msg, sender_port):
    global clock, replies_received, requesting

    parts = msg.split(":")
    if parts[0] == "REQUEST":
        req_time = int(parts[1])
        sender = int(parts[2])

        with lock:
            clock = max(clock, req_time) + 1

            # Check if we should defer the reply
            if requesting and (
                (our_request_time < req_time) or
                (our_request_time == req_time and my_port < sender)
            ):
                deferred_replies.append(sender)
            else:
                send_message(sender, "REPLY")

    elif parts[0] == "REPLY":
        with lock:
            replies_received += 1

def listen():
    server = socket.socket()
    server.bind(('localhost', my_port))
    server.listen()
    print(f"[{my_port}] Listening...")

    while True:
        conn, _ = server.accept()
        msg = conn.recv(1024).decode()
        handle_message(msg, _)
        conn.close()

def enter_critical_section():
    print(f"[{my_port}] >>> ENTERING CRITICAL SECTION <<<")
    time.sleep(2)
    print(f"[{my_port}] <<< EXITING CRITICAL SECTION >>>")

def release():
    global requesting, our_request_time

    with lock:
        requesting = False
        our_request_time = None
        for port in deferred_replies:
            send_message(port, "REPLY")
        deferred_replies.clear()

def run():
    threading.Thread(target=listen, daemon=True).start()
    time.sleep(2)  # Let other processes start

    while True:
        input(f"[{my_port}] Press Enter to request critical section...")
        multicast_request()

        # Wait for all REPLYs
        while True:
            with lock:
                if replies_received == len(ALL_PORTS) - 1:
                    break
            time.sleep(0.1)

        enter_critical_section()
        release()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ricart_agrawala.py <port>")
        sys.exit(1)

    my_port = int(sys.argv[1])
    run()

"""

    def lamport_clock(self):
        return """
import socket
import threading
import time
import sys

# Simulated list of process ports
ALL_PORTS = [5001, 5002, 5003]

class LamportProcess:
    def __init__(self, my_port):
        self.port = my_port
        self.clock = 0
        self.lock = threading.Lock()

    def increment_clock(self):
        with self.lock:
            self.clock += 1

    def update_clock_on_receive(self, received_ts):
        with self.lock:
            self.clock = max(self.clock, received_ts) + 1

    def send_message(self, target_port):
        self.increment_clock()
        message = f"{self.clock}"
        try:
            s = socket.socket()
            s.connect(('localhost', target_port))
            s.send(message.encode())
            s.close()
            print(f"[{self.port}] Sent message to {target_port} with timestamp {self.clock}")
        except:
            print(f"[{self.port}] Failed to send to {target_port}")

    def receive_message(self, conn, sender):
        msg = conn.recv(1024).decode()
        received_ts = int(msg)
        print(f"[{self.port}] Received message from {sender} with timestamp {received_ts}")
        self.update_clock_on_receive(received_ts)
        print(f"[{self.port}] Updated clock to {self.clock}")

    def listen(self):
        server = socket.socket()
        server.bind(('localhost', self.port))
        server.listen()
        print(f"[{self.port}] Listening for messages...")

        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.receive_message, args=(conn, addr[1]), daemon=True).start()

    def run(self):
        threading.Thread(target=self.listen, daemon=True).start()
        time.sleep(2)  # Let everyone start

        while True:
            print(f"\n[{self.port}] Clock = {self.clock}")
            print("Options:")
            print("1. Send message to process")
            print("2. Internal event (increment clock)")
            choice = input("Choice: ")

            if choice == "1":
                target = int(input("Enter target port: "))
                if target in ALL_PORTS and target != self.port:
                    self.send_message(target)
                else:
                    print("Invalid port.")
            elif choice == "2":
                self.increment_clock()
                print(f"[{self.port}] Internal event occurred. Clock = {self.clock}")
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python lamport_clock.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    process = LamportProcess(port)
    process.run()
"""

    def vector_clock(self):
        return """
import threading
import time
import random

NUM_PROCESSES = 3

class Process:
    def __init__(self, pid, controller):
        self.pid = pid
        self.vector_clock = [0] * NUM_PROCESSES
        self.controller = controller

    def internal_event(self):
        self.vector_clock[self.pid] += 1
        print(f" Process {self.pid} INTERNAL event: {self.vector_clock}")

    def send_event(self, target_pid):
        self.vector_clock[self.pid] += 1
        msg = self.vector_clock.copy()
        print(f" Process {self.pid} SEND to {target_pid}: {msg}")
        self.controller.deliver_message(self.pid, target_pid, msg)

    def receive_event(self, sender_pid, received_vc):
        for i in range(NUM_PROCESSES):
            self.vector_clock[i] = max(self.vector_clock[i], received_vc[i])
        self.vector_clock[self.pid] += 1
        print(f" Process {self.pid} RECEIVE from {sender_pid}: {received_vc} → Updated: {self.vector_clock}")

class Controller:
    def __init__(self):
        self.processes = [Process(pid, self) for pid in range(NUM_PROCESSES)]

    def deliver_message(self, sender_pid, target_pid, vector_clock):
        # Simulate network delay
        delay = random.uniform(0.5, 1.5)
        threading.Timer(delay, self.processes[target_pid].receive_event,
                        args=(sender_pid, vector_clock)).start()

    def run_simulation(self):
        threads = []

        # Simulate actions for each process
        for p in self.processes:
            t = threading.Thread(target=self.simulate_process, args=(p,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def simulate_process(self, process):
        time.sleep(random.uniform(0.5, 1))
        process.internal_event()

        time.sleep(random.uniform(0.5, 1))
        target = random.choice([p.pid for p in self.processes if p.pid != process.pid])
        process.send_event(target)

        time.sleep(random.uniform(1, 2))
        process.internal_event()

if __name__ == "__main__":
    controller = Controller()
    controller.run_simulation()
"""