import socket
import threading
import sys # Importa sys para sys.stdout.flush

# Inserir o IP do Servidor
HOST = 'localhost'  # Use o IP do servidor real se for em rede
PORT_TCP = 5000
PORT_UDP = 6000

# Lida com notificações recebidas via UDP
def escutar_udp():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # ADICIONADO: Permite que múltiplos sockets se vinculem à mesma porta
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        udp_socket.bind(('', PORT_UDP)) # Vincula a todas as interfaces na porta UDP
        print(f"[INFO] Escutando notificações UDP na porta {PORT_UDP}...")
        while True:
            msg, _ = udp_socket.recvfrom(2048) # Aumentado o buffer um pouco
            # Usar sys.stdout.flush() para garantir que a mensagem seja impressa imediatamente
            print(f"\n[NOTIFICAÇÃO UDP]: {msg.decode()}\n> ", end='', flush=True)
            # ou simplesmente: print(f"\n[NOTIFICAÇÃO UDP]: {msg.decode()}")
            # se não quiser o "> " na mesma linha para input
    except Exception as e:
        print(f"[ERRO UDP] Falha ao iniciar escuta UDP: {e}")
    finally:
        if udp_socket:
            udp_socket.close()
            print("[INFO] Socket UDP fechado.")

# Funções para cada comando
def listar_clientes(tcp_socket):
    try:
        tcp_socket.send("LISTAR_CLIENTES".encode())
        resposta = tcp_socket.recv(2048).decode()
        print(f"\nClientes conectados:\n{resposta}")
    except Exception as e:
        print(f"Erro ao listar clientes: {e}")

def criar_tarefa(tcp_socket):
    try:
        titulo = input("Título da tarefa: ")
        descricao = input("Descrição da tarefa: ")
        if not titulo or not descricao:
            print("Título e descrição não podem ser vazios.")
            return
        comando = f"CRIAR_TAREFA|{titulo}|{descricao}"
        tcp_socket.send(comando.encode())
        print(tcp_socket.recv(1024).decode())
    except Exception as e:
        print(f"Erro ao criar tarefa: {e}")

def listar_tarefas(tcp_socket):
    try:
        tcp_socket.send("LISTAR_TAREFAS".encode())
        print(tcp_socket.recv(4096).decode())
    except Exception as e:
        print(f"Erro ao listar tarefas: {e}")

def atualizar_tarefa(tcp_socket):
    try:
        id_tarefa = input("ID da tarefa para atualizar: ")
        if not id_tarefa.isdigit():
            print("ID da tarefa deve ser um número inteiro.")
            return
        novo_titulo = input("Novo título: ")
        nova_desc = input("Nova descrição: ")
        if not novo_titulo or not nova_desc:
            print("Novo título e nova descrição não podem ser vazios.")
            return
        comando = f"ATUALIZAR_TAREFA|{id_tarefa}|{novo_titulo}|{nova_desc}"
        tcp_socket.send(comando.encode())
        print(tcp_socket.recv(1024).decode())
    except Exception as e:
        print(f"Erro ao atualizar tarefa: {e}")

def deletar_tarefa(tcp_socket):
    try:
        id_tarefa = input("ID da tarefa para deletar: ")
        if not id_tarefa.isdigit():
            print("ID da tarefa deve ser um número inteiro.")
            return
        comando = f"DELETAR_TAREFA|{id_tarefa}"
        tcp_socket.send(comando.encode())
        print(tcp_socket.recv(1024).decode())
    except Exception as e:
        print(f"Erro ao deletar tarefa: {e}")

# Inicia escuta UDP em uma thread separada
threading.Thread(target=escutar_udp, daemon=True).start()

# Inicia comunicação TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(5)  # evita travamento total caso o servidor trave
    try:
        s.connect((HOST, PORT_TCP))
    except ConnectionRefusedError:
        print("Não foi possível conectar ao servidor TCP. Verifique se o servidor está online e o IP/Porta estão corretos.")
        sys.exit(1) # Sai do programa
    except socket.timeout:
        print("Tempo limite de conexão TCP esgotado. Verifique a rede ou se o servidor está respondendo.")
        sys.exit(1)
    except Exception as e:
        print(f"Ocorreu um erro ao conectar ao servidor TCP: {e}")
        sys.exit(1)

    nome = input("Digite seu nome de usuário: ")
    s.send(nome.encode())  # Envia nome ao servidor para identificação
    
    # Recebe a mensagem de boas-vindas ou erro de nome duplicado do servidor
    try:
        resposta_conexao = s.recv(1024).decode()
        print(f"[SERVIDOR]: {resposta_conexao}")
        if "ERRO: Nome de usuário já em uso" in resposta_conexao:
            print("Encerrando cliente devido ao nome de usuário duplicado.")
            sys.exit(1) # Sai do programa
    except Exception as e:
        print(f"Erro ao receber resposta inicial do servidor: {e}")
        sys.exit(1)

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