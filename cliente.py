import socket
import threading

HOST = 'localhost'
PORT_TCP = 5000
PORT_UDP = 6000

# Lida com notificações recebidas via UDP
def escutar_udp():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', PORT_UDP))
    while True:
        msg, _ = udp_socket.recvfrom(1024)
        print(f"\n[NOTIFICAÇÃO UDP]: {msg.decode()}\n> ", end='')

# Inicia escuta UDP em uma thread
threading.Thread(target=escutar_udp, daemon=True).start()

# Cliente envia tarefas via TCP
while True:
    tarefa = input("> Digite uma nova tarefa (ou 'sair'): ")
    if tarefa.lower() == 'sair':
        break
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT_TCP))
        s.send(tarefa.encode())
        lista_atualizada = s.recv(4096).decode()
        print("📋 Lista de Tarefas Atualizada:", lista_atualizada)