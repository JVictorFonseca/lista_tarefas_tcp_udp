import socket
import threading

# Inserir o IP do Servidor
HOST = 'localhost'  # Use o IP do servidor real se for em rede
PORT_TCP = 5000
PORT_UDP = 6000

# Lida com notificações recebidas via UDP
def escutar_udp():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', PORT_UDP))
    while True:
        msg, _ = udp_socket.recvfrom(1024)
        print(f"\n[NOTIFICAÇÃO UDP]: {msg.decode()}\n> ", end='', flush=True)

# Funções para cada comando
def listar_clientes(tcp_socket):
    try:
        tcp_socket.send("LISTAR_CLIENTES".encode())
        resposta = tcp_socket.recv(2048).decode()
        print(f"\nClientes conectados:\n{resposta}")
    except:
        print("Erro ao listar clientes.")

def criar_tarefa(tcp_socket):
    try:
        titulo = input("Título da tarefa: ")
        descricao = input("Descrição da tarefa: ")
        comando = f"CRIAR_TAREFA|{titulo}|{descricao}"
        tcp_socket.send(comando.encode())
        print(tcp_socket.recv(1024).decode())
    except:
        print("Erro ao criar tarefa.")

def listar_tarefas(tcp_socket):
    try:
        tcp_socket.send("LISTAR_TAREFAS".encode())
        print(tcp_socket.recv(4096).decode())
    except:
        print("Erro ao listar tarefas.")

def atualizar_tarefa(tcp_socket):
    try:
        id_tarefa = input("ID da tarefa para atualizar: ")
        novo_titulo = input("Novo título: ")
        nova_desc = input("Nova descrição: ")
        comando = f"ATUALIZAR_TAREFA|{id_tarefa}|{novo_titulo}|{nova_desc}"
        tcp_socket.send(comando.encode())
        print(tcp_socket.recv(1024).decode())
    except:
        print("Erro ao atualizar tarefa.")

def deletar_tarefa(tcp_socket):
    try:
        id_tarefa = input("ID da tarefa para deletar: ")
        comando = f"DELETAR_TAREFA|{id_tarefa}"
        tcp_socket.send(comando.encode())
        print(tcp_socket.recv(1024).decode())
    except:
        print("Erro ao deletar tarefa.")

# Inicia escuta UDP em uma thread separada
threading.Thread(target=escutar_udp, daemon=True).start()

# Inicia comunicação TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(5)  # evita travamento total caso o servidor trave
    try:
        s.connect((HOST, PORT_TCP))
    except:
        print("Não foi possível conectar ao servidor TCP.")
        exit()

    nome = input("Digite seu nome de usuário: ")
    s.send(nome.encode())  # Envia nome ao servidor para identificação

    while True:
        print("\n===== MENU DE COMANDOS =====")
        print("1 - Listar clientes conectados")
        print("2 - Criar nova tarefa")
        print("3 - Listar tarefas")
        print("4 - Atualizar tarefa")
        print("5 - Deletar tarefa")
        print("6 - Sair")
        escolha = input("Escolha uma opção: ")

        if escolha == "1":
            listar_clientes(s)
        elif escolha == "2":
            criar_tarefa(s)
        elif escolha == "3":
            listar_tarefas(s)
        elif escolha == "4":
            atualizar_tarefa(s)
        elif escolha == "5":
            deletar_tarefa(s)
        elif escolha == "6":
            print("Encerrando conexão...")
            break
        else:
            print("Opção inválida.")