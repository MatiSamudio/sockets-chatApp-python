import os
import socket
import threading

HEADER = 64
HOST = os.getenv("CHAT_HOST", "127.0.0.1")  # default local, configurable por env
PORT = int(os.getenv("CHAT_PORT", "5050"))
ADDR = (HOST, PORT)
FORMAT = "UTF-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(ADDR)
except Exception as e:
    print(f"[ERROR] No se pudo conectar al servidor: {e}")
    raise SystemExit(1)

def _send_framed(text: str):
    """Cliente -> Servidor: HEADER(64) + cuerpo."""
    try:
        body = text.encode(FORMAT)
        n = len(body)
        header = str(n).encode(FORMAT)
        if len(header) > HEADER:
            print("[ERROR] Mensaje demasiado largo para el header.")
            return
        header += b" " * (HEADER - len(header))
        client.sendall(header)
        client.sendall(body)
    except Exception as e:
        print(f"[ERROR ENVIO] {e}")

def receiver():
    """Recibir texto plano del servidor y mostrarlo."""
    while True:
        try:
            data = client.recv(4096)
            if not data:
                print("[INFO] Conexión cerrada por el servidor.")
                break
            print(data.decode(FORMAT), end="")  # server ya envía \n
        except Exception as e:
            print(f"[ERROR RECEPCION] {e}")
            break

def sender():
    """Leer input del usuario y enviar (framing)."""
    # Registro de username (cliente decide el nombre)
    username = input("Ingresa tu nombre de usuario: ").strip()
    while not username:
        username = input("Ingresa tu nombre de usuario: ").strip()
    _send_framed(username)

    # Sugerir /help localmente
    print("Escribe /help para ver los comandos.\n")

    while True:
        try:
            msg = input("")
            if not msg:
                continue
            _send_framed(msg)
            if msg == DISCONNECT_MESSAGE or msg.strip().lower() == "/quit":
                break
        except (KeyboardInterrupt, EOFError):
            _send_framed(DISCONNECT_MESSAGE)
            break
        except Exception as e:
            print(f"[ERROR INPUT] {e}")
            break

    try:
        client.close()
    except Exception:
        pass

# Lanzar hilos
t_recv = threading.Thread(target=receiver, daemon=True)
t_send = threading.Thread(target=sender, daemon=True)
t_recv.start()
t_send.start()

# Esperar a que termine el hilo de envío
t_send.join()
