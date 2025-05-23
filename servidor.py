import socket
import threading
import json
import os

HOST = '0.0.0.0'
PORT_TCP = 5000
PORT_UDP = 6000
BROADCAST_IP = '255.255.255.255'
ARQUIVO_TAREFAS = 'tarefas.json'

clientes = {}  # dicionário: nome_cliente -> socket
tarefas_enviadas = []  # tarefas com id, cliente, tarefa
contador_tarefas = 1    # contador incremental de IDs

# Carrega tarefas do JSON
if os.path.exists(ARQUIVO_TAREFAS):
    with open(ARQUIVO_TAREFAS, 'r') as f:
        tarefas_carregadas = json.load(f)
        if tarefas_carregadas:
            tarefas_enviadas.extend(tarefas_carregadas) # Adiciona tarefas carregadas
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
        # É necessário vincular o socket UDP a uma porta para enviar broadcast em algumas configurações
        # udp_socket.bind(('', 0)) # Porta 0 permite que o SO escolha uma porta livre
        udp_socket.sendto(mensagem.encode('utf-8'), (BROADCAST_IP, PORT_UDP))
        udp_socket.close()
    except Exception as e:
        print(f"[ERRO-UDP] Falha ao enviar notificação UDP: {e}")

# Lida com clientes TCP e processa comandos
def lidar_com_cliente_tcp(conn, addr):
    global contador_tarefas # Permite modificar o contador globalmente
    nome_cliente = "Desconhecido" # Valor padrão para caso o cliente não envie o nome

    try:
        nome_cliente = conn.recv(1024).decode().strip()
        if not nome_cliente:
            print(f"[ERRO] Cliente de {addr} não enviou nome. Conexão fechada.")
            conn.close()
            return

        # Verifica se o nome já está em uso
        if nome_cliente in clientes:
            conn.send("ERRO: Nome de usuário já em uso. Escolha outro nome.".encode())
            print(f"[ALERTA] Tentativa de conexão com nome duplicado: {nome_cliente} de {addr}")
            conn.close()
            return
            
        clientes[nome_cliente] = conn
        print(f"[TCP] {nome_cliente} conectado de {addr}")
        conn.send(f"Bem-vindo, {nome_cliente}! Conectado ao servidor.".encode())

        while True:
            dados = conn.recv(1024).decode()
            if not dados:
                break # Cliente desconectou

            print(f"[TCP-RECEBIDO] De {nome_cliente}: {dados}")
            partes = dados.split('|')
            comando = partes[0]

            resposta = "Comando inválido ou erro no processamento."

            if comando == "LISTAR_CLIENTES":
                if clientes:
                    lista_nomes = "\n".join(clientes.keys())
                    resposta = f"Clientes conectados:\n{lista_nomes}"
                else:
                    resposta = "Nenhum cliente conectado no momento."
                conn.send(resposta.encode())

            elif comando == "CRIAR_TAREFA":
                if len(partes) >= 3:
                    titulo = partes[1]
                    descricao = partes[2]
                    
                    nova_tarefa = {
                        "id": contador_tarefas,
                        "cliente_associado": nome_cliente, # Tarefa associada ao cliente que a criou
                        "titulo": titulo,
                        "descricao": descricao,
                        "status": "pendente" # Exemplo de campo de status
                    }
                    tarefas_enviadas.append(nova_tarefa)
                    salvar_tarefas()
                    contador_tarefas += 1
                    resposta = f"Tarefa '{titulo}' criada com ID {nova_tarefa['id']}."
                    conn.send(resposta.encode())
                    # Notifica todos os clientes via UDP
                    enviar_notificacao_udp(f"[NOVA TAREFA] Criada por {nome_cliente}: '{titulo}' (ID: {nova_tarefa['id']})")
                else:
                    resposta = "Formato CRIAR_TAREFA inválido. Use: CRIAR_TAREFA|titulo|descricao"
                    conn.send(resposta.encode())

            elif comando == "LISTAR_TAREFAS":
                if not tarefas_enviadas:
                    resposta = "Nenhuma tarefa registrada."
                else:
                    tarefas_str = ["\n=== TAREFAS REGISTRADAS ==="]
                    for t in tarefas_enviadas:
                        tarefas_str.append(f"ID: {t['id']} | Criador: {t.get('cliente_associado', 'N/A')} | Título: {t['titulo']} | Descrição: {t['descricao']} | Status: {t.get('status', 'N/A')}")
                    resposta = "\n".join(tarefas_str)
                conn.send(resposta.encode())

            elif comando == "ATUALIZAR_TAREFA":
                if len(partes) >= 4:
                    try:
                        id_tarefa = int(partes[1])
                        novo_titulo = partes[2]
                        nova_desc = partes[3]
                        
                        tarefa_encontrada = False
                        for t in tarefas_enviadas:
                            if t["id"] == id_tarefa:
                                t["titulo"] = novo_titulo
                                t["descricao"] = nova_desc
                                # t["status"] = "atualizada" # Opcional: atualizar status
                                salvar_tarefas()
                                resposta = f"Tarefa ID {id_tarefa} atualizada."
                                conn.send(resposta.encode())
                                enviar_notificacao_udp(f"[TAREFA ATUALIZADA] ID {id_tarefa} por {nome_cliente}: '{novo_titulo}'")
                                tarefa_encontrada = True
                                break
                        if not tarefa_encontrada:
                            resposta = f"Tarefa com ID {id_tarefa} não encontrada."
                            conn.send(resposta.encode())
                    except ValueError:
                        resposta = "ID da tarefa deve ser um número."
                        conn.send(resposta.encode())
                else:
                    resposta = "Formato ATUALIZAR_TAREFA inválido. Use: ATUALIZAR_TAREFA|id|novo_titulo|nova_desc"
                    conn.send(resposta.encode())

            elif comando == "DELETAR_TAREFA":
                if len(partes) >= 2:
                    try:
                        id_tarefa = int(partes[1])
                        tarefa_removida = False
                        for i, t in enumerate(tarefas_enviadas):
                            if t["id"] == id_tarefa:
                                del tarefas_enviadas[i]
                                salvar_tarefas()
                                resposta = f"Tarefa ID {id_tarefa} deletada."
                                conn.send(resposta.encode())
                                enviar_notificacao_udp(f"[TAREFA DELETADA] ID {id_tarefa} por {nome_cliente}.")
                                tarefa_removida = True
                                break
                        if not tarefa_removida:
                            resposta = f"Tarefa com ID {id_tarefa} não encontrada."
                            conn.send(resposta.encode())
                    except ValueError:
                        resposta = "ID da tarefa deve ser um número."
                        conn.send(resposta.encode())
                else:
                    resposta = "Formato DELETAR_TAREFA inválido. Use: DELETAR_TAREFA|id"
                    conn.send(resposta.encode())
            
            else:
                resposta = "Comando desconhecido."
                conn.send(resposta.encode())

    except ConnectionResetError:
        print(f"[INFO] Cliente {nome_cliente} de {addr} desconectou abruptamente.")
    except Exception as e:
        print(f"[ERRO] Falha na conexão com {nome_cliente} ({addr}): {e}")
    finally:
        conn.close()
        if nome_cliente in clientes:
            del clientes[nome_cliente]
            print(f"[INFO] Cliente removido: {nome_cliente}")


# Inicia o servidor TCP
def iniciar_servidor_tcp():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Permite reuso do endereço
    try:
        tcp_socket.bind((HOST, PORT_TCP))
        tcp_socket.listen()
        print(f"[TCP] Servidor ouvindo em {HOST}:{PORT_TCP}")
        while True:
            conn, addr = tcp_socket.accept()
            threading.Thread(target=lidar_com_cliente_tcp, args=(conn, addr), daemon=True).start()
    except Exception as e:
        print(f"[ERRO-TCP] Não foi possível iniciar o servidor TCP: {e}")
        os._exit(1) # Sai se o servidor TCP não puder iniciar

# === Funções de CRUD (para o menu do servidor) - Mantidas para uso manual ===

def criar_tarefa_manual():
    global contador_tarefas
    print("\n--- Criar Nova Tarefa (Manual do Servidor) ---")
    cliente = input("Nome do cliente para associar a tarefa (deixe vazio para não associar): ").strip()
    if cliente and cliente not in clientes:
        print("Cliente não encontrado ou não conectado. A tarefa será criada, mas não associada a um cliente ativo.")
        cliente = "N/A" # Marca como não associado a um cliente ativo
    elif not cliente:
        cliente = "Servidor" # Tarefa criada pelo servidor diretamente

    titulo = input("Título da tarefa: ").strip()
    descricao = input("Descrição da tarefa: ").strip()

    nova = {
        "id": contador_tarefas,
        "cliente_associado": cliente,
        "titulo": titulo,
        "descricao": descricao,
        "status": "pendente"
    }
    tarefas_enviadas.append(nova)
    salvar_tarefas()
    
    mensagem_notificacao = f"[NOVA TAREFA - MANUAL] Criada pelo {cliente}: '{titulo}' (ID: {nova['id']})"
    enviar_notificacao_udp(mensagem_notificacao)
    print(f"Tarefa '{titulo}' criada com ID {nova['id']}.")
    contador_tarefas += 1

def listar_tarefas_manual():
    if not tarefas_enviadas:
        print("Nenhuma tarefa registrada.")
        return
    print("\n=== TAREFAS REGISTRADAS (Manual do Servidor) ===")
    for t in tarefas_enviadas:
        print(f"ID: {t['id']} | Criador: {t.get('cliente_associado', 'N/A')} | Título: {t['titulo']} | Descrição: {t['descricao']} | Status: {t.get('status', 'N/A')}")

def atualizar_tarefa_manual():
    listar_tarefas_manual()
    if not tarefas_enviadas:
        return
    try:
        id_alvo = int(input("ID da tarefa a atualizar: "))
        tarefa_encontrada = False
        for t in tarefas_enviadas:
            if t["id"] == id_alvo:
                novo_titulo = input(f"Novo título (atual: {t['titulo']}): ").strip()
                nova_desc = input(f"Nova descrição (atual: {t['descricao']}): ").strip()
                
                t["titulo"] = novo_titulo if novo_titulo else t["titulo"]
                t["descricao"] = nova_desc if nova_desc else t["descricao"]
                # t["status"] = "atualizada" # Opcional: atualizar status
                salvar_tarefas()
                print("Tarefa atualizada.")
                enviar_notificacao_udp(f"[TAREFA ATUALIZADA - MANUAL] ID {id_alvo}: '{novo_titulo}'")
                tarefa_encontrada = True
                break
        if not tarefa_encontrada:
            print("ID não encontrado.")
    except ValueError:
        print("Entrada inválida. O ID deve ser um número.")

def deletar_tarefa_manual():
    listar_tarefas_manual()
    if not tarefas_enviadas:
        return
    try:
        id_del = int(input("ID da tarefa a deletar: "))
        tarefa_removida = False
        for i, t in enumerate(tarefas_enviadas):
            if t["id"] == id_del:
                del tarefas_enviadas[i]
                salvar_tarefas()
                print("Tarefa removida.")
                enviar_notificacao_udp(f"[TAREFA DELETADA - MANUAL] ID {id_del}.")
                tarefa_removida = True
                break
        if not tarefa_removida:
            print("ID não encontrado.")
    except ValueError:
        print("Entrada inválida. O ID deve ser um número.")

# === MENU PRINCIPAL DO SERVIDOR ===

def menu_servidor():
    while True:
        print("\n====== MENU DO SERVIDOR ======")
        print("1 - Listar clientes conectados")
        print("2 - Criar nova tarefa (Manual do Servidor)")
        print("3 - Listar tarefas (Manual do Servidor)")
        print("4 - Atualizar tarefa (Manual do Servidor)")
        print("5 - Deletar tarefa (Manual do Servidor)")
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
            criar_tarefa_manual()
        elif opcao == "3":
            listar_tarefas_manual()
        elif opcao == "4":
            atualizar_tarefa_manual()
        elif opcao == "5":
            deletar_tarefa_manual()
        elif opcao == "6":
            print("Encerrando servidor...")
            os._exit(0)
        else:
            print("Opção inválida.")

# === INÍCIO DO PROGRAMA ===

if __name__ == "__main__":
    # Inicia o servidor TCP em uma thread separada
    threading.Thread(target=iniciar_servidor_tcp, daemon=True).start()
    # Inicia o menu do servidor na thread principal
    menu_servidor()