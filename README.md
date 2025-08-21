# Chat en Tiempo Real (Python) 
---English Below--- 

Aplicación cliente-servidor de chat en consola, desarrollada en Python utilizando sockets y multithreading.  
El sistema permite la comunicación simultánea entre múltiples usuarios dentro de una misma red local, con soporte para comandos básicos.

---

## Flujo general del programa

1. **Servidor (`server.py`)**
   - Se inicia y queda a la escucha de conexiones entrantes en un puerto definido.
   - Cada vez que un cliente se conecta, se crea un hilo independiente para manejar esa sesión.
   - El servidor gestiona:
     - Registro y validación de nombres de usuario.
     - Envío de mensajes a todos los clientes conectados (broadcast).
     - Mensajes privados entre usuarios.
     - Comandos de utilidad (/help, /users, /rename, /quit).
     - Desconexiones limpias de clientes.

2. **Cliente (`client.py`)**
   - Se conecta al servidor usando la IP y puerto definidos.
   - El usuario ingresa un nombre válido para identificarse.
   - Dos hilos independientes manejan la comunicación:
     - **Sender**: lee el input del usuario y lo envía al servidor.
     - **Receiver**: escucha los mensajes del servidor y los muestra en consola.
   - El cliente puede:
     - Enviar mensajes a todos.
     - Enviar privados con `/msg`.
     - Cambiar su nombre con `/rename`.
     - Salir con `/quit` o `Ctrl+C`.

---

## Estructura del proyecto
```
├── server.py # Servidor del chat
├── client.py # Cliente del chat
└── README.md # Documentación
```
---

## Requisitos

- Python 3.9 o superior.  
- No requiere librerías externas (solo la librería estándar de Python).

---

## Uso

### 1. Iniciar el servidor
En la máquina que actuará como servidor:

```bash
CHAT_HOST=0.0.0.0 CHAT_PORT=5050 python server.py
```
## Conectarse desde un cliente

En la misma máquina (localhost):

python client.py

Desde otra máquina en la misma LAN (reemplazar con la IP del servidor):

CHAT_HOST=192.168.X.X CHAT_PORT=5050 python client.py

# Real-Time Chat (Python)

Console-based client-server chat application, developed in Python using sockets and multithreading.  
The system enables simultaneous communication between multiple users within the same local network, with support for basic commands.

---

## General Flow

1. **Server (`server.py`)**
   - Starts and listens for incoming connections on a given port.
   - Each client connection is handled in a separate thread.
   - The server manages:
     - User registration and validation.
     - Broadcasting messages to all connected clients.
     - Private messaging between users.
     - Utility commands (/help, /users, /rename, /quit).
     - Clean client disconnections.

2. **Client (`client.py`)**
   - Connects to the server using the defined IP and port.
   - User enters a valid username for identification.
   - Two independent threads handle communication:
     - **Sender**: reads user input and sends it to the server.
     - **Receiver**: listens for messages from the server and displays them.
   - The client can:
     - Send messages to everyone.
     - Send private messages with `/msg`.
     - Change username with `/rename`.
     - Quit with `/quit` or `Ctrl+C`.

---

## Project Structure
```
├── server.py # Chat server
├── client.py # Chat client
└── README.md # Documentation
```

---

## Requirements

- Python 3.9 or higher.  
- No external libraries required (only Python standard library).

---

## Usage

### 1. Start the server
On the machine acting as server:

```bash
CHAT_HOST=0.0.0.0 CHAT_PORT=5050 python server.py
```
## Connect from a client

On the same machine (localhost):

python client.py

From another machine on the same LAN (replace with the server’s IP):

CHAT_HOST=192.168.X.X CHAT_PORT=5050 python client.py
