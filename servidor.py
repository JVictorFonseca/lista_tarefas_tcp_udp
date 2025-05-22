import socket
import threading
import json
import os

HOST = 'localhost'
PORT_TCP = 5000
PORT_UDP = 6000
BROADCAST_IP = '255.255.255.255'
ARQUIVO_TAREFAS = 'tarefas.json'

clientes = {}  # dicionário: nome_cliente -> socket
tarefas_enviadas = []  # tarefas com id, cliente, tarefa
contador_tarefas = 1   # contador incremental de IDs

# Carrega tarefas do JSON
if os.path.exists(ARQUIVO_TAREFAS):
    with open(ARQUIVO_TAREFAS, 'r') as f:
        tarefas_enviadas = json.load(f)
        if tarefas_enviadas:
            contador_tarefas = max(t["id"] for t in tarefas_enviadas) + 1

# Salva tarefas no JSON
def salvar_tarefas():
    with open(ARQUIVO_TAREFAS, 'w') as f:
        json.dump(tarefas_enviadas, f, indent=4)

# Envia notificação via UDP broadcast
def enviar_notificacao_udp(mensagem):
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.sendto(mensagem.encode('utf-8'), (BROADCAST_IP, PORT_UDP))
        udp_socket.close()
    except Exception as e:
        print(f"[ERRO-UDP] {e}")

# Lida com clientes TCP
def lidar_com_cliente_tcp(conn, addr):
    try:
        nome_cliente = conn.recv(1024).decode().strip()
        if not nome_cliente:
            conn.close()
            return
        clientes[nome_cliente] = conn
        print(f"[TCP] {nome_cliente} conectado de {addr}")

        while True:
            dados = conn.recv(1024).decode()
            if not dados:
                break
            print(f"[TCP] {nome_cliente}: {dados}")

    except Exception as e:
        print(f"[ERRO] Conexão com {addr} encerrada. {e}")
    finally:
        conn.close()
        if nome_cliente in clientes:
            del clientes[nome_cliente]
            print(f"[INFO] Cliente removido: {nome_cliente}")

# Inicia o servidor TCP
def iniciar_servidor_tcp():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind((HOST, PORT_TCP))
    tcp_socket.listen()
    print(f"[TCP] Servidor ouvindo em {HOST}:{PORT_TCP}")
    while True:
        conn, addr = tcp_socket.accept()
        threading.Thread(target=lidar_com_cliente_tcp, args=(conn, addr), daemon=True).start()

# === CRUD DE TAREFAS ===

def criar_tarefa():
    global contador_tarefas
    cliente = input("Cliente destino: ").strip()
    if cliente not in clientes:
        print("Cliente não encontrado.")
        return
    tarefa = input("Tarefa: ").strip()
    nova = {"id": contador_tarefas, "cliente": cliente, "tarefa": tarefa}
    tarefas_enviadas.append(nova)
    salvar_tarefas()

    try:
        clientes[cliente].send(tarefa.encode('utf-8'))
        enviar_notificacao_udp(f"[Nova tarefa] {cliente}: {tarefa}")
        print("Tarefa enviada.")
    except Exception as e:
        print(f"[ERRO] Falha ao enviar tarefa para {cliente}: {e}")

    contador_tarefas += 1

def listar_tarefas():
    if not tarefas_enviadas:
        print("Nenhuma tarefa registrada.")
        return
    print("\n=== TAREFAS REGISTRADAS ===")
    for t in tarefas_enviadas:
        print(f"[{t['id']}] Cliente: {t['cliente']} | Tarefa: {t['tarefa']}")

def atualizar_tarefa():
    listar_tarefas()
    try:
        id_alvo = int(input("ID da tarefa a atualizar: "))
        for t in tarefas_enviadas:
            if t["id"] == id_alvo:
                nova = input("Nova tarefa: ").strip()
                t["tarefa"] = nova
                salvar_tarefas()
                if t["cliente"] in clientes:
                    clientes[t["cliente"]].send(nova.encode('utf-8'))
                    enviar_notificacao_udp(f"[Atualização] {t['cliente']}: {nova}")
                print("Tarefa atualizada.")
                return
        print("ID não encontrado.")
    except ValueError:
        print("Entrada inválida.")

def deletar_tarefa():
    listar_tarefas()
    try:
        id_del = int(input("ID da tarefa a deletar: "))
        for t in tarefas_enviadas:
            if t["id"] == id_del:
                tarefas_enviadas.remove(t)
                salvar_tarefas()
                print("Tarefa removida.")
                return
        print("ID não encontrado.")
    except ValueError:
        print("Entrada inválida.")

# === MENU PRINCIPAL ===

def menu_servidor():
    while True:
        print("\n====== MENU DO SERVIDOR ======")
        print("1 - Listar clientes conectados")
        print("2 - Criar nova tarefa")
        print("3 - Listar tarefas")
        print("4 - Atualizar tarefa")
        print("5 - Deletar tarefa")
        print("6 - Sair")
        opcao = input("Escolha: ").strip()

        if opcao == "1":
            if clientes:
                print("\nClientes conectados:")
                for c in clientes:
                    print(f"- {c}")
            else:
                print("Nenhum cliente conectado.")
        elif opcao == "2":
            criar_tarefa()
        elif opcao == "3":
            listar_tarefas()
        elif opcao == "4":
            atualizar_tarefa()
        elif opcao == "5":
            deletar_tarefa()
        elif opcao == "6":
            print("Encerrando servidor...")
            os._exit(0)
        else:
            print("Opção inválida.")

# === INÍCIO DO PROGRAMA ===

if __name__ == "__main__":
    threading.Thread(target=iniciar_servidor_tcp, daemon=True).start()
    menu_servidor()