import socket
import threading
host = "127.0.0.1"
port = 12345
s = socket.socket()
s.bind((host, port))
s.listen()


LIST_OF_FLYING = ["<class '__main__.Defiler'>",
                  "<class '__main__.Apocalypse'>"]
minerals = []
our_units = []
workers = []
our_structs = []
enemy_structs = []
prod_structs = []
offensive_structs = []
enemy_units = []

counter = 1
con1, addr = s.accept()
print("Connection from: " + str(addr))
con1.sendall(str(counter).encode())
counter = 2
con2, addr = s.accept()
print("Connection from: " + str(addr))
con2.sendall(str(counter).encode())
def con_loop(_con1, _con2):
    while True:
        data = _con1.recv(1024).decode()
        print("Received from client: " + str(data))
        _con2.sendall(data.encode())
thread1 = threading.Thread(target=con_loop, args=(con1, con2))
thread1.start()
thread2 = threading.Thread(target=con_loop, args=(con2, con1))
thread2.start()