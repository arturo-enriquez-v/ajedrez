#!/usr/bin/env python3
"""
Módulo de Partidas Multijugador en Red Local (LAN).
Permite crear salas protegidas con contraseña (Host) o unirse a salas existentes (Cliente),
con sincronización en tiempo real de jugadas, chat en terminal, detección automática de IP local
y soporte completo para todas las personalizaciones visuales (temas, estilos de piezas, tamaños).
"""

import sys
import os
import time
import socket
import threading
import queue
import json
import datetime
import random
import chess

from board_view import render_game_view, clear_screen, THEMES, PIECE_SETS, BOARD_SIZES
from move_parser import parse_move, san_to_spanish, get_legal_moves_list
from game import (
    choose_piece_style_in_game,
    choose_theme_in_game,
    choose_board_size_in_game,
    show_legal_moves,
    save_game_to_pgn
)

DEFAULT_PORT = 5050

def get_local_ip() -> str:
    """Detecta la dirección IP local de la máquina en la red Wi-Fi o Ethernet."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Dirección de difusión o prueba que no requiere conexión real
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

class NetworkSession:
    """Gestiona la comunicación por socket TCP bidireccional mediante mensajes JSON delimitados por saltos de línea."""
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.incoming_queue = queue.Queue()
        self.running = True
        self.send_lock = threading.Lock()
        self.recv_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.recv_thread.start()

    def _listen_loop(self):
        try:
            sock_file = self.sock.makefile("r", encoding="utf-8")
            while self.running:
                line = sock_file.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    self.incoming_queue.put(data)
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass
        finally:
            self.running = False
            self.incoming_queue.put({"type": "disconnect"})

    def send(self, data: dict) -> bool:
        """Envía un diccionario serializado en JSON al otro jugador de manera segura entre hilos."""
        if not self.running:
            return False
        try:
            raw = (json.dumps(data, ensure_ascii=False) + "\n").encode("utf-8")
            with self.send_lock:
                self.sock.sendall(raw)
            return True
        except Exception:
            self.running = False
            return False

    def poll_message(self, timeout: float = 0.0) -> dict | None:
        """Extrae el siguiente mensaje recibido de la cola si existe."""
        try:
            return self.incoming_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self):
        """Cierra el socket y finaliza la sesión limpiamente."""
        self.running = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass

def host_room_interactive(port: int = DEFAULT_PORT):
    """
    Guía interactiva para crear una sala multijugador local como anfitrión (Host).
    Solicita nombre, contraseña, color y espera a que el rival se conecte.
    """
    clear_screen()
    local_ip = get_local_ip()

    print("\033[1;36m╔═══════════════════════════════════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║               👑 CREAR SALA MULTIJUGADOR LOCAL (HOST)                 ║\033[0m")
    print("\033[1;36m╠═══════════════════════════════════════════════════════════════════════╣\033[0m")
    print(f"  Tu dirección IP en la red local: \033[1;93m{local_ip}\033[0m")
    print("\033[1;36m╚═══════════════════════════════════════════════════════════════════════╝\033[0m\n")

    # 1. Nombre de usuario
    default_name = os.environ.get("USER", "Anfitrión")
    try:
        player_name = input(f"Tu nombre/apodo [\033[1;32m{default_name}\033[0m]: ").strip() or default_name
    except (KeyboardInterrupt, EOFError):
        return None

    # 2. Contraseña de la sala
    while True:
        try:
            room_pass = input("Establece la contraseña de la sala (mínimo 3 caracteres): ").strip()
            if len(room_pass) >= 3:
                break
            print("\033[91mLa contraseña debe tener al menos 3 caracteres.\033[0m")
        except (KeyboardInterrupt, EOFError):
            return None

    # 3. Elección de color
    print("\n\033[1;34mElige tu color:\033[0m")
    print("  [\033[1;32m1\033[0m] Blancas (Juegas primero)")
    print("  [\033[1;32m2\033[0m] Negras  (Rival juega primero)")
    print("  [\033[1;32m3\033[0m] Aleatorio (Sorteo 🎲)")
    while True:
        try:
            c_choice = input("Selecciona [1-3, defecto 1]: ").strip()
            if c_choice in ("", "1"):
                host_color = chess.WHITE
                break
            elif c_choice == "2":
                host_color = chess.BLACK
                break
            elif c_choice == "3":
                host_color = random.choice([chess.WHITE, chess.BLACK])
                break
            print("\033[91mOpción inválida. Elige 1, 2 o 3.\033[0m")
        except (KeyboardInterrupt, EOFError):
            return None

    # Crear socket servidor
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_sock.bind(("0.0.0.0", port))
        server_sock.listen(1)
        server_sock.settimeout(0.5)
    except Exception as e:
        print(f"\n\033[91mError al abrir el puerto {port}: {e}\033[0m")
        input("Presiona Enter para continuar...")
        return None

    clear_screen()
    print("\033[1;32m╔═══════════════════════════════════════════════════════════════════════╗\033[0m")
    print("\033[1;32m║                  ★ SALA CREADA: ESPERANDO AL RIVAL                    ║\033[0m")
    print("\033[1;32m╠═══════════════════════════════════════════════════════════════════════╣\033[0m")
    print(f"║  \033[1;37mTu IP Local:\033[0m        \033[1;93m{local_ip:<46}\033[0m \033[1;32m║\033[0m")
    print(f"║  \033[1;37mPuerto:\033[0m          \033[1;93m{port:<46}\033[0m \033[1;32m║\033[0m")
    print(f"║  \033[1;37mContraseña:\033[0m      \033[1;93m{room_pass:<46}\033[0m \033[1;32m║\033[0m")
    print(f"║  \033[1;37mAnfitrión:\033[0m       \033[1;97m{player_name:<46}\033[0m \033[1;32m║\033[0m")
    print("\033[1;32m╠═══════════════════════════════════════════════════════════════════════╣\033[0m")
    print("║  \033[1;36mDile a tu amigo en la misma red que seleccione:\033[0m                     \033[1;32m║\033[0m")
    print("║  \033[92m'Unirse a Sala LAN'\033[0m o ejecute:                                      \033[1;32m║\033[0m")
    print(f"║  \033[96mpython3 main.py --join {local_ip:<43}\033[0m \033[1;32m║\033[0m")
    print("\033[1;32m╚═══════════════════════════════════════════════════════════════════════╝\033[0m")
    print("\nEsperando que el rival se conecte... (Presiona \033[1;31mCtrl+C\033[0m para cancelar)")

    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    idx = 0
    client_conn = None

    while True:
        try:
            sys.stdout.write(f"\r\033[K\033[1;33mBuscando conexión {spinner[idx % len(spinner)]}\033[0m")
            sys.stdout.flush()
            idx += 1
            client_conn, client_addr = server_sock.accept()
            break
        except socket.timeout:
            continue
        except (KeyboardInterrupt, EOFError):
            print("\n\nCreación de sala cancelada.")
            server_sock.close()
            return None

    sys.stdout.write("\r\033[K\033[92m¡Rival detectado! Verificando autenticación...\033[0m\n")
    sys.stdout.flush()

    # Handshake de autenticación
    client_conn.settimeout(5.0)
    try:
        client_file = client_conn.makefile("r", encoding="utf-8")
        line = client_file.readline()
        if not line:
            print("\033[91mEl cliente se desconectó antes de identificarse.\033[0m")
            server_sock.close()
            client_conn.close()
            return None

        auth_req = json.loads(line.strip())
        received_pass = auth_req.get("password", "")
        rival_name = auth_req.get("player_name", "Invitado")

        if received_pass != room_pass:
            # Contraseña incorrecta
            err_resp = {"type": "auth_res", "success": False, "error": "Contraseña de sala incorrecta"}
            client_conn.sendall((json.dumps(err_resp) + "\n").encode("utf-8"))
            client_conn.close()
            server_sock.close()
            print("\n\033[91m✖ Un usuario intentó conectarse con contraseña incorrecta.\033[0m")
            input("Presiona Enter para volver...")
            return None

        # Autenticación exitosa
        client_color_str = "black" if host_color == chess.WHITE else "white"
        host_color_str = "white" if host_color == chess.WHITE else "black"
        auth_resp = {
            "type": "auth_res",
            "success": True,
            "host_name": player_name,
            "your_color": client_color_str,
            "host_color": host_color_str
        }
        client_conn.sendall((json.dumps(auth_resp) + "\n").encode("utf-8"))
        server_sock.close()  # No aceptar más conexiones
        client_conn.settimeout(None)

        session = NetworkSession(client_conn)
        return session, host_color, player_name, rival_name

    except Exception as e:
        print(f"\n\033[91mError durante el handshake con el cliente: {e}\033[0m")
        server_sock.close()
        if client_conn:
            client_conn.close()
        input("Presiona Enter para continuar...")
        return None

def join_room_interactive(preset_ip: str = None, port: int = DEFAULT_PORT):
    """
    Guía interactiva para conectarse a una sala multijugador existente (Cliente).
    Solicita nombre, IP del anfitrión y contraseña de la sala.
    """
    clear_screen()
    print("\033[1;36m╔═══════════════════════════════════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║                  ⚔️  UNIRSE A SALA MULTIJUGADOR LOCAL                  ║\033[0m")
    print("\033[1;36m╚═══════════════════════════════════════════════════════════════════════╝\033[0m\n")

    default_name = os.environ.get("USER", "Jugador 2")
    try:
        player_name = input(f"Tu nombre/apodo [\033[1;32m{default_name}\033[0m]: ").strip() or default_name
    except (KeyboardInterrupt, EOFError):
        return None

    # IP del anfitrión
    default_ip = preset_ip or "127.0.0.1"
    while True:
        try:
            target_ip = input(f"IP del Anfitrión [\033[1;32m{default_ip}\033[0m]: ").strip() or default_ip
            if target_ip:
                break
        except (KeyboardInterrupt, EOFError):
            return None

    # Contraseña de la sala
    while True:
        try:
            room_pass = input("Contraseña de la sala: ").strip()
            if room_pass:
                break
            print("\033[91mDebes ingresar la contraseña establecida por el anfitrión.\033[0m")
        except (KeyboardInterrupt, EOFError):
            return None

    print(f"\nConectando a \033[1;93m{target_ip}:{port}\033[0m...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(6.0)

    try:
        sock.connect((target_ip, port))
    except Exception as e:
        print(f"\n\033[91m✖ No se pudo conectar con el anfitrión en {target_ip}:{port}.\033[0m")
        print(f"Detalle: {e}")
        print("Asegúrate de que el anfitrión tenga la sala creada y estén en la misma red Wi-Fi/LAN.")
        input("\nPresiona Enter para continuar...")
        return None

    # Enviar credenciales
    try:
        auth_req = {"type": "auth", "password": room_pass, "player_name": player_name}
        sock.sendall((json.dumps(auth_req) + "\n").encode("utf-8"))

        sock_file = sock.makefile("r", encoding="utf-8")
        line = sock_file.readline()
        if not line:
            print("\n\033[91m✖ El servidor cerró la conexión inesperadamente.\033[0m")
            sock.close()
            input("Presiona Enter...")
            return None

        auth_res = json.loads(line.strip())
        if not auth_res.get("success"):
            err_msg = auth_res.get("error", "Autenticación rechazada")
            print(f"\n\033[91m✖ Falló el acceso: {err_msg}\033[0m")
            sock.close()
            input("\nPresiona Enter para volver...")
            return None

        # Conexión aceptada
        rival_name = auth_res.get("host_name", "Anfitrión")
        my_color = chess.WHITE if auth_res.get("your_color") == "white" else chess.BLACK
        sock.settimeout(None)

        print(f"\033[92m✔ ¡Conexión exitosa con {rival_name}!\033[0m Iniciando partida...")
        time.sleep(1.0)

        session = NetworkSession(sock)
        return session, my_color, player_name, rival_name

    except Exception as e:
        print(f"\n\033[91mError de comunicación durante la autenticación: {e}\033[0m")
        sock.close()
        input("Presiona Enter para continuar...")
        return None

def play_network_game(
    session: NetworkSession,
    my_color: chess.Color,
    my_name: str,
    rival_name: str,
    theme_key: str = "verde",
    piece_style: str = "espanol",
    board_size: str = "mediano"
):
    """
    Bucle principal de la partida multijugador LAN en terminal.
    Maneja turnos, sincronización de jugadas validadas, chat en vivo y comandos.
    """
    board = chess.Board()
    last_move = None
    chat_messages = [
        {"time": datetime.datetime.now().strftime("%H:%M"), "sender": "SISTEMA", "text": f"¡Partida iniciada entre {my_name} y {rival_name}!"}
    ]
    draw_offer_pending_by_rival = False

    # Cola para entrada asíncrona de teclado
    stdin_queue = queue.Queue()
    input_thread_running = True

    def stdin_worker():
        while input_thread_running:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                stdin_queue.put(line.strip())
            except Exception:
                break

    input_thread = threading.Thread(target=stdin_worker, daemon=True)
    input_thread.start()

    def redraw(prompt_msg: str = None):
        clear_screen()
        render_game_view(
            board=board,
            player_color=my_color,
            ai_name=rival_name,
            last_move=last_move,
            ai_commentary=None,
            theme_key=theme_key,
            piece_style=piece_style,
            board_size=board_size,
            chat_messages=chat_messages,
            game_mode="lan",
            my_name=my_name
        )
        if prompt_msg:
            sys.stdout.write(prompt_msg)
            sys.stdout.flush()

    # Bucle principal de partida
    while not board.is_game_over() and session.running:
        is_my_turn = (board.turn == my_color)
        if draw_offer_pending_by_rival:
            current_prompt = f"\n\033[1;33m🤝 {rival_name} te ofrece tablas. ¿Aceptas? (escribe 'si' o 'no'): \033[0m"
        elif is_my_turn:
            current_prompt = "\n\033[1;32mTu jugada (ej. e4, Cf3, 'c hola' o 'ayuda'): \033[0m"
        else:
            current_prompt = f"\n\033[1;33m[Turno de {rival_name}] Escribe 'c <mensaje>' para chatear: \033[0m"

        redraw(current_prompt)

        # Esperar jugada local o mensaje de red
        turn_action_done = False
        while not turn_action_done and session.running:
            # 1. Verificar mensajes entrantes de red
            msg = session.poll_message(timeout=0.1)
            if msg:
                m_type = msg.get("type")

                if m_type == "move":
                    uci_str = msg.get("uci")
                    try:
                        move = chess.Move.from_uci(uci_str)
                        if move in board.legal_moves:
                            board.push(move)
                            last_move = move
                            turn_action_done = True
                            break
                    except Exception:
                        pass

                elif m_type == "chat":
                    chat_messages.append({
                        "time": msg.get("time", datetime.datetime.now().strftime("%H:%M")),
                        "sender": msg.get("sender", rival_name),
                        "text": msg.get("text", "")
                    })
                    redraw(current_prompt)

                elif m_type == "draw_offer":
                    draw_offer_pending_by_rival = True
                    chat_messages.append({
                        "time": datetime.datetime.now().strftime("%H:%M"),
                        "sender": "SISTEMA",
                        "text": f"{rival_name} te ha ofrecido tablas."
                    })
                    current_prompt = f"\n\033[1;33m🤝 {rival_name} te ofrece tablas. ¿Aceptas? (escribe 'si' o 'no'): \033[0m"
                    redraw(current_prompt)

                elif m_type == "draw_response":
                    accepted = msg.get("accepted", False)
                    if accepted:
                        chat_messages.append({
                            "time": datetime.datetime.now().strftime("%H:%M"),
                            "sender": "SISTEMA",
                            "text": f"¡{rival_name} aceptó las tablas! Partida empatada."
                        })
                        redraw()
                        input("\nPresiona Enter para finalizar...")
                        session.close()
                        return
                    else:
                        chat_messages.append({
                            "time": datetime.datetime.now().strftime("%H:%M"),
                            "sender": "SISTEMA",
                            "text": f"{rival_name} rechazó la oferta de tablas."
                        })
                        redraw(current_prompt)

                elif m_type == "resign":
                    chat_messages.append({
                        "time": datetime.datetime.now().strftime("%H:%M"),
                        "sender": "SISTEMA",
                        "text": f"¡{rival_name} se ha rendido! ¡Has ganado la partida! 🏆"
                    })
                    redraw()
                    print(f"\n\033[92m¡Victoria! {rival_name} ha abandonado la partida.\033[0m")
                    save_game_to_pgn(board, my_color, rival_name, "1-0" if my_color == chess.WHITE else "0-1")
                    input("\nPresiona Enter para continuar...")
                    session.close()
                    return

                elif m_type == "disconnect":
                    chat_messages.append({
                        "time": datetime.datetime.now().strftime("%H:%M"),
                        "sender": "SISTEMA",
                        "text": f"{rival_name} se ha desconectado de la sala."
                    })
                    redraw()
                    print(f"\n\033[91m✖ El rival ({rival_name}) se ha desconectado.\033[0m")
                    input("\nPresiona Enter para salir...")
                    session.close()
                    return

            # 2. Verificar entrada del usuario local
            try:
                user_raw = stdin_queue.get_nowait()
            except queue.Empty:
                continue

            if not user_raw:
                continue

            # Respuesta a oferta de tablas pendiente
            if draw_offer_pending_by_rival:
                ans = user_raw.lower().strip()
                if ans in ("s", "si", "sí", "y", "yes", "aceptar"):
                    session.send({"type": "draw_response", "accepted": True})
                    chat_messages.append({
                        "time": datetime.datetime.now().strftime("%H:%M"),
                        "sender": "SISTEMA",
                        "text": "Has aceptado las tablas. Partida empatada."
                    })
                    redraw()
                    input("\nPresiona Enter para finalizar...")
                    session.close()
                    return
                elif ans in ("n", "no", "rechazar"):
                    session.send({"type": "draw_response", "accepted": False})
                    draw_offer_pending_by_rival = False
                    chat_messages.append({
                        "time": datetime.datetime.now().strftime("%H:%M"),
                        "sender": "SISTEMA",
                        "text": "Rechazaste la oferta de tablas."
                    })
                    current_prompt = "\n\033[1;32mTu jugada (ej. e4, Cf3, 'c hola'): \033[0m" if is_my_turn else f"\n\033[1;33m[Turno de {rival_name}] Escribe 'c <mensaje>': \033[0m"
                    redraw(current_prompt)
                    continue

            # Chat en la sala (prefijos: 'c ', '/c ', 'chat ')
            if user_raw.startswith(("c ", "C ", "/c ", "/C ", "chat ", "CHAT ")):
                parts = user_raw.split(" ", 1)
                if len(parts) > 1 and parts[1].strip():
                    msg_txt = parts[1].strip()
                    now_str = datetime.datetime.now().strftime("%H:%M")
                    session.send({"type": "chat", "sender": my_name, "text": msg_txt, "time": now_str})
                    chat_messages.append({"time": now_str, "sender": my_name, "text": msg_txt})
                redraw(current_prompt)
                continue

            cmd = user_raw.lower().strip()

            # Comandos de personalización visual en tiempo real
            if cmd in ("tamano", "tamaño", "size"):
                new_size = choose_board_size_in_game(board_size)
                board_size = new_size
                redraw(current_prompt)
                continue

            if cmd in ("piezas", "estilo", "pieces", "style"):
                new_style = choose_piece_style_in_game(piece_style)
                piece_style = new_style
                redraw(current_prompt)
                continue

            if cmd in ("tema", "theme", "colores"):
                new_theme = choose_theme_in_game(theme_key)
                theme_key = new_theme
                redraw(current_prompt)
                continue

            if cmd in ("tablero", "board", "ver"):
                redraw(current_prompt)
                continue

            if cmd in ("moves", "jugadas", "legal"):
                show_legal_moves(board)
                sys.stdout.write(current_prompt)
                sys.stdout.flush()
                continue

            if cmd in ("tablas", "draw"):
                session.send({"type": "draw_offer"})
                now_str = datetime.datetime.now().strftime("%H:%M")
                chat_messages.append({"time": now_str, "sender": "SISTEMA", "text": "Has ofrecido tablas al rival."})
                redraw(current_prompt)
                continue

            if cmd in ("rendirse", "resign", "abandonar"):
                confirm = input("¿Estás seguro de que deseas rendirte? [s/\033[1;32mN\033[0m]: ").strip().lower()
                if confirm in ("s", "si", "sí", "y"):
                    session.send({"type": "resign"})
                    print(f"\n\033[91mTe has rendido. ¡Victoria para {rival_name}!\033[0m")
                    save_game_to_pgn(board, my_color, rival_name, "0-1" if my_color == chess.WHITE else "1-0")
                    session.close()
                    input("Presiona Enter...")
                    return
                else:
                    redraw(current_prompt)
                    continue

            if cmd in ("salir", "exit", "quit"):
                confirm = input("¿Deseas salir y abandonar la partida? [s/\033[1;32mN\033[0m]: ").strip().lower()
                if confirm in ("s", "si", "sí", "y"):
                    session.send({"type": "resign"})
                    session.close()
                    return
                else:
                    redraw(current_prompt)
                    continue

            # Jugada de ajedrez
            if is_my_turn:
                move = parse_move(board, user_raw)
                if move:
                    san_es = san_to_spanish(move.uci())
                    board.push(move)
                    last_move = move
                    session.send({"type": "move", "uci": move.uci(), "san": san_es})
                    turn_action_done = True
                    break
                else:
                    sys.stdout.write(f"\r\033[K\033[91m✖ Jugada '{user_raw}' no válida o ilegal.\033[0m Escribe 'c <mensaje>' para chat.\n{current_prompt}")
                    sys.stdout.flush()
            else:
                sys.stdout.write(f"\r\033[K\033[93m✖ Aún es el turno de {rival_name}. Para chatear escribe: 'c tu mensaje'\033[0m\n{current_prompt}")
                sys.stdout.flush()

    # Fin de la partida
    redraw()
    if board.is_checkmate():
        winner = my_name if board.turn != my_color else rival_name
        print(f"\n\033[1;92m¡JAQUE MATE! El ganador es: {winner} 🏆\033[0m")
        res_pgn = "1-0" if (winner == my_name and my_color == chess.WHITE) or (winner == rival_name and my_color == chess.BLACK) else "0-1"
        save_game_to_pgn(board, my_color, rival_name, res_pgn)
    elif board.is_stalemate():
        print("\n\033[1;93m¡TABLAS por rey ahogado! Partida empatada.\033[0m")
        save_game_to_pgn(board, my_color, rival_name, "1/2-1/2")
    elif board.is_insufficient_material():
        print("\n\033[1;93m¡TABLAS por material insuficiente! Partida empatada.\033[0m")
        save_game_to_pgn(board, my_color, rival_name, "1/2-1/2")

    input("\nPresiona Enter para volver al menú principal...")
    session.close()
