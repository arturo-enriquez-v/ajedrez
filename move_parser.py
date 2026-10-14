#!/usr/bin/env python3
"""
Módulo de parseo de jugadas de ajedrez.
Soporta:
 - Notación UCI (e2e4, g1f3, e7e8q)
 - Notación Algebraica Estándar en Inglés (e4, Nf3, Bc4, O-O, exd5, e8=Q)
 - Notación Algebraica en Español (e4, Cf3, Ac4, Dh5, Te1, 0-0, e8=D)
 - Formatos con guiones o espacios (e2-e4, e2 e4)
"""

import re
import chess

SPANISH_TO_ENGLISH_PIECES = {
    'C': 'N',  # Caballo -> Knight
    'c': 'N',
    'A': 'B',  # Alfil -> Bishop
    'a': 'B',
    'T': 'R',  # Torre -> Rook
    't': 'R',
    'D': 'Q',  # Dama -> Queen
    'd': 'Q',
    'R': 'K',  # Rey -> King
    'r': 'K',
}

ENGLISH_TO_SPANISH_PIECES = {
    'N': 'C',
    'B': 'A',
    'R': 'T',
    'Q': 'D',
    'K': 'R',
}

def san_to_spanish(san_move: str) -> str:
    """Convierte una jugada SAN en inglés a notación en español para visualización."""
    res = san_move
    for eng, esp in ENGLISH_TO_SPANISH_PIECES.items():
        if res.startswith(eng):
            res = esp + res[1:]
            break
        elif f"={eng}" in res:
            res = res.replace(f"={eng}", f"={esp}")
            break
    return res

def normalize_user_input(text: str) -> str:
    """Limpia la entrada del usuario de caracteres superfluos."""
    cleaned = text.strip()
    # Reemplazar 0-0 y 0-0-0 por O-O y O-O-O
    cleaned = cleaned.replace("0-0-0", "O-O-O").replace("0-0", "O-O")
    # Reemplazar e2-e4 o e2 e4 por e2e4
    cleaned = re.sub(r"^([a-h][1-8])[- ]([a-h][1-8])([qrbnQRBN])?$", r"\1\2\3", cleaned)
    return cleaned

def parse_move(board: chess.Board, user_input: str):
    """
    Intenta interpretar la entrada del usuario como una jugada legal en el tablero.
    Retorna un objeto chess.Move si es válida, o None si no se reconoce.
    """
    text = normalize_user_input(user_input)
    if not text:
        return None

    # 1. Intentar como jugada UCI (ej. e2e4, e7e8q)
    try:
        uci_move = chess.Move.from_uci(text.lower())
        if uci_move in board.legal_moves:
            return uci_move
    except Exception:
        pass

    # 2. Intentar como SAN estándar (ej. e4, Nf3, O-O, exd5, e8=Q)
    try:
        san_move = board.parse_san(text)
        if san_move in board.legal_moves:
            return san_move
    except Exception:
        pass

    # 3. Intentar traducción de pieza en español al inicio (ej. Cf3 -> Nf3, Ac4 -> Bc4, Dh5 -> Qh5)
    if len(text) >= 2 and text[0] in SPANISH_TO_ENGLISH_PIECES and text[1] not in "12345678":
        translated = SPANISH_TO_ENGLISH_PIECES[text[0]] + text[1:]
        try:
            san_move = board.parse_san(translated)
            if san_move in board.legal_moves:
                return san_move
        except Exception:
            pass

    # 4. Intentar coronación en español (ej. e8=D -> e8=Q, exd8=D -> exd8=Q)
    if "=" in text:
        parts = text.split("=", 1)
        prefix = parts[0]
        promo = parts[1].strip()
        if promo in SPANISH_TO_ENGLISH_PIECES:
            translated = f"{prefix}={SPANISH_TO_ENGLISH_PIECES[promo]}"
            try:
                san_move = board.parse_san(translated)
                if san_move in board.legal_moves:
                    return san_move
            except Exception:
                pass

    # 5. Capturas con piezas en español (ej. Cxd5 -> Nxd5, Axc6 -> Bxc6)
    if len(text) >= 4 and text[0] in SPANISH_TO_ENGLISH_PIECES and "x" in text:
        translated = SPANISH_TO_ENGLISH_PIECES[text[0]] + text[1:]
        try:
            san_move = board.parse_san(translated)
            if san_move in board.legal_moves:
                return san_move
        except Exception:
            pass

    return None

def get_legal_moves_list(board: chess.Board):
    """
    Devuelve las jugadas legales en formatos convenientes:
    - Lista de tuplas: (uci, san_en, san_es)
    """
    results = []
    for move in board.legal_moves:
        uci = move.uci()
        san_en = board.san(move)
        san_es = san_to_spanish(san_en)
        results.append((uci, san_en, san_es))
    return results
