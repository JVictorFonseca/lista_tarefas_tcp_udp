import socket
import threading
import json
import os

HOST = 'localhost'
PORT_TCP = 5000
PORT_UDP = 6000
BROADCAST_IP = '255.255.255.255'
ARQUIVO_TAREFAS = 'tarefas.json'

# Carrega as tarefas salvas no JSON ou cria uma lista vazia
if os.path.exists(ARQUIVO_TAREFAS):
    with open(ARQUIVO_TAREFAS, 'r') as f:
        tarefas = json.load(f)
else:
    tarefas = []

# Salva tarefas no arquivo JSON
def salvar_tarefas():
    with open(ARQUIVO_TAREFAS, 'w') as f:
        json.dump(tarefas, f, indent=4)

# Envia notificação via UDP broadcast
def enviar_notificacao_udp(mensagem):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.sendto(mensagem.encode(), (BROADCAST_IP, PORT_UDP))
    udp_socket.close()

# Lida com conexões TCP de clientes
def lidar_com_cliente_tcp(conn, addr):
    print(f"Conexão TCP de {addr}")
    try:
        while True:
            dados = conn.recv(1024).decode()
            if not dados:
                break
            print(f"Recebido de {addr}: {dados}")
            tarefas.append(dados)
            salvar_tarefas()
            conn.send(json.dumps(tarefas).encode())
            enviar_notificacao_udp(f"Nova tarefa adicionada: {dados}")
    except:
        print(f"Conexão encerrada com {addr}")
    finally:
        conn.close()

# Inicia servidor TCP
def iniciar_servidor_tcp():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind((HOST, PORT_TCP))
    tcp_socket.listen()
    print(f"Servidor TCP ouvindo em {HOST}:{PORT_TCP}")
    while True:
        conn, addr = tcp_socket.accept()
        threading.Thread(target=lidar_com_cliente_tcp, args=(conn, addr)).start()

iniciar_servidor_tcp()