import socket
import threading
import json

HOST = 'localhost'
PORT_TCP = 5000
PORT_UDP = 6000

# Thread para escutar notificações UDP
def escutar_udp():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', PORT_UDP))
    while True:
        msg, _ = udp_socket.recvfrom(1024)
        print(f"\n[🔔 NOTIFICAÇÃO]: {msg.decode()}")

# Inicia thread de escuta UDP
threading.Thread(target=escutar_udp, daemon=True).start()

# Loop principal do cliente
while True:
    print("\n--- Nova Tarefa ---")
    titulo = input("Título da tarefa (ou 'sair'): ").strip()
    if titulo.lower() == 'sair':
        print("Encerrando cliente...")
        break
    descricao = input("Descrição: ").strip()

    # Monta mensagem no formato JSON
    mensagem = {
        "tipo": "adicionar",
        "titulo": titulo,
        "descricao": descricao
    }

    # Envia mensagem via TCP
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT_TCP))
            s.send(json.dumps(mensagem).encode())

            resposta = s.recv(4096).decode()
            tarefas = json.loads(resposta)

            print("\n📋 Lista atualizada de tarefas:")
            for i, tarefa in enumerate(tarefas, 1):
                print(f"{i}. {tarefa['titulo']}: {tarefa['descricao']}")
    except ConnectionRefusedError:
        print("[ERRO] Não foi possível conectar ao servidor.")
    except json.JSONDecodeError:
        print("[ERRO] Resposta do servidor está em formato inválido.")