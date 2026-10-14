#!/usr/bin/env python3
"""
Módulo del bucle principal de la partida de ajedrez.
Gestiona los turnos del jugador humano y de la IA, comandos interactivos,
cambio dinámico de estilo de piezas y temas, deshacer jugadas,
reloj/spinner de pensamiento y guardado de partidas PGN.
"""

import os
import sys
import time
import datetime
import threading
import chess
import chess.pgn

from move_parser import parse_move, get_legal_moves_list, san_to_spanish
from board_view import render_game_view, clear_screen, PIECE_SETS, THEMES, BOARD_SIZES
from gemini_ai import GeminiChessAI

class ThinkingSpinner:
    def __init__(self, message="🤖 Gemini está pensando su jugada"):
        self.message = message
        self.running = False
        self.thread = None

    def _spin(self):
        chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        idx = 0
        while self.running:
            sys.stdout.write(f"\r\033[K\033[1;35m{self.message} {chars[idx % len(chars)]}\033[0m")
            sys.stdout.flush()
            idx += 1
            time.sleep(0.08)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.4)
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

def show_help_modal():
    """Muestra la pantalla de ayuda con explicaciones claras."""
    print("\n\033[1;36m╔═════════════════════════════════════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║                         GUÍA DE COMANDOS Y JUGADAS                      ║\033[0m")
    print("\033[1;36m╠═════════════════════════════════════════════════════════════════════════╣\033[0m")
    print("\033[1;36m║\033[0m \033[1;33mFORMATOS DE JUGADA ACEPTADOS:\033[0m                                           \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • Peón:              \033[92me4\033[0m, \033[92md5\033[0m, \033[92me2e4\033[0m, \033[92me2-e4\033[0m                               \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • Caballo:           \033[92mCf3\033[0m (Español) o \033[92mNf3\033[0m (Inglés), \033[92mg1f3\033[0m                 \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • Alfil:             \033[92mAc4\033[0m (Español) o \033[92mBc4\033[0m (Inglés), \033[92mf1c4\033[0m                 \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • Torre:             \033[92mTe1\033[0m (Español) o \033[92mRe1\033[0m (Inglés)                         \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • Dama / Reina:      \033[92mDh5\033[0m (Español) o \033[92mQh5\033[0m (Inglés)                         \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • Rey:               \033[92mRg1\033[0m (Español) o \033[92mKg1\033[0m (Inglés)                         \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • Capturas:          \033[92mexd5\033[0m, \033[92mCxd5\033[0m, \033[92mAxf7+\033[0m                                   \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • Enroques:          \033[92mO-O\033[0m o \033[92m0-0\033[0m (corto), \033[92mO-O-O\033[0m o \033[92m0-0-0\033[0m (largo)             \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • Coronación:        \033[92me8=D\033[0m (Español), \033[92me8=Q\033[0m (Inglés), \033[92me7e8q\033[0m                 \033[1;36m║\033[0m")
    print("\033[1;36m╠═════════════════════════════════════════════════════════════════════════╣\033[0m")
    print("\033[1;36m║\033[0m \033[1;33mCOMANDOS ESPECIALES:\033[0m                                                    \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • \033[96mtamano\033[0m o \033[96msize\033[0m    Cambia el tamaño del tablero (Mediano, Grande, Compacto)\033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • \033[96mpiezas\033[0m o \033[96mestilo\033[0m  Cambia apariencia de piezas (Español, Inglés, Unicode) \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • \033[96mtema\033[0m o \033[96mcolores\033[0m    Cambia el tema de color del tablero (Verde, Madera...) \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • \033[96mmoves\033[0m o \033[96mjugadas\033[0m   Muestra todas las jugadas legales posibles ahora        \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • \033[96mdeshacer\033[0m o \033[96mundo\033[0m    Retrocede tu última jugada y la de la IA               \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • \033[96mtablero\033[0m o \033[96mboard\033[0m    Vuelve a dibujar el tablero en pantalla                \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • \033[96mfen\033[0m               Muestra la posición actual en notación FEN             \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • \033[96mpgn\033[0m               Muestra el registro de la partida en PGN               \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • \033[96mrendirse\033[0m o \033[96mresign\033[0m   Rinde la partida                                       \033[1;36m║\033[0m")
    print("\033[1;36m║\033[0m  • \033[96msalir\033[0m o \033[96mquit\033[0m        Sale del programa                                      \033[1;36m║\033[0m")
    print("\033[1;36m╚═════════════════════════════════════════════════════════════════════════╝\033[0m")
    input("\nPresiona Enter para continuar...")

def choose_piece_style_in_game(current_style: str = "espanol") -> str:
    """Permite al usuario cambiar el estilo visual de piezas durante la partida."""
    print("\n\033[1;36m╔═════════════════════════════════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║                  CAMBIAR ESTILO VISUAL DE PIEZAS                    ║\033[0m")
    print("\033[1;36m╠═════════════════════════════════════════════════════════════════════╣\033[0m")
    print("  [\033[1;32m1\033[0m] Letras en Español (\033[1;97mP, C, A, T, D, R\033[0m) - \033[92mRecomendado (Evita '?')\033[0m")
    print("  [\033[1;32m2\033[0m] Letras en Español Mayúsculas (\033[1;97mP, C, A, T, D, R\033[0m)")
    print("  [\033[1;32m3\033[0m] Letras Internacionales / FEN (\033[1;97mP, N, B, R, Q, K\033[0m)")
    print("  [\033[1;32m4\033[0m] Símbolos Unicode tradicionales (\033[1;97m♔ ♕ ♖ ♗ ♘ ♙\033[0m)")
    print("  [\033[1;32m5\033[0m] Símbolos Unicode invertidos (\033[1;97m♚ ♛ ♜ ♝ ♞ ♟\033[0m)")
    print("  [\033[1;33mc\033[0m] Cancelar (mantener actual)")
    print("\033[1;36m╚═════════════════════════════════════════════════════════════════════╝\033[0m")

    mapping = {
        "1": "espanol",
        "2": "espanol_mayus",
        "3": "ingles",
        "4": "unicode",
        "5": "unicode_invertido",
    }
    while True:
        try:
            choice = input(f"Selecciona opción [1-5 o 'c', actual: {current_style}]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return current_style

        if choice in ("c", "cancelar", ""):
            return current_style
        if choice in mapping:
            return mapping[choice]
        print("\033[91mOpción inválida. Elige del 1 al 5 o 'c'.\033[0m")

def choose_theme_in_game(current_theme: str = "verde") -> str:
    """Permite al usuario cambiar el tema visual durante la partida."""
    print("\n\033[1;36m╔═════════════════════════════════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║                  CAMBIAR TEMA DE COLOR DEL TABLERO                  ║\033[0m")
    print("\033[1;36m╠═════════════════════════════════════════════════════════════════════╣\033[0m")
    print("  [\033[1;32m1\033[0m] Verde Clásico (Chess.com)")
    print("  [\033[1;32m2\033[0m] Madera Cálida (Lichess)")
    print("  [\033[1;32m3\033[0m] Alto Contraste Neón (Cian y Blanco)")
    print("  [\033[1;32m4\033[0m] Azul Océano (Marino)")
    print("  [\033[1;32m5\033[0m] ASCII Básico (Sin colores 256)")
    print("  [\033[1;33mc\033[0m] Cancelar (mantener actual)")
    print("\033[1;36m╚═════════════════════════════════════════════════════════════════════╝\033[0m")

    mapping = {
        "1": "verde",
        "2": "madera",
        "3": "contraste",
        "4": "azul",
        "5": "ascii"
    }
    while True:
        try:
            choice = input(f"Selecciona opción [1-5 o 'c', actual: {current_theme}]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return current_theme

        if choice in ("c", "cancelar", ""):
            return current_theme
        if choice in mapping:
            return mapping[choice]
        print("\033[91mOpción inválida. Elige del 1 al 5 o 'c'.\033[0m")

def choose_board_size_in_game(current_size: str = "mediano") -> str:
    """Permite al usuario cambiar el tamaño del tablero durante la partida."""
    print("\n\033[1;36m╔═════════════════════════════════════════════════════════════════════╗\033[0m")
    print("\033[1;36m║                  CAMBIAR TAMAÑO DEL TABLERO                         ║\033[0m")
    print("\033[1;36m╠═════════════════════════════════════════════════════════════════════╣\033[0m")
    print("  [\033[1;32m1\033[0m] Mediano (5x1)  - Casillas amplias de 5 col., letras centradas (\033[92mRecomendado\033[0m)")
    print("  [\033[1;32m2\033[0m] Grande (5x2)   - Casillas de 5x2. Proporción cuadrada de ajedrez")
    print("  [\033[1;32m3\033[0m] Compacto (3x1) - Casillas compactas para terminales pequeñas")
    print("  [\033[1;33mc\033[0m] Cancelar (mantener actual)")
    print("\033[1;36m╚═════════════════════════════════════════════════════════════════════╝\033[0m")

    mapping = {
        "1": "mediano",
        "2": "grande",
        "3": "compacto",
    }
    while True:
        try:
            choice = input(f"Selecciona opción [1-3 o 'c', actual: {current_size}]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return current_size

        if choice in ("c", "cancelar", ""):
            return current_size
        if choice in mapping:
            return mapping[choice]
        print("\033[91mOpción inválida. Elige del 1 al 3 o 'c'.\033[0m")

def show_legal_moves(board: chess.Board):
    """Muestra la lista de jugadas legales de forma compacta y ordenada."""
    legal_moves = get_legal_moves_list(board)
    print(f"\n\033[1;33m📋 Jugadas legales disponibles ({len(legal_moves)}):\033[0m")
    formatted = [f"{san_es:8} ({uci})" for uci, san_en, san_es in legal_moves]
    col_width = 18
    num_cols = 4
    for i in range(0, len(formatted), num_cols):
        chunk = formatted[i:i + num_cols]
        line = "   ".join([f"{item:<{col_width}}" for item in chunk])
        print(f"  {line}")
    print("")

def save_game_to_pgn(board: chess.Board, player_color: chess.Color, ai_name: str, result_str: str = "*"):
    """Guarda la partida actual en formato PGN en el directorio partidas_guardadas/."""
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "partidas_guardadas")
    os.makedirs(folder, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(folder, f"partida_{timestamp}.pgn")

    game = chess.pgn.Game.from_board(board)
    game.headers["Event"] = "Partida en Terminal vs Gemini IA"
    game.headers["Site"] = "Terminal Linux"
    game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
    game.headers["White"] = "Humano" if player_color == chess.WHITE else ai_name
    game.headers["Black"] = ai_name if player_color == chess.WHITE else "Humano"
    game.headers["Result"] = result_str

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(game))
        print(f"\033[92m✔ Partida guardada exitosamente en:\033[0m {filepath}")
        return filepath
    except Exception as e:
        print(f"\033[91m✖ Error al guardar archivo PGN: {e}\033[0m")
        return None

def get_history_pgn_string(board: chess.Board) -> str:
    """Genera una cadena compacta con las jugadas realizadas (ej. 1. e4 e5 2. Nf3)."""
    game = chess.pgn.Game.from_board(board)
    exporter = chess.pgn.StringExporter(headers=False, variations=False, comments=False)
    return game.accept(exporter).strip()

def play_game(
    ai: GeminiChessAI,
    player_color: chess.Color = chess.WHITE,
    theme_key: str = "verde",
    piece_style: str = "espanol",
    board_size: str = "mediano",
    ai_name: str = "Gemini IA"
):
    """Bucle principal de la partida."""
    board = chess.Board()
    last_move = None
    ai_commentary = "¡Que comience la partida! Buena suerte."

    def redraw():
        render_game_view(
            board=board,
            player_color=player_color,
            ai_name=ai_name,
            last_move=last_move,
            ai_commentary=ai_commentary,
            theme_key=theme_key,
            piece_style=piece_style,
            board_size=board_size
        )

    while not board.is_game_over():
        clear_screen()
        redraw()

        # Determinar de quién es el turno
        if board.turn == player_color:
            # TURNO DEL JUGADOR HUMANO
            while True:
                try:
                    user_input = input("\n\033[1;32mTu jugada (ej. e4, Cf3, o 'ayuda'): \033[0m").strip()
                except (KeyboardInterrupt, EOFError):
                    print("\n\n¿Deseas salir del juego? (s/n): ", end="")
                    try:
                        ans = input().strip().lower()
                        if ans in ("s", "si", "sí", "y"):
                            print("Partida cancelada. ¡Hasta luego!")
                            return
                        else:
                            continue
                    except Exception:
                        return

                if not user_input:
                    continue

                cmd = user_input.lower()

                if cmd in ("ayuda", "help", "?"):
                    show_help_modal()
                    clear_screen()
                    redraw()
                    continue

                if cmd in ("tamano", "tamaño", "size"):
                    new_size = choose_board_size_in_game(board_size)
                    board_size = new_size
                    clear_screen()
                    redraw()
                    continue

                if cmd in ("grande", "big"):
                    board_size = "grande"
                    clear_screen()
                    redraw()
                    continue

                if cmd in ("mediano", "medium"):
                    board_size = "mediano"
                    clear_screen()
                    redraw()
                    continue

                if cmd in ("compacto", "small"):
                    board_size = "compacto"
                    clear_screen()
                    redraw()
                    continue

                if cmd in ("piezas", "estilo", "pieces", "style"):
                    new_style = choose_piece_style_in_game(piece_style)
                    piece_style = new_style
                    clear_screen()
                    redraw()
                    continue

                if cmd in ("tema", "theme", "colores"):
                    new_theme = choose_theme_in_game(theme_key)
                    theme_key = new_theme
                    clear_screen()
                    redraw()
                    continue

                # Atajos rápidos de estilo de piezas
                if cmd in ("espanol", "letras", "spanish"):
                    piece_style = "espanol"
                    clear_screen()
                    redraw()
                    continue

                if cmd in ("ingles", "english", "fen"):
                    piece_style = "ingles"
                    clear_screen()
                    redraw()
                    continue

                if cmd in ("unicode", "simbolos"):
                    piece_style = "unicode"
                    clear_screen()
                    redraw()
                    continue

                if cmd in ("moves", "jugadas", "legal"):
                    show_legal_moves(board)
                    continue

                if cmd in ("tablero", "board", "ver"):
                    clear_screen()
                    redraw()
                    continue

                if cmd in ("fen", "posicion"):
                    print(f"\n\033[96mFEN actual:\033[0m {board.fen()}")
                    continue

                if cmd in ("pgn", "historial"):
                    pgn_str = get_history_pgn_string(board)
                    print(f"\n\033[96mRegistro PGN:\033[0m\n{pgn_str or '(Sin jugadas aún)'}")
                    continue

                if cmd in ("deshacer", "undo", "atras"):
                    if len(board.move_stack) >= 2:
                        board.pop()  # Pop jugada de la IA
                        board.pop()  # Pop jugada del humano
                        last_move = board.move_stack[-1] if board.move_stack else None
                        ai_commentary = "Has retrocedido tu jugada. Intenta una nueva táctica."
                        clear_screen()
                        redraw()
                        break
                    elif len(board.move_stack) == 1 and board.turn != player_color:
                        board.pop()
                        last_move = None
                        ai_commentary = "Jugada deshecha."
                        clear_screen()
                        redraw()
                        break
                    else:
                        print("\033[93mNo hay jugadas previas para deshacer.\033[0m")
                        continue

                if cmd in ("rendirse", "resign", "abandonar"):
                    confirm = input("¿Estás seguro de que quieres rendirte? [s/\033[1;32mN\033[0m]: ").strip().lower()
                    if confirm in ("s", "si", "sí", "y"):
                        print(f"\n\033[91mTe has rendido. ¡Victoria para {ai_name}!\033[0m")
                        save_game_to_pgn(board, player_color, ai_name, "0-1" if player_color == chess.WHITE else "1-0")
                        return
                    else:
                        continue

                if cmd in ("salir", "exit", "quit"):
                    confirm = input("¿Deseas salir del juego? [s/\033[1;32mN\033[0m]: ").strip().lower()
                    if confirm in ("s", "si", "sí", "y"):
                        print("¡Gracias por jugar!")
                        sys.exit(0)
                    else:
                        continue

                # Intentar parsear jugada
                move = parse_move(board, user_input)
                if move:
                    board.push(move)
                    last_move = move
                    break
                else:
                    print(f"\033[91m✖ Jugada '{user_input}' no válida o ilegal.\033[0m Escribe '\033[1;36mmoves\033[0m' para ver opciones, '\033[1;36mpiezas\033[0m' para cambiar letras/iconos, o '\033[1;36mayuda\033[0m'.")

        else:
            # TURNO DE LA IA
            spinner = ThinkingSpinner(f"🤖 {ai_name} está calculando su mejor respuesta")
            spinner.start()

            history_pgn = get_history_pgn_string(board)
            try:
                ai_move, ai_comment = ai.get_move(board, history_pgn)
            finally:
                spinner.stop()

            if ai_move and ai_move in board.legal_moves:
                board.push(ai_move)
                last_move = ai_move
                ai_commentary = ai_comment
            else:
                # Si falló completamente (raro), elegir la primera jugada legal
                moves = list(board.legal_moves)
                if moves:
                    board.push(moves[0])
                    last_move = moves[0]
                    ai_commentary = "Jugada ejecutada."

    # FIN DE LA PARTIDA
    clear_screen()
    ai_commentary = "¡Partida finalizada!"
    redraw()

    print("\n\033[1;33m╔═════════════════════════════════════════════════════════════════════════╗\033[0m")
    result_str = "*"
    if board.is_checkmate():
        winner = "Humano (¡Felicidades!)" if board.turn != player_color else f"{ai_name}"
        result_str = "1-0" if board.turn == chess.BLACK else "0-1"
        print(f"\033[1;33m║\033[0m  \033[1;92m🏆 ¡JAQUE MATE! Ganador: {winner:43}\033[0m \033[1;33m║\033[0m")
    elif board.is_stalemate():
        result_str = "1/2-1/2"
        print("\033[1;33m║\033[0m  \033[1;93m🤝 ¡TABLAS POR AHOGADO! El rey no tiene jugadas legales.           \033[0m \033[1;33m║\033[0m")
    elif board.is_insufficient_material():
        result_str = "1/2-1/2"
        print("\033[1;33m║\033[0m  \033[1;93m🤝 ¡TABLAS POR MATERIAL INSUFICIENTE!                                \033[0m \033[1;33m║\033[0m")
    elif board.is_seventyfive_moves():
        result_str = "1/2-1/2"
        print("\033[1;33m║\033[0m  \033[1;93m🤝 ¡TABLAS POR REGLA DE 75 JUGADAS!                                  \033[0m \033[1;33m║\033[0m")
    elif board.is_fivefold_repetition():
        result_str = "1/2-1/2"
        print("\033[1;33m║\033[0m  \033[1;93m🤝 ¡TABLAS POR QUÍNTUPLE REPETICIÓN!                                \033[0m \033[1;33m║\033[0m")
    else:
        print("\033[1;33m║\033[0m  \033[1;93m🏁 Partida terminada.                                                \033[0m \033[1;33m║\033[0m")
    print("\033[1;33m╚═════════════════════════════════════════════════════════════════════════╝\033[0m")

    # Guardar PGN opcional
    try:
        save_q = input("\n¿Deseas guardar la partida en archivo PGN? [\033[1;32mS\033[0m/n]: ").strip().lower()
        if save_q in ("", "s", "si", "sí", "y", "yes"):
            save_game_to_pgn(board, player_color, ai_name, result_str)
    except (KeyboardInterrupt, EOFError):
        pass
