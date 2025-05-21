import socket
import threading

HOST = 'localhost'
PORT_TCP = 5000
PORT_UDP = 6000

# Lida com notificações recebidas via UDP

#bind fixo
#def escutar_udp():
'''    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', PORT_UDP))
    while True:
        msg, _ = udp_socket.recvfrom(1024)
        print(f"[NOTIFICAÇÃO]: {msg.decode()}")
'''        

#Sem bind() fixo, para poder ter mais de um cliente ao mesmo tempo
def escutar_udp():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(('', PORT_UDP))  # OK em Linux/macOS, mas pode causar problema no Windows se mais de um cliente fizer isso
    while True:
        msg, _ = udp_socket.recvfrom(1024)
        print(f"[NOTIFICAÇÃO]: {msg.decode()}")
        

# Inicia escuta UDP em uma thread
threading.Thread(target=escutar_udp, daemon=True).start()

# Cliente envia tarefas via TCP
while True:
    tarefa = input("Digite uma nova tarefa (ou 'sair'): ")
    if tarefa.lower() == 'sair':
        break
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT_TCP))
        s.send(tarefa.encode())
        lista_atualizada = s.recv(4096).decode()
        print("Tarefas atualizadas:", lista_atualizada)