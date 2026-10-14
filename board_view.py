#!/usr/bin/env python3
"""
Módulo de renderizado del tablero y paneles visuales en terminal.
Proporciona temas personalizables, múltiples estilos de piezas (Letras en Español,
Letras en Inglés/FEN, Símbolos Unicode), vista volteada según el color del jugador,
resaltado de última jugada, jaque, panel lateral con capturas, guía de piezas y comentarios.
"""

import os
import re
import shutil
import chess
from move_parser import san_to_spanish

def strip_ansi(text: str) -> str:
    """Elimina secuencias de escape ANSI para calcular el ancho visible exacto en terminal."""
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

# Estilos de piezas soportados
PIECE_SETS = {
    "espanol": {
        "name": "Letras en Español (P, C, A, T, D, R)",
        "description": "Evita signos '?' en terminales sin fuentes especiales. Letras estándar en español.",
        "legend": "P=Peón · C=Caballo · A=Alfil · T=Torre · D=Dama · R=Rey",
        "legend_case": "Blancas = MAYÚSCULAS (P, C...) │ Negras = minúsculas (p, c...)",
        "pieces": {
            'P': 'P', 'N': 'C', 'B': 'A', 'R': 'T', 'Q': 'D', 'K': 'R',
            'p': 'p', 'n': 'c', 'b': 'a', 'r': 't', 'q': 'd', 'k': 'r',
        }
    },
    "espanol_mayus": {
        "name": "Letras en Español Mayúsculas (P, C, A, T, D, R)",
        "description": "Todas en mayúsculas, diferenciadas por el color de casilla y texto.",
        "legend": "P=Peón · C=Caballo · A=Alfil · T=Torre · D=Dama · R=Rey",
        "legend_case": "Diferenciadas por color: Blancas claras vs Negras oscuras",
        "pieces": {
            'P': 'P', 'N': 'C', 'B': 'A', 'R': 'T', 'Q': 'D', 'K': 'R',
            'p': 'P', 'n': 'C', 'b': 'A', 'r': 'T', 'q': 'D', 'k': 'R',
        }
    },
    "ingles": {
        "name": "Letras en Inglés / FEN (P, N, B, R, Q, K)",
        "description": "Notación algebraica internacional (P=Pawn, N=Knight, B=Bishop, R=Rook, Q=Queen, K=King).",
        "legend": "P=Peón(P) · N=Caballo(N) · B=Alfil(B) · R=Torre(R) · Q=Dama(Q) · K=Rey(K)",
        "legend_case": "Blancas = MAYÚSCULAS (P, N...) │ Negras = minúsculas (p, n...)",
        "pieces": {
            'P': 'P', 'N': 'N', 'B': 'B', 'R': 'R', 'Q': 'Q', 'K': 'K',
            'p': 'p', 'n': 'n', 'b': 'b', 'r': 'r', 'q': 'q', 'k': 'k',
        }
    },
    "unicode": {
        "name": "Símbolos Unicode tradicionales (♔ ♕ ♖ ♗ ♘ ♙)",
        "description": "Iconos gráficos clásicos (requiere fuente con soporte para ajedrez).",
        "legend": "♙=Peón · ♘=Caballo · ♗=Alfil · ♖=Torre · ♕=Dama · ♔=Rey",
        "legend_case": "Blancas = Huecas (♔, ♕...) │ Negras = Rellenas (♚, ♛...)",
        "pieces": {
            'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
            'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚',
        }
    },
    "unicode_invertido": {
        "name": "Símbolos Unicode invertidos (♚ ♛ ♜ ♝ ♞ ♟)",
        "description": "Para terminales donde los símbolos rellenos lucen mejor en las piezas blancas.",
        "legend": "♟=Blancas · ♙=Negras",
        "legend_case": "Blancas = Rellenas (♚, ♛...) │ Negras = Huecas (♔, ♕...)",
        "pieces": {
            'P': '♟', 'N': '♞', 'B': '♝', 'R': '♜', 'Q': '♛', 'K': '♚',
            'p': '♙', 'n': '♘', 'b': '♗', 'r': '♖', 'q': '♕', 'k': '♔',
        }
    }
}

# Aliases de compatibilidad hacia atrás
UNICODE_PIECES = PIECE_SETS["unicode"]["pieces"]
ASCII_PIECES = PIECE_SETS["ingles"]["pieces"]

PIECE_WEIGHTS = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}

# Definición de temas de color ANSI
THEMES = {
    "verde": {
        "name": "Verde Clásico (Chess.com)",
        "light_sq": "\033[48;5;187m",
        "dark_sq": "\033[48;5;65m",
        "last_sq": "\033[48;5;142m",
        "check_sq": "\033[48;5;196m",
        "white_piece": "\033[38;5;231;1m",
        "black_piece": "\033[38;5;16;1m",
        "border": "\033[38;5;244m",
        "reset": "\033[0m"
    },
    "madera": {
        "name": "Madera Cálida (Lichess)",
        "light_sq": "\033[48;5;223m",
        "dark_sq": "\033[48;5;137m",
        "last_sq": "\033[48;5;178m",
        "check_sq": "\033[48;5;196m",
        "white_piece": "\033[38;5;231;1m",
        "black_piece": "\033[38;5;233;1m",
        "border": "\033[38;5;180m",
        "reset": "\033[0m"
    },
    "contraste": {
        "name": "Alto Contraste Neón",
        "light_sq": "\033[48;5;254m",
        "dark_sq": "\033[48;5;238m",
        "last_sq": "\033[48;5;220m",
        "check_sq": "\033[48;5;196m",
        "white_piece": "\033[38;5;231;1m",
        "black_piece": "\033[38;5;45;1m",  # Cian brillante
        "border": "\033[38;5;247m",
        "reset": "\033[0m"
    },
    "azul": {
        "name": "Azul Océano",
        "light_sq": "\033[48;5;252m",
        "dark_sq": "\033[48;5;31m",
        "last_sq": "\033[48;5;221m",
        "check_sq": "\033[48;5;196m",
        "white_piece": "\033[38;5;231;1m",
        "black_piece": "\033[38;5;16;1m",
        "border": "\033[38;5;75m",
        "reset": "\033[0m"
    },
    "ascii": {
        "name": "ASCII Básico (Sin colores 256)",
        "light_sq": "",
        "dark_sq": "",
        "last_sq": "",
        "check_sq": "",
        "white_piece": "",
        "black_piece": "",
        "border": "",
        "reset": ""
    }
}

# Tamaños del tablero soportados
BOARD_SIZES = {
    "mediano": {
        "name": "Mediano (5x1)",
        "description": "Casillas amplias de 5 columnas. Letras centradas al milímetro y espacio cómodo.",
        "cell_w": 5,
        "cell_h": 1,
    },
    "grande": {
        "name": "Grande (5x2)",
        "description": "Casillas de 5x2 caracteres. Proporción cuadrada de ajedrez en terminal y máxima claridad.",
        "cell_w": 5,
        "cell_h": 2,
    },
    "compacto": {
        "name": "Compacto (3x1)",
        "description": "Casillas de 3x1 caracteres. Formato clásico para terminales pequeñas, coordenadas alineadas.",
        "cell_w": 3,
        "cell_h": 1,
    }
}

def clear_screen():
    """Limpia la terminal de forma compatible con Windows y Linux."""
    os.system("cls" if os.name == "nt" else "clear")

def get_captured_pieces(board: chess.Board):
    """Calcula las piezas capturadas por cada bando y la diferencia de material."""
    starting_pieces = {
        chess.WHITE: {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2, chess.ROOK: 2, chess.QUEEN: 1},
        chess.BLACK: {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2, chess.ROOK: 2, chess.QUEEN: 1}
    }

    current_pieces = {
        chess.WHITE: {chess.PAWN: 0, chess.KNIGHT: 0, chess.BISHOP: 0, chess.ROOK: 0, chess.QUEEN: 0},
        chess.BLACK: {chess.PAWN: 0, chess.KNIGHT: 0, chess.BISHOP: 0, chess.ROOK: 0, chess.QUEEN: 0}
    }

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.piece_type != chess.KING:
            current_pieces[piece.color][piece.piece_type] += 1

    # Piezas negras capturadas por blancas
    white_captures = []
    white_score = 0
    for p_type, count in starting_pieces[chess.BLACK].items():
        lost = count - current_pieces[chess.BLACK][p_type]
        for _ in range(max(0, lost)):
            white_captures.append(chess.Piece(p_type, chess.BLACK).symbol())
            white_score += PIECE_WEIGHTS[p_type]

    # Piezas blancas capturadas por negras
    black_captures = []
    black_score = 0
    for p_type, count in starting_pieces[chess.WHITE].items():
        lost = count - current_pieces[chess.WHITE][p_type]
        for _ in range(max(0, lost)):
            black_captures.append(chess.Piece(p_type, chess.WHITE).symbol())
            black_score += PIECE_WEIGHTS[p_type]

    diff = white_score - black_score
    return white_captures, black_captures, diff

def format_captured_symbols(symbols: list, piece_style: str = "espanol", use_ascii: bool = False) -> str:
    """Convierte la lista de símbolos capturados a una cadena visual según el estilo elegido."""
    if not symbols:
        return "(ninguna)"
    if use_ascii and piece_style not in PIECE_SETS:
        piece_style = "espanol"
    pset = PIECE_SETS.get(piece_style, PIECE_SETS["espanol"])["pieces"]
    res = [pset.get(s, s) for s in symbols]
    return " ".join(res)

def make_side_line(content: str, width: int = 47) -> str:
    """Construye una fila del panel lateral cerrada por ambos lados exactamente al ancho especificado."""
    vis_len = len(strip_ansi(content))
    pad = max(0, width - vis_len)
    return f"\033[1;36m║\033[0m{content}{' ' * pad}\033[1;36m║\033[0m"

def make_box_line(content: str, width: int = 72, border_color: str = "\033[1;34m") -> str:
    """Construye una línea de caja horizontal con bordes alineados."""
    vis_len = len(strip_ansi(content))
    pad = max(0, width - vis_len)
    return f"{border_color}│\033[0m{content}{' ' * pad}{border_color}│\033[0m"

def render_game_view(
    board: chess.Board,
    player_color: chess.Color,
    ai_name: str = "Gemini IA",
    last_move: chess.Move = None,
    ai_commentary: str = None,
    theme_key: str = "verde",
    piece_style: str = "espanol",
    board_size: str = "mediano",
    chat_messages: list = None,
    game_mode: str = "ai",
    my_name: str = "Tú"
):
    """
    Renderiza el tablero y el panel lateral de información con estilo elegante y configurable.
    Permite casillas compactas (3x1), medianas (5x1) o grandes (5x2), con coordenadas
    perfectamente alineadas y centradas al milímetro con cada casilla.
    Soporta visualización de chat en partidas multijugador LAN.
    """
    cfg = BOARD_SIZES.get(board_size, BOARD_SIZES["mediano"])
    cell_w = cfg["cell_w"]
    cell_h = cfg["cell_h"]
    pad_l = (cell_w - 1) // 2
    pad_r = cell_w - 1 - pad_l
    total_w = cell_w * 8

    theme = THEMES.get(theme_key, THEMES["verde"])
    use_ascii_theme = (theme_key == "ascii")
    RST = theme["reset"]
    BDR = theme["border"] if not use_ascii_theme else ""
    COORD = "\033[1;93m" if not use_ascii_theme else ""
    COORD_RST = RST if not use_ascii_theme else ""

    tl = "+" if use_ascii_theme else "┌"
    tr = "+" if use_ascii_theme else "┐"
    bl = "+" if use_ascii_theme else "└"
    br = "+" if use_ascii_theme else "┘"
    hz = "-" if use_ascii_theme else "─"
    vl = "|" if use_ascii_theme else "│"

    pset_data = PIECE_SETS.get(piece_style, PIECE_SETS["espanol"])
    pieces_map = pset_data["pieces"]

    # Cuadros de la última jugada para resaltado
    last_squares = set()
    if last_move:
        last_squares.add(last_move.from_square)
        last_squares.add(last_move.to_square)

    # Cuadro del rey en jaque
    check_square = None
    if board.is_check():
        check_square = board.king(board.turn)

    # Determinar orientación (si el jugador es negras, voltear el tablero)
    flip = (player_color == chess.BLACK)
    ranks = range(8) if flip else range(7, -1, -1)
    files = range(7, -1, -1) if flip else range(8)

    # Obtener capturas
    w_caps, b_caps, diff = get_captured_pieces(board)
    diff_str_w = f" (+{diff})" if diff > 0 else ""
    diff_str_b = f" (+{-diff})" if diff < 0 else ""

    # Textos de estado y turno
    turn_str = "Blancas" if board.turn == chess.WHITE else "Negras"
    turn_owner = "(Tu turno)" if board.turn == player_color else f"({ai_name})"
    
    last_move_str = "-"
    if last_move:
        san_display = san_to_spanish(last_move.uci())
        last_move_str = f"{last_move.uci()} ({san_display})" if san_display != last_move.uci() else f"{last_move.uci()}"

    # Estado de la partida
    status_str = "En curso"
    if board.is_checkmate():
        winner = "Negras" if board.turn == chess.WHITE else "Blancas"
        status_str = f"\033[92m¡Jaque Mate! Ganan {winner}\033[0m"
    elif board.is_stalemate():
        status_str = "\033[93mTablas por Ahogado\033[0m"
    elif board.is_insufficient_material():
        status_str = "\033[93mTablas por Material Insuficiente\033[0m"
    elif board.is_check():
        status_str = "\033[91m¡JAQUE!\033[0m"

    w_caps_str = format_captured_symbols(w_caps, piece_style=piece_style) + diff_str_w
    b_caps_str = format_captured_symbols(b_caps, piece_style=piece_style) + diff_str_b

    # Renderizado visual línea a línea del tablero
    board_lines = []
    header_cells = "".join([f"{' ' * pad_l}{COORD}{chess.FILE_NAMES[f]}{COORD_RST}{' ' * pad_r}" for f in files])
    top_header = f"    {header_cells}   "
    top_border = f"   {BDR}{tl}{hz * total_w}{tr}{RST}  "
    bot_border = f"   {BDR}{bl}{hz * total_w}{br}{RST}  "

    board_lines.append(top_header)
    board_lines.append(top_border)

    for rank in ranks:
        rank_num = rank + 1
        for sub_row in range(cell_h):
            is_mid = (sub_row == cell_h // 2)
            prefix = f" {COORD}{rank_num}{COORD_RST} {BDR}{vl}{RST}" if is_mid else f"   {BDR}{vl}{RST}"
            suffix = f"{BDR}{vl}{RST} {COORD}{rank_num}{COORD_RST}" if is_mid else f"{BDR}{vl}{RST}  "
            line_parts = [prefix]

            for file in files:
                sq = chess.square(file, rank)
                piece = board.piece_at(sq)
                is_light = (rank + file) % 2 != 0

                # Selección de color de fondo
                if sq == check_square:
                    bg = theme["check_sq"]
                elif sq in last_squares and not use_ascii_theme:
                    bg = theme["last_sq"]
                else:
                    bg = theme["light_sq"] if is_light else theme["dark_sq"]

                if piece and is_mid:
                    fg = theme["white_piece"] if piece.color == chess.WHITE else theme["black_piece"]
                    sym = pieces_map.get(piece.symbol(), piece.symbol())
                    if use_ascii_theme:
                        line_parts.append(f"{' ' * pad_l}{sym}{' ' * pad_r}")
                    else:
                        line_parts.append(f"{bg}{fg}{' ' * pad_l}{sym}{' ' * pad_r}{RST}")
                else:
                    if use_ascii_theme:
                        line_parts.append(f"{' ' * pad_l}.{' ' * pad_r}" if (not is_light and is_mid) else " " * cell_w)
                    else:
                        line_parts.append(f"{bg}{' ' * cell_w}{RST}")

            line_parts.append(suffix)
            board_lines.append("".join(line_parts))

    board_lines.append(bot_border)
    board_lines.append(top_header)

    # Detección de ancho de terminal y adaptación del panel lateral
    term_cols = shutil.get_terminal_size((80, 24)).columns
    board_w = max(len(strip_ansi(b)) for b in board_lines)

    if board_w + 2 + 47 <= term_cols:
        side_by_side = True
        side_inner_w = 45
    elif board_w + 2 + 30 <= term_cols:
        side_by_side = True
        side_inner_w = 28
    else:
        side_by_side = False
        side_inner_w = min(45, max(28, term_cols - 4))

    border_c = "\033[1;36m"
    s_top = f"{border_c}╔{'═' * side_inner_w}╗{RST}"
    s_mid = f"{border_c}╠{'═' * side_inner_w}╣{RST}"
    s_bot = f"{border_c}╚{'═' * side_inner_w}╝{RST}"

    def make_sline(content: str) -> str:
        vis_len = len(strip_ansi(content))
        pad = max(0, side_inner_w - vis_len)
        return f"{border_c}║{RST}{content}{' ' * pad}{border_c}║{RST}"

    if side_inner_w >= 40:
        title_text = f"  \033[1;33m★  LAN: {my_name[:10]} vs {ai_name[:10]}\033[0m" if game_mode == "lan" else f"  \033[1;33m★  AJEDREZ: Humano vs {ai_name[:16]}\033[0m"
        side_lines = [
            s_top,
            make_sline(title_text),
            s_mid,
            make_sline(f"  Turno: \033[1;97m{turn_str} {turn_owner}\033[0m"),
            make_sline(f"  Estado: {status_str}"),
            make_sline(f"  Última jugada: \033[93m{last_move_str}\033[0m"),
            s_mid,
            make_sline(f"  Capturas Blancas: {w_caps_str}"),
            make_sline(f"  Capturas Negras:  {b_caps_str}"),
        ]
        if len(board_lines) > 14:
            size_name = cfg["name"]
            style_name = pset_data["name"].split("(")[0].strip()
            side_lines.extend([
                s_mid,
                make_sline(f"  \033[96mTamaño:\033[0m {size_name}"),
                make_sline(f"  \033[96mEstilo:\033[0m {style_name[:20]}"),
            ])
        side_lines.append(s_bot)
    else:
        title_text = f" \033[1;33m★ LAN: {my_name[:6]} vs {ai_name[:6]}\033[0m" if game_mode == "lan" else f" \033[1;33m★ Humano vs {ai_name[:10]}\033[0m"
        side_lines = [
            s_top,
            make_sline(title_text),
            s_mid,
            make_sline(f" Turno: \033[1;97m{turn_str}\033[0m {turn_owner}"),
            make_sline(f" Estado: {status_str}"),
            make_sline(f" Última: \033[93m{last_move_str}\033[0m"),
            s_mid,
            make_sline(f" Cap. B: {w_caps_str}"),
            make_sline(f" Cap. N: {b_caps_str}"),
        ]
        if len(board_lines) > 14:
            size_name = cfg["name"].split("(")[0].strip()
            side_lines.extend([
                s_mid,
                make_sline(f" Tamaño: {size_name} · 'tamano'"),
            ])
        side_lines.append(s_bot)

    # Imprimir tablero y panel lateral con alineación exacta
    print("")
    if side_by_side:
        max_rows = max(len(board_lines), len(side_lines))
        for i in range(max_rows):
            b_part = board_lines[i] if i < len(board_lines) else " " * board_w
            s_part = side_lines[i] if i < len(side_lines) else ""
            vis_b = len(strip_ansi(b_part))
            pad = max(0, board_w - vis_b)
            print(f"{b_part}{' ' * pad}  {s_part}")
    else:
        for b_line in board_lines:
            print(b_line)
        print("")
        for s_line in side_lines:
            print(s_line)

    # Mostrar caja de guía de piezas y ayuda
    legend_line = pset_data["legend"]
    legend_case = pset_data["legend_case"]
    cmds_help = "  \033[96mComandos:\033[0m \033[92m'c mensaje'\033[0m (chat), \033[92m'tablas'\033[0m, \033[92m'rendirse'\033[0m, \033[92m'tamano'\033[0m, \033[92m'ayuda'\033[0m" if game_mode == "lan" else "  \033[96mComandos:\033[0m \033[92m'tamano'\033[0m (tamaño tablero), \033[92m'piezas'\033[0m (estilo), \033[92m'tema'\033[0m (colores)"
    print("\n\033[1;34m╭────────────────────────────────────────────────────────────────────────╮\033[0m")
    print(make_box_line(f"  \033[1;33mPiezas:\033[0m   {legend_line}", 72, "\033[1;34m"))
    print(make_box_line(f"  \033[1;37mBando:\033[0m    {legend_case}", 72, "\033[1;34m"))
    print(make_box_line(cmds_help, 72, "\033[1;34m"))
    print("\033[1;34m╰────────────────────────────────────────────────────────────────────────╯\033[0m")

    # Mostrar caja de chat si es partida multijugador LAN o hay mensajes
    if game_mode == "lan" or chat_messages is not None:
        print("\n\033[1;35m╭────────────────────────────────────────────────────────────────────────╮\033[0m")
        print(make_box_line(" 💬 \033[1;97mCHAT DE LA SALA:\033[0m", 72, "\033[1;35m"))
        if not chat_messages:
            print(make_box_line("   \033[90m(Sin mensajes aún. Escribe 'c <mensaje>' para chatear)\033[0m", 72, "\033[1;35m"))
        else:
            for msg in chat_messages[-4:]:
                t = msg.get("time", "")
                s = msg.get("sender", "")
                txt = msg.get("text", "")
                prefix_str = f"[{t}] {s}: "
                max_txt = 66 - len(prefix_str)
                if len(txt) > max_txt:
                    txt = txt[:max_txt - 3] + "..."
                formatted = f"   \033[90m[{t}]\033[0m \033[1;33m{s}:\033[0m {txt}"
                print(make_box_line(formatted, 72, "\033[1;35m"))
        print(make_box_line("   \033[96mComando chat:\033[0m Escribe \033[92m'c tu mensaje'\033[0m o \033[92m'/c mensaje'\033[0m", 72, "\033[1;35m"))
        print("\033[1;35m╰────────────────────────────────────────────────────────────────────────╯\033[0m")

    # Mostrar comentario de la IA si existe y es modo IA
    if ai_commentary and game_mode == "ai":
        print("\n\033[1;35m╭────────────────────────────────────────────────────────────────────────╮\033[0m")
        print(make_box_line(f" 🤖 \033[1;97m{ai_name}:\033[0m", 72, "\033[1;35m"))
        for line in ai_commentary.split("\n"):
            while len(line) > 68:
                print(make_box_line(f"   {line[:68]}", 72, "\033[1;35m"))
                line = line[68:]
            if line:
                print(make_box_line(f"   {line}", 72, "\033[1;35m"))
        print("\033[1;35m╰────────────────────────────────────────────────────────────────────────╯\033[0m")
