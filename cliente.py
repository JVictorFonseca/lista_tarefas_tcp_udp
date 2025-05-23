import socket
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
from queue import Queue
import sys # Importa sys para sys.exit

# --- Configurações de Rede ---
PORT_TCP = 5000
PORT_UDP = 6000

# Variáveis globais para os sockets e nome do cliente
tcp_socket = None
udp_socket = None
client_name = ""
server_host = ""

# Fila para comunicação entre threads de rede e a thread da GUI
message_queue = Queue()

# --- Funções de Rede (Executadas em threads separadas) ---

def escutar_udp():
    """
    Escuta por notificações UDP do servidor em uma thread separada.
    Usa SO_REUSEADDR para permitir múltiplas instâncias do cliente.
    """
    global udp_socket
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Permite que múltiplos sockets se vinculem à mesma porta
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        udp_socket.bind(('', PORT_UDP))
        message_queue.put(f"[INFO] Escutando notificações UDP na porta {PORT_UDP}...")
        while True:
            msg, _ = udp_socket.recvfrom(2048)
            message_queue.put(f"[NOTIFICAÇÃO UDP]: {msg.decode()}")
    except Exception as e:
        message_queue.put(f"[ERRO UDP] Falha ao iniciar escuta UDP: {e}")
    finally:
        # Garante que o socket UDP seja fechado se a thread terminar
        if udp_socket:
            udp_socket.close()
            udp_socket = None

def conectar_tcp(host, port, name):
    """
    Tenta conectar ao servidor TCP.
    Retorna True em caso de sucesso, False caso contrário.
    """
    global tcp_socket, client_name, server_host
    try:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.settimeout(5) # 5 segundos de timeout para conexão
        message_queue.put(f"[INFO] Tentando conectar a {host}:{port}...")
        tcp_socket.connect((host, port))
        
        # Envia o nome do cliente para identificação no servidor
        tcp_socket.send(name.encode())
        response = tcp_socket.recv(1024).decode()
        
        # Verifica se o nome já está em uso ou se há outra mensagem de erro inicial
        if "ERRO: Nome de usuário já em uso" in response:
            message_queue.put(f"[ERRO] {response}")
            tcp_socket.close()
            tcp_socket = None
            return False
        
        message_queue.put(f"[INFO] Conectado ao servidor TCP como {name}.")
        message_queue.put(f"[SERVIDOR] {response}") # Exibe a mensagem de boas-vindas do servidor
        
        client_name = name
        server_host = host
        
        # Inicia a thread para receber mensagens contínuas do servidor via TCP
        threading.Thread(target=receber_mensagens_tcp, daemon=True).start()
        
        return True
    except socket.timeout:
        message_queue.put("[ERRO] Tempo limite de conexão TCP esgotado. Verifique a rede ou se o servidor está respondendo.")
        if tcp_socket: tcp_socket.close()
        tcp_socket = None
        return False
    except ConnectionRefusedError:
        message_queue.put("[ERRO] Conexão TCP recusada. Servidor pode não estar online ou IP/Porta incorretos.")
        if tcp_socket: tcp_socket.close()
        tcp_socket = None
        return False
    except Exception as e:
        message_queue.put(f"[ERRO TCP] Não foi possível conectar ao servidor TCP: {e}")
        if tcp_socket: tcp_socket.close()
        tcp_socket = None
        return False

def receber_mensagens_tcp():
    """
    Recebe mensagens do servidor TCP continuamente em uma thread separada.
    """
    while True:
        try:
            if tcp_socket:
                msg = tcp_socket.recv(4096).decode()
                if not msg: # Servidor fechou a conexão
                    message_queue.put("[INFO] Servidor TCP desconectou.")
                    break
                message_queue.put(f"[RESPOSTA TCP]:\n{msg}")
            else:
                break # Sai do loop se o socket TCP não estiver ativo
        except Exception as e:
            message_queue.put(f"[ERRO RECEBIMENTO TCP] {e}")
            break
    desconectar() # Tenta limpar a conexão na GUI após um erro ou desconexão

def enviar_comando_tcp(comando):
    """
    Envia um comando via socket TCP para o servidor.
    """
    if tcp_socket:
        try:
            tcp_socket.send(comando.encode())
            # Mostra apenas o comando principal no log, sem os parâmetros
            message_queue.put(f"[ENVIADO] {comando.split('|')[0]}...") 
        except Exception as e:
            message_queue.put(f"[ERRO ENVIO TCP] Falha ao enviar comando: {e}")
            desconectar() # Desconecta se houver erro no envio
    else:
        message_queue.put("[AVISO] Não conectado ao servidor TCP. Por favor, conecte-se primeiro.")

def desconectar():
    """
    Fecha as conexões TCP e UDP e atualiza o estado da GUI.
    """
    global tcp_socket, udp_socket, client_name, server_host
    if tcp_socket:
        try:
            # shutdown(SHUT_RDWR) para liberar o socket de leituras/escritas pendentes
            tcp_socket.shutdown(socket.SHUT_RDWR) 
            tcp_socket.close()
            message_queue.put("[INFO] Desconectado do servidor TCP.")
        except Exception as e:
            message_queue.put(f"[ERRO DESCONEXÃO TCP] {e}")
        finally:
            tcp_socket = None
            client_name = ""
            server_host = ""
            # Envia um comando para a fila da GUI para atualizar a interface para o estado desconectado
            message_queue.put("[GUI_UPDATE_DISCONNECTED]")
    else:
        message_queue.put("[AVISO] Nenhuma conexão TCP ativa para desconectar.")
    
    # Garante que o socket UDP também seja fechado, se estiver ativo
    if udp_socket:
        try:
            udp_socket.close()
            message_queue.put("[INFO] Socket UDP fechado.")
        except Exception as e:
            message_queue.put(f"[ERRO FECHAMENTO UDP] {e}")
        finally:
            udp_socket = None

# --- Funções da GUI ---

def process_queue():
    """
    Processa mensagens da fila e atualiza a GUI.
    É chamada periodicamente pela thread principal da GUI.
    """
    while not message_queue.empty():
        msg = message_queue.get()
        if msg == "[GUI_UPDATE_CONNECTED]":
            update_gui_on_connect()
        elif msg == "[GUI_UPDATE_DISCONNECTED]":
            update_gui_on_disconnect()
        else:
            # Insere a mensagem no widget de log e rola para o final
            log_output.insert(tk.END, msg + "\n")
        log_output.see(tk.END) 
    root.after(100, process_queue) # Agenda a próxima chamada

def on_connect_button_click():
    """
    Callback para o botão 'Conectar'. Coleta dados de entrada e inicia a conexão.
    """
    global server_host, client_name
    server_host = ip_entry.get()
    client_name = name_entry.get().strip()

    if not server_host or not client_name:
        messagebox.showwarning("Entrada Inválida", "Por favor, insira o IP do servidor e seu nome de usuário.")
        return

    # Inicia a conexão de rede em uma thread separada para não bloquear a GUI
    threading.Thread(target=lambda: start_network_connections(server_host, client_name), daemon=True).start()

def start_network_connections(host, name):
    """
    Inicia as tentativas de conexão TCP e UDP.
    """
    if conectar_tcp(host, PORT_TCP, name):
        threading.Thread(target=escutar_udp, daemon=True).start()
        # Envia um comando para a fila da GUI para mudar para a tela de comandos
        message_queue.put("[GUI_UPDATE_CONNECTED]")
    # Se conectar_tcp retornar False, a mensagem de erro já foi posta na fila

def update_gui_on_connect():
    """
    Atualiza a GUI para o estado 'conectado': esconde tela de conexão, mostra comandos.
    """
    connect_frame.pack_forget() # Esconde o frame de conexão
    commands_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10) # Mostra o frame de comandos
    status_label.config(text=f"Conectado como: {client_name} @ {server_host}", fg="green")

def update_gui_on_disconnect():
    """
    Atualiza a GUI para o estado 'desconectado': mostra tela de conexão, esconde comandos.
    """
    commands_frame.pack_forget() # Esconde o frame de comandos
    connect_frame.pack(pady=20) # Mostra o frame de conexão novamente
    status_label.config(text="Desconectado", fg="red")
    
    # Limpa as variáveis globais de estado
    global tcp_socket, udp_socket, client_name, server_host
    tcp_socket = None
    udp_socket = None
    client_name = ""
    server_host = ""

# --- Funções de Comando (chamadas pelos botões da GUI) ---

def cmd_listar_clientes():
    enviar_comando_tcp("LISTAR_CLIENTES")

def cmd_criar_tarefa():
    titulo = simpledialog.askstring("Criar Tarefa", "Título da Tarefa:")
    if titulo is None: # Usuário cancelou a caixa de diálogo
        return
    descricao = simpledialog.askstring("Criar Tarefa", "Descrição da Tarefa:")
    if descricao is None: # Usuário cancelou
        return
    if titulo and descricao:
        enviar_comando_tcp(f"CRIAR_TAREFA|{titulo}|{descricao}")
    else:
        messagebox.showwarning("Entrada Inválida", "Título e descrição não podem ser vazios.")

def cmd_listar_tarefas():
    enviar_comando_tcp("LISTAR_TAREFAS")

def cmd_atualizar_tarefa():
    id_tarefa = simpledialog.askstring("Atualizar Tarefa", "ID da tarefa para atualizar:")
    if id_tarefa is None:
        return
    try:
        int(id_tarefa) # Valida se é um número
    except ValueError:
        messagebox.showerror("Erro", "ID da tarefa deve ser um número inteiro.")
        return
        
    novo_titulo = simpledialog.askstring("Atualizar Tarefa", "Novo título:")
    if novo_titulo is None:
        return
    nova_desc = simpledialog.askstring("Atualizar Tarefa", "Nova descrição:")
    if nova_desc is None:
        return

    if id_tarefa and novo_titulo and nova_desc:
        enviar_comando_tcp(f"ATUALIZAR_TAREFA|{id_tarefa}|{novo_titulo}|{nova_desc}")
    else:
        messagebox.showwarning("Entrada Inválida", "ID, novo título e nova descrição não podem ser vazios.")

def cmd_deletar_tarefa():
    id_tarefa = simpledialog.askstring("Deletar Tarefa", "ID da tarefa para deletar:")
    if id_tarefa is None:
        return
    try:
        int(id_tarefa) # Valida se é um número
    except ValueError:
        messagebox.showerror("Erro", "ID da tarefa deve ser um número inteiro.")
        return

    if id_tarefa:
        enviar_comando_tcp(f"DELETAR_TAREFA|{id_tarefa}")
    else:
        messagebox.showwarning("Entrada Inválida", "ID da tarefa não pode ser vazio.")

def on_closing():
    """
    Função chamada ao tentar fechar a janela principal.
    Confirma com o usuário e garante que os sockets sejam fechados.
    """
    if messagebox.askokcancel("Sair", "Tem certeza que deseja sair?"):
        desconectar() # Tenta desconectar graciosamente
        root.destroy() # Fecha a janela Tkinter
        sys.exit(0) # Garante que todos os threads e o processo Python terminem

# --- Configuração da Janela Principal (GUI) ---
root = tk.Tk()
root.title("Cliente TCP/UDP de Tarefas (Interface Gráfica)") # Título da janela para identificação
root.geometry("800x600") # Tamanho inicial da janela

# Frame para a tela de conexão (visível inicialmente)
connect_frame = tk.Frame(root)
connect_frame.pack(pady=20)

tk.Label(connect_frame, text="IP do Servidor:").pack(pady=5)
ip_entry = tk.Entry(connect_frame, width=30)
ip_entry.insert(0, "192.168.9.53") # IP do servidor setado como valor padrão
ip_entry.pack(pady=5)

tk.Label(connect_frame, text="Seu Nome:").pack(pady=5)
name_entry = tk.Entry(connect_frame, width=30)
name_entry.pack(pady=5)

connect_button = tk.Button(connect_frame, text="Conectar", command=on_connect_button_click)
connect_button.pack(pady=10)

# Frame para os comandos (inicialmente oculto)
commands_frame = tk.Frame(root, padx=10, pady=10, bd=2, relief="groove")

# Botões de comando organizados em um frame interno
button_frame = tk.Frame(commands_frame)
button_frame.pack(pady=10)

tk.Button(button_frame, text="Listar Clientes", command=cmd_listar_clientes).grid(row=0, column=0, padx=5, pady=5)
tk.Button(button_frame, text="Criar Tarefa", command=cmd_criar_tarefa).grid(row=0, column=1, padx=5, pady=5)
tk.Button(button_frame, text="Listar Tarefas", command=cmd_listar_tarefas).grid(row=0, column=2, padx=5, pady=5)
tk.Button(button_frame, text="Atualizar Tarefa", command=cmd_atualizar_tarefa).grid(row=1, column=0, padx=5, pady=5)
tk.Button(button_frame, text="Deletar Tarefa", command=cmd_deletar_tarefa).grid(row=1, column=1, padx=5, pady=5)
tk.Button(button_frame, text="Desconectar", command=desconectar).grid(row=1, column=2, padx=5, pady=5)

# Área de log/output com scroll
tk.Label(commands_frame, text="Registro de Eventos:").pack(pady=5)
log_output = scrolledtext.ScrolledText(commands_frame, width=80, height=20, wrap=tk.WORD)
log_output.pack(pady=10)

# Barra de status na parte inferior da janela
status_label = tk.Label(root, text="Desconectado", bd=1, relief=tk.SUNKEN, anchor=tk.W, fg="red")
status_label.pack(side=tk.BOTTOM, fill=tk.X)

# Define a função a ser chamada quando o usuário tentar fechar a janela
root.protocol("WM_DELETE_WINDOW", on_closing)

# Inicia o processamento periódico da fila de mensagens para atualizar a GUI
root.after(100, process_queue)

# Inicia o loop principal de eventos da GUI
root.mainloop()