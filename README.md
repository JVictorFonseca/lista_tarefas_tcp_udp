# Projeto de Lista de Tarefas com TCP e UDP

## 🎯 Objetivo da Tarefa

Implementar, por meio de um projeto simples divertido, a transmissão de dados utilizando os protocolos **TCP** e **UDP**, respeitando os seguintes critérios (Tarefa 2 de Dev. Stm. Distribuído):

* O projeto **deve utilizar diretamente** os protocolos TCP e UDP (não pode usar protocolos baseados neles como HTTP ou RTSP).
* Os dois protocolos **devem coexistir** no mesmo projeto.
* O projeto será **apresentado presencialmente**, com código testável.
* O código deve ser publicado em um **repositório no GitHub**.

## 💡 Ideia do Projeto

Uma **lista de tarefas colaborativa**, onde:

* Usuários **cadastram e recebem tarefas** (protocolo TCP);
* Notificações rápidas (como "nova tarefa adicionada") são enviadas para todos os usuários conectados usando **UDP broadcast**.

Isso simula um ambiente simples de trabalho em equipe, como grupos em aplicativos de organização, mas com foco no aprendizado de redes.

## 🧰 Tecnologias e Ferramentas

* **Linguagem:** Python 3
* **Editor:** Visual Studio Code (VS Code)
* **Protocolo TCP:** Comunicação confiável (cliente-servidor)
* **Protocolo UDP:** Notificações em tempo real (broadcast)

## 🧠 Conceitos Envolvidos

* **TCP (Transmission Control Protocol):** garante entrega ordenada e confiável de dados.
* **UDP (User Datagram Protocol):** envia mensagens sem garantia de entrega, mas com menor latência — ideal para notificações.

## 📁 Estrutura do Projeto

```
lista_tarefas_tcp_udp/
├── servidor.py
├── cliente.py
├── tarefas.json
└── README.md
```

## 🖥️ Configuração e Execução no VS Code

### Pré-requisitos

* Python 3 instalado
* VS Code com a extensão Python

### 1. Criar Ambiente do Projeto

```bash
mkdir lista_tarefas_tcp_udp
cd lista_tarefas_tcp_udp
code .
```

### 2. Criar Arquivos

* `servidor.py`: responsável por gerenciar tarefas via TCP e enviar notificações via UDP.
* `cliente.py`: conecta-se ao servidor, envia comandos e recebe tarefas.
* `tarefas.json`: onde as tarefas são salvas.
* `README.md`: explicação do projeto.

### 3. Instalar Dependências (nenhuma biblioteca externa é necessária!)

Usaremos apenas módulos nativos do Python: `socket`, `json`, `threading`, `os`, etc.

## 🚦 Funcionamento

### Comunicação TCP

* Cliente envia uma nova tarefa ao servidor.
* O servidor armazena a tarefa em um arquivo JSON.
* O servidor responde ao cliente com a lista atualizada.

### Comunicação UDP

* Quando uma nova tarefa é adicionada, o servidor envia uma mensagem UDP em **broadcast** para alertar todos os clientes conectados.

## 📜 Exemplo de Interação

1. Cliente: "Adicionar tarefa: Fazer relatório"
2. Servidor (via TCP): Tarefa adicionada com sucesso.
3. Servidor (via UDP): Nova tarefa disponível: "Fazer relatório"
4. Outro cliente (ouvindo via UDP): Recebe notificação sem precisar requisitar nada.

## 🔒 Justificativas Técnicas

* **TCP** garante que a tarefa seja corretamente registrada.
* **UDP** permite alertas rápidos para todos, sem necessidade de conexão direta.


## 🎥 Apresentação

Prepare-se para rodar o `servidor.py` e múltiplos `cliente.py` em terminais diferentes, simulando usuários.

## 📚 Referências do Dia a Dia

* Aplicativos como Trello ou Asana (só que no terminal)
* Grupos do WhatsApp: envio da tarefa = TCP, notificação para o grupo = UDP

## ✅ Conclusão

Requisitos da tarefa que foram cumpridos:

* Usa **TCP e UDP de forma direta e justificada**;
* Permite **execução local simples** e testes em rede;
* É fácil de apresentar e compreender, mesmo por iniciantes.