import os
import socket 
import threading 
import re 

# Config
HEADER = 64
HOST = os.getenv("CHAT_HOST", "0.0.0.0")  
PORT = int(os.getenv("CHAT_PORT", "5050"))
ADDR = (HOST, PORT)
FORMAT = "UTF-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

clients = []  #lista de sockets
usernames = {}  #conn -> username
name_to_conn = {}  #username -> conn
state_lock = threading.Lock()  #para proteger estructuras compartidas


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)
server.settimeout(1.0)

#utils de envio
def _safe_send(conn, text: str):
    '''Envia texto plano al cliente (server a cliente)'''
    try:
        conn.sendall(text.encode(FORMAT))
    except Exception:
        # si falla el receptor sera limpiado donde corresponda
        pass

def _broadcast_plain(text: str, sender_conn=None):
    """Envía texto plano a todos (opcionalmente excluye al emisor)."""
    with state_lock:
        snapshot = list(clients)
    failed = []
    for c in snapshot:
        if sender_conn is not None and c is sender_conn:
            continue
        try:
            c.sendall(text.encode(FORMAT))
        except Exception:
            failed.append(c)
    if failed:
        for c in failed:
            _remove_client(c)

def _remove_client(conn):
    """Quita al cliente de todas las estructuras y cierra el socket."""
    try:
        conn.close()
    except Exception:
        pass
    with state_lock:
        if conn in clients:
            clients.remove(conn)
        if conn in usernames:
            name = usernames.pop(conn)
            if name_to_conn.get(name) is conn:
                name_to_conn.pop(name, None)

def _recv_exact(conn, n: int):
    """Lee exactamente n bytes o devuelve None si el peer cerró."""
    data = bytearray()
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            return None
        data.extend(chunk)
    return bytes(data)

def _valid_username(name: str) -> bool:
    """Reglas básicas: 3-16 chars, letras/números/_/-, sin espacios."""
    if not (3 <= len(name) <= 16):
        return False
    return re.fullmatch(r"[A-Za-z0-9_-]+", name) is not None

def _username_available(name: str) -> bool:
    with state_lock:
        return name not in name_to_conn


# comandos 
HELP_TEXT = (
    "[COMMANDS]\n"
    "/help                      - ver este listado\n"
    "/users                     - lista de usuarios conectados\n"
    "/msg <user> <mensaje>      - mensaje privado (whisper)\n"
    "/rename                    - cambiar nombre (si esta disponible)\n"
    "/quit                      - salir del chat\n"
)


def _handle_command(conn, username: str, line: str) -> bool:
    '''Procesa comandos. Devuelve False si el cliente debe desconectarse'''
    parts = line.strip().split()
    if not parts:
        return True
    cmd = parts[0].lower()

    if cmd == "/help":
        _safe_send(conn, HELP_TEXT)
        return True

    if cmd == "/users":
        with state_lock:
            users = ", ".join(sorted(name_to_conn.keys()))
        _safe_send(conn,f"[USERS] {users}\n")
        return True

    if cmd == "/quit":
        _safe_send(conn, "Has salido del chat.\n")
        return False

    if cmd == "/rename":
        if len(parts) < 2:
            _safe_send(conn, "[ERROR] Uso: /rename <nuevo_nombre>\n")
            return True
        newname = parts[1]
        if not _valid_username(newname):
            _safe_send(conn, "[ERROR] Nombre invalido. Usa 3-16 chars A-Z a-z 0-9 _ -.\n")
            return True

        if not _username_available(newname):
            _safe_send(conn, "[ERROR] Nombre en uso. elige otro.\n")
            return True

        with state_lock:
            old = username
            name_to_conn.pop(old, None)
            usernames[conn] = newname
            name_to_conn[newname] = conn
            _broadcast_plain(f"[SYSTEM] {old} ahora es {newname}\n")
            return True
            

    if cmd == "/msg":
        if len(parts) < 3:
            _safe_send(conn, "[ERROR] Uso: /msg <usuario> <mensaje>\n")
            return True
        target = parts[1]
        text = " ".join(parts[2:])
        with state_lock:
            tconn = name_to_conn.get(target)
        if not tconn:
            _safe_send(conn, f"[ERROR] Usuario '{target}' no encontrado\n")
            return True
        
        _safe_send(tconn, f"[PM de {username}] {text}\n")
        _safe_send(conn, f"[PM a {target}] {text}\n")
        return True
    
    _safe_send(conn, "[ERROR] Comando no reconocido. Usa /help\n")
    return True


def handle_client(conn, addr):
    with state_lock:
        clients.append(conn)

    # Registro de username
    _safe_send(conn, "[SYSTEM] Bienvenido Ingresa un Nombre de usuario (3-16, A-Z a-z 0-9 _ -):\n")
    username = None
    while username is None:
        #header 
        header_raw = _recv_exact(conn, HEADER)
        if header_raw is None:
            _remove_client(conn)
            return
        header = header_raw.decode(FORMAT).strip()
        if not header.isdigit():
            _safe_send(conn, "[ERROR] Header invalido. Vuelve a intentar tu nombre.\n")
            continue
        n = int(header)

        #cuerpo 
        body = _recv_exact(conn, n)
        if body is None:
            _remove_client(conn)
            return
        proposed = body.decode(FORMAT).strip()

        #validar
        if not _valid_username(proposed):
            _safe_send(conn, "[ERROR] Nombre invalido. Intenta otro:\n")
            continue
        if not _username_available(proposed):
            _safe_send(conn, "[ERROR] Nombre en uso. Intenta otro:\n")
            continue

        with state_lock:
            usernames[conn] = proposed
            name_to_conn[proposed] = conn
        username = proposed

    print(f"[NUEVA CONEXION] {addr} -> {username}")
    _broadcast_plain(f"[SYSTEM] {username} se ha unido al chat.\n")

    # Chat loop
    while True:
        try:
            
            header_raw = _recv_exact(conn, HEADER)
            if header_raw is None:
                break
            header = header_raw.decode(FORMAT).strip()
            if not header.isdigit():
                _safe_send(conn, "[ERROR] Header inválido.\n")
                continue
            n = int(header)

            body = _recv_exact(conn, n)
            if body is None:
                break
            msg = body.decode(FORMAT)

            # Comandos y salida
            if msg == DISCONNECT_MESSAGE:
                _safe_send(conn, "Has sido desconectado.\n")
                break
            if msg.startswith("/"):
                if not _handle_command(conn, username, msg):
                    break
                continue

            # Mensaje normal -> broadcast
            print(f"[{username}] {msg}")
            _broadcast_plain(f"[{username}] {msg}\n", sender_conn=conn)

        except Exception as e:
            print(f"[ERROR] {username or addr}: {e}")
            break

    # Limpieza y aviso de salida
    _remove_client(conn)
    if username:
        _broadcast_plain(f"[SYSTEM] {username} se ha desconectado.\n")
    print(f"[CIERRE] conexión cerrada con {addr}")


def start():
    server.listen()
    print(f"[LISTENING] Servidor en {HOST}:{PORT}")
    try:
        while True:
            try:
                conn, addr = server.accept()
            except socket.timeout:
                continue  # volver a chequear Ctrl+C
            except OSError:
                break  # socket cerrado durante el shutdown

            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
            print(f"[CONEXIONES ACTIVAS] {threading.active_count() - 1}")
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Ctrl+C recibido, cerrando...")
    finally:
        # cerrar clientes
        with state_lock:
            snapshot = list(clients)
        for c in snapshot:
            try:
                c.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                c.close()
            except Exception:
                pass
        # cerrar servidor
        try:
            server.close()
        except Exception:
            pass
        print("[SHUTDOWN] Listo.")



print("[INICIANDO SERVIDOR] Servidor")
start()
