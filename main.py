#!/usr/bin/env python3
"""
Punto de entrada principal para el Ajedrez en Terminal con Google AI Studio (Gemini).
Permite configurar partida, validar API key, elegir color, personalidad,
tema visual y estilo de piezas (letras en español para evitar signos de interrogación '?').
"""

import sys
import random
import argparse
import chess

from config import get_or_prompt_api_key, validate_api_key, load_env_file
from gemini_ai import GeminiChessAI, PERSONALITIES
from game import play_game
from network_game import host_room_interactive, join_room_interactive, play_network_game

BANNER = r"""
\033[1;36m
  █████╗      ██╗███████╗██████╗ ██████╗ ███████╗███████╗
 ██╔══██╗     ██║██╔════╝██╔══██╗██╔══██╗██╔════╝╚══███╔╝
 ███████║     ██║█████╗  ██║  ██║██████╔╝█████╗    ███╔╝ 
 ██╔══██║██   ██║██╔══╝  ██║  ██║██╔══██╗██╔══╝   ███╔╝  
 ██║  ██║╚█████╔╝███████╗██████╔╝██║  ██║███████╗███████╗
 ╚═╝  ╚═╝ ╚════╝ ╚══════╝╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝
\033[0m
 \033[1;33m═══  AJEDREZ EN TERMINAL CON INTELIGENCIA ARTIFICIAL DE GOOGLE  ═══\033[0m
"""

def print_banner():
    print(BANNER)

def choose_color():
    """Permite al usuario elegir jugar con Blancas, Negras o Aleatorio."""
    print("\n\033[1;34mElige tu color:\033[0m")
    print("  [\033[1;32m1\033[0m] Blancas - Juegas primero (Recomendado)")
    print("  [\033[1;32m2\033[0m] Negras  - Gemini juega primero (Tablero invertido)")
    print("  [\033[1;32m3\033[0m] Aleatorio (Sorteo 🎲)")

    while True:
        try:
            choice = input("\nSelecciona [1-3, defecto 1]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo...")
            sys.exit(0)

        if choice in ("", "1"):
            return chess.WHITE
        elif choice == "2":
            return chess.BLACK
        elif choice == "3":
            return random.choice([chess.WHITE, chess.BLACK])
        print("\033[91mOpción inválida. Elige 1, 2 o 3.\033[0m")

def choose_personality():
    """Permite elegir la personalidad o estilo de juego de la IA."""
    print("\n\033[1;34mElige el estilo / personalidad de la IA:\033[0m")
    keys = list(PERSONALITIES.keys())
    for idx, k in enumerate(keys, 1):
        p = PERSONALITIES[k]
        print(f"  [\033[1;32m{idx}\033[0m] \033[1;97m{p['name']}\033[0m - {p['description']}")

    while True:
        try:
            choice = input("\nSelecciona [1-4, defecto 1]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo...")
            sys.exit(0)

        if choice in ("", "1"):
            return "clasico"
        elif choice == "2":
            return "agresivo"
        elif choice == "3":
            return "sarcastico"
        elif choice == "4":
            return "entrenador"
        print("\033[91mOpción inválida. Elige del 1 al 4.\033[0m")

def choose_theme():
    """Permite elegir el tema visual del tablero."""
    print("\n\033[1;34mElige el tema visual del tablero:\033[0m")
    print("  [\033[1;32m1\033[0m] Verde Clásico (Estilo Chess.com) - \033[92mRecomendado\033[0m")
    print("  [\033[1;32m2\033[0m] Madera Cálida (Estilo Lichess)")
    print("  [\033[1;32m3\033[0m] Alto Contraste Neón (Cian y Blanco)")
    print("  [\033[1;32m4\033[0m] Azul Océano (Estilo Marino)")
    print("  [\033[1;32m5\033[0m] ASCII Básico (Sin colores 256)")

    while True:
        try:
            choice = input("\nSelecciona [1-5, defecto 1]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo...")
            sys.exit(0)

        if choice in ("", "1"):
            return "verde"
        elif choice == "2":
            return "madera"
        elif choice == "3":
            return "contraste"
        elif choice == "4":
            return "azul"
        elif choice == "5":
            return "ascii"
        print("\033[91mOpción inválida. Elige del 1 al 5.\033[0m")

def choose_piece_style():
    """Permite elegir la apariencia de las piezas (Letras en español para evitar signos '?')."""
    print("\n\033[1;34mElige el estilo visual de las piezas:\033[0m")
    print("  [\033[1;32m1\033[0m] Letras en Español (\033[1;97mP, C, A, T, D, R\033[0m) - \033[92mRecomendado (Evita '?' en cualquier terminal)\033[0m")
    print("  [\033[1;32m2\033[0m] Letras en Español Mayúsculas (\033[1;97mP, C, A, T, D, R\033[0m)")
    print("  [\033[1;32m3\033[0m] Letras Internacionales / FEN (\033[1;97mP, N, B, R, Q, K\033[0m)")
    print("  [\033[1;32m4\033[0m] Símbolos Unicode tradicionales (\033[1;97m♔ ♕ ♖ ♗ ♘ ♙\033[0m)")
    print("  [\033[1;32m5\033[0m] Símbolos Unicode invertidos (\033[1;97m♚ ♛ ♜ ♝ ♞ ♟\033[0m)")

    while True:
        try:
            choice = input("\nSelecciona [1-5, defecto 1]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo...")
            sys.exit(0)

        if choice in ("", "1"):
            return "espanol"
        elif choice == "2":
            return "espanol_mayus"
        elif choice == "3":
            return "ingles"
        elif choice == "4":
            return "unicode"
        elif choice == "5":
            return "unicode_invertido"
        print("\033[91mOpción inválida. Elige del 1 al 5.\033[0m")

def choose_board_size():
    """Permite elegir el tamaño visual del tablero."""
    print("\n\033[1;34mElige el tamaño del tablero:\033[0m")
    print("  [\033[1;32m1\033[0m] Mediano (5x1)  - Casillas amplias de 5 col., letras centradas (\033[92mRecomendado\033[0m)")
    print("  [\033[1;32m2\033[0m] Grande (5x2)   - Casillas de 5x2 líneas. Proporción cuadrada de ajedrez")
    print("  [\033[1;32m3\033[0m] Compacto (3x1) - Casillas compactas para terminales pequeñas")

    while True:
        try:
            choice = input("\nSelecciona [1-3, defecto 1]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo...")
            sys.exit(0)

        if choice in ("", "1"):
            return "mediano"
        elif choice == "2":
            return "grande"
        elif choice == "3":
            return "compacto"
        print("\033[91mOpción inválida. Elige del 1 al 3.\033[0m")

def choose_game_mode():
    """Permite al usuario elegir entre IA, Crear Sala LAN o Unirse a Sala LAN."""
    print("\n\033[1;34mElige el modo de juego:\033[0m")
    print("  [\033[1;32m1\033[0m] Contra Inteligencia Artificial (Google Gemini)")
    print("  [\033[1;32m2\033[0m] Multijugador LAN: \033[1;93mCrear Sala con Contraseña (Host 👑)\033[0m")
    print("  [\033[1;32m3\033[0m] Multijugador LAN: \033[1;96mUnirse a Sala (Cliente ⚔️)\033[0m")
    print("  [\033[1;32m4\033[0m] Contra Bot Táctico Local (sin conexión / offline)")

    while True:
        try:
            choice = input("\nSelecciona [1-4, defecto 1]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo...")
            sys.exit(0)

        if choice in ("", "1"):
            return "ai"
        elif choice == "2":
            return "host"
        elif choice == "3":
            return "join"
        elif choice == "4":
            return "offline"
        print("\033[91mOpción inválida. Elige del 1 al 4.\033[0m")

def select_best_model(available_models: list) -> str:
    """Selecciona el modelo Gemini más rápido, avanzado y disponible para la clave."""
    preferred = [
        "gemini-3.1-flash-lite",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash",
        "gemini-flash-latest",
        "gemini-flash-lite-latest",
    ]
    for model in preferred:
        if model in available_models:
            return model
    for model in available_models:
        if "flash" in model.lower() and "lite" in model.lower():
            return model
    for model in available_models:
        if "flash" in model.lower() and "preview" not in model.lower():
            return model
    return "gemini-3.1-flash-lite"

def main():
    parser = argparse.ArgumentParser(description="Ajedrez en Terminal con Google Gemini AI y Multijugador LAN")
    parser.add_argument("--offline", action="store_true", help="Jugar directamente contra el bot local sin pedir API")
    parser.add_argument("--host", action="store_true", help="Crear sala multijugador local (Host)")
    parser.add_argument("--join", type=str, default=None, metavar="IP", help="Unirse a sala multijugador indicando la IP del anfitrión")
    parser.add_argument("--port", type=int, default=5050, help="Puerto de conexión multijugador (por defecto 5050)")
    parser.add_argument("--white", action="store_true", help="Jugar con blancas automáticamente")
    parser.add_argument("--black", action="store_true", help="Jugar con negras automáticamente")
    parser.add_argument("--model", type=str, default=None, help="Modelo de Gemini a utilizar")
    parser.add_argument("--theme", type=str, default=None, choices=["verde", "madera", "contraste", "azul", "ascii"], help="Tema visual")
    parser.add_argument("--pieces", "-p", type=str, default=None, choices=["espanol", "espanol_mayus", "ingles", "unicode", "unicode_invertido"], help="Estilo visual de las piezas")
    parser.add_argument("--size", "--tamano", type=str, default=None, choices=["mediano", "grande", "compacto"], help="Tamaño visual del tablero")
    parser.add_argument("--personality", type=str, default=None, choices=["clasico", "agresivo", "sarcastico", "entrenador"], help="Personalidad de la IA")
    args = parser.parse_args()

    print_banner()

    # Determinar modo de juego
    if args.host:
        mode = "host"
    elif args.join:
        mode = "join"
    elif args.offline:
        mode = "offline"
    else:
        mode = choose_game_mode()

    if mode == "host":
        theme = args.theme or choose_theme()
        piece_style = args.pieces or choose_piece_style()
        board_size = args.size or choose_board_size()
        res = host_room_interactive(port=args.port)
        if res:
            session, my_color, my_name, rival_name = res
            play_network_game(
                session=session,
                my_color=my_color,
                my_name=my_name,
                rival_name=rival_name,
                theme_key=theme,
                piece_style=piece_style,
                board_size=board_size
            )
        return

    if mode == "join":
        theme = args.theme or choose_theme()
        piece_style = args.pieces or choose_piece_style()
        board_size = args.size or choose_board_size()
        res = join_room_interactive(preset_ip=args.join, port=args.port)
        if res:
            session, my_color, my_name, rival_name = res
            play_network_game(
                session=session,
                my_color=my_color,
                my_name=my_name,
                rival_name=rival_name,
                theme_key=theme,
                piece_style=piece_style,
                board_size=board_size
            )
        return

    # Gestión de API Key de Google AI Studio para partidas vs IA
    if mode == "offline":
        api_key = None
        models = []
        ai_name = "Bot Local"
        model_name = "Local"
    else:
        api_key, models = get_or_prompt_api_key()
        if api_key:
            model_name = args.model or select_best_model(models)
            ai_name = f"Gemini ({model_name})"
            print(f"\n\033[92m✔ Conectado a Google AI Studio con modelo:\033[0m \033[1;93m{model_name}\033[0m")
        else:
            model_name = "Local"
            ai_name = "Bot Táctico Local"

    while True:
        # Configurar partida
        if args.white:
            player_color = chess.WHITE
        elif args.black:
            player_color = chess.BLACK
        else:
            player_color = choose_color()

        personality = args.personality or choose_personality()
        theme = args.theme or choose_theme()
        piece_style = args.pieces or choose_piece_style()
        board_size = args.size or choose_board_size()

        ai = GeminiChessAI(
            api_key=api_key,
            model=model_name if api_key else "gemini-3.1-flash-lite",
            personality_key=personality
        )

        # Iniciar partida
        play_game(
            ai=ai,
            player_color=player_color,
            theme_key=theme,
            piece_style=piece_style,
            board_size=board_size,
            ai_name=ai_name
        )

        # Preguntar si desea revancha
        try:
            again = input("\n¿Deseas jugar otra partida? [\033[1;32mS\033[0m/n]: ").strip().lower()
            if again not in ("", "s", "si", "sí", "y", "yes"):
                print("\n¡Gracias por jugar al Ajedrez en Terminal! Hasta la próxima.")
                break
        except (KeyboardInterrupt, EOFError):
            print("\n¡Hasta la próxima!")
            break

if __name__ == "__main__":
    main()
