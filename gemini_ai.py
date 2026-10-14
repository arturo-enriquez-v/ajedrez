#!/usr/bin/env python3
"""
Módulo del motor de Inteligencia Artificial utilizando Google AI Studio (Gemini).
Incluye:
 - Conexión con la API REST de Google AI Studio
 - Prompt engineering especializado en ajedrez
 - Validación rigurosa de jugadas legales
 - Personalidades y estilos de juego
 - Motor táctico de respaldo local (Alpha-Beta / Minimax) si falla la API
"""

import json
import re
import urllib.request
import urllib.error
import chess

PERSONALITIES = {
    "clasico": {
        "name": "Gran Maestro Clásico",
        "description": "Juego posicional equilibrado, sólido y estratégico.",
        "prompt": "Juegas con un estilo clásico y posicional como Anatoly Karpov. Prioriza la estructura de peones, el control del centro y la seguridad del rey. Da comentarios profesionales y analíticos."
    },
    "agresivo": {
        "name": "Ataque Agresivo y Táctico",
        "description": "Busca ataques directos al rey, sacrificios y juego dinámico.",
        "prompt": "Juegas con un estilo hiper-agresivo y táctico como Mikhail Tal o Garry Kasparov. Busca líneas ofensivas, presionar al rey rival y crear complicaciones tácticas continuas. Comentarios enérgicos y amenazantes."
    },
    "sarcastico": {
        "name": "Comentarista Ingenioso / Sarcástico",
        "description": "Comentarios cómicos, burlones y divertidos con buen ajedrez.",
        "prompt": "Eres un jugador de ajedrez muy habilidoso pero divertido, con humor sarcástico e ingenioso. Haz jugadas sólidas mientras lanzas comentarios graciosos o burlas amistosas sobre la posición del rival."
    },
    "entrenador": {
        "name": "Entrenador Mentor Didáctico",
        "description": "Explica el porqué de cada jugada para ayudarte a aprender.",
        "prompt": "Eres un amable entrenador de ajedrez pedagógico. Tu objetivo es ayudar a tu rival a aprender ajedrez. En tus comentarios, explica brevemente el concepto estratégico o táctico detrás de tu jugada."
    }
}

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# Bonificaciones posicionales básicas (centro del tablero)
CENTER_SQUARES = {chess.D4, chess.D5, chess.E4, chess.E5}
EXTENDED_CENTER = {chess.C3, chess.D3, chess.E3, chess.F3, chess.C4, chess.F4, chess.C5, chess.F5, chess.C6, chess.D6, chess.E6, chess.F6}

def evaluate_board(board: chess.Board) -> int:
    """Evalúa la posición material y posicional básica de forma rápida."""
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_game_over():
        return 0

    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            val = PIECE_VALUES[piece.piece_type]
            if square in CENTER_SQUARES:
                val += 25
            elif square in EXTENDED_CENTER:
                val += 10
            score += val if piece.color == chess.WHITE else -val

    # Bonificación por movilidad
    mobility = board.legal_moves.count()
    score += (mobility * 2) if board.turn == chess.WHITE else -(mobility * 2)

    return score

def get_fallback_move(board: chess.Board, depth: int = 2) -> chess.Move:
    """
    Motor local de respaldo: Minimax básico con poda alfa-beta para elegir
    una jugada sólida si no hay internet o la API tiene problemas.
    """
    best_move = None
    is_white = board.turn == chess.WHITE

    # Ordenar jugadas: primero capturas y jaques
    moves = sorted(
        board.legal_moves,
        key=lambda m: (board.is_capture(m), board.gives_check(m)),
        reverse=True
    )

    if not moves:
        return None

    best_score = -999999 if is_white else 999999

    for move in moves:
        board.push(move)
        # Búsqueda profundidad 1-2
        if depth > 1 and not board.is_game_over():
            opp_moves = sorted(
                board.legal_moves,
                key=lambda m: (board.is_capture(m), board.gives_check(m)),
                reverse=True
            )
            opp_best = 999999 if is_white else -999999
            for opp_m in opp_moves[:8]:  # Evaluar las mejores respuestas del oponente
                board.push(opp_m)
                ev = evaluate_board(board)
                board.pop()
                if is_white:
                    opp_best = min(opp_best, ev)
                else:
                    opp_best = max(opp_best, ev)
            score = opp_best
        else:
            score = evaluate_board(board)

        board.pop()

        if is_white and score > best_score:
            best_score = score
            best_move = move
        elif not is_white and score < best_score:
            best_score = score
            best_move = move

    return best_move or moves[0]

class GeminiChessAI:
    def __init__(self, api_key: str = None, model: str = "gemini-3.1-flash-lite", personality_key: str = "clasico"):
        self.api_key = api_key
        self.model = model
        self.personality_key = personality_key
        self.is_offline = not bool(api_key)
        
        # Lista ordenada de modelos a probar en caso de indisponibilidad o 404
        preferred_fallbacks = [
            model,
            "gemini-3.1-flash-lite",
            "gemini-3.1-flash-lite-preview",
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-flash-latest"
        ]
        self.fallback_models = []
        for m in preferred_fallbacks:
            if m and m not in self.fallback_models:
                self.fallback_models.append(m)

    def _call_gemini_api(self, prompt: str, system_instruction: str = None, timeout: int = 12) -> str:
        """Realiza la petición HTTP POST a Google AI Studio con reintento automático en modelos disponibles."""
        last_err = None
        for candidate in self.fallback_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{candidate}:generateContent?key={self.api_key}"

            payload = {
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.4,
                    "responseMimeType": "application/json"
                }
            }

            if system_instruction:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_instruction}]
                }

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "Terminal-Chess-Gemini/1.0"},
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    candidates = result.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            self.model = candidate
                            return parts[0].get("text", "")
            except urllib.error.HTTPError as e:
                # 404: modelo deprecado, 503/429: alta demanda o cuota -> probar siguiente candidato
                last_err = f"HTTP {e.code}"
                continue
            except Exception as e:
                last_err = str(e)
                continue

        if last_err:
            raise RuntimeError(f"Error de conexión con Google AI Studio: {last_err}")
        return ""

    def _clean_json_response(self, raw_text: str) -> dict:
        """Limpia bloques de código markdown y extrae el objeto JSON."""
        text = raw_text.strip()
        # Eliminar ```json ... ``` si existen
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
        text = text.strip()

        try:
            return json.loads(text)
        except Exception:
            # Buscar el primer bloque {...}
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
        return {}

    def get_move(self, board: chess.Board, history_pgn: str = ""):
        """
        Calcula y retorna la jugada de la IA junto a un comentario explicativo.
        Retorna (chess.Move, comentario_str).
        """
        if self.is_offline:
            fallback = get_fallback_move(board)
            san = board.san(fallback)
            return fallback, f"[Modo Local] Jugada táctica calculada: {san}."

        color_name = "BLANCAS" if board.turn == chess.WHITE else "NEGRAS"
        personality = PERSONALITIES.get(self.personality_key, PERSONALITIES["clasico"])

        # Generar listado exacto de jugadas legales en formato UCI y SAN
        legal_moves_info = []
        for m in board.legal_moves:
            legal_moves_info.append(f'"{m.uci()}" ({board.san(m)})')
        legal_moves_str = ", ".join(legal_moves_info)

        # Representación textual del tablero para el modelo
        board_ascii = str(board)

        system_instruction = (
            f"Eres un Gran Maestro de Ajedrez compitiendo en una partida. {personality['prompt']}\n"
            "Tu objetivo es elegir la MEJOR jugada posible de la lista de jugadas legales disponibles.\n"
            "REGLAS CRÍTICAS:\n"
            "1. La jugada seleccionada en 'move' DEBE estar EXACTAMENTE en formato UCI (ej: 'e7e5', 'g8f6', 'e7e8q').\n"
            "2. 'move' DEBE pertenecer estrictamente a la lista de jugadas legales proporcionada.\n"
            "3. 'commentary' debe ser un comentario breve en español (1-2 frases) sobre tu jugada o la situación de la partida.\n"
            "Debes responder ÚNICAMENTE con un JSON con los campos 'move' y 'commentary'."
        )

        user_prompt = (
            f"Partida actual:\n"
            f"- Te toca jugar con las piezas: {color_name}\n"
            f"- FEN actual: {board.fen()}\n"
            f"- Historial de jugadas: {history_pgn or 'Inicio de la partida'}\n"
            f"- Estado de jaque: {'¡Estás en jaque!' if board.is_check() else 'No'}\n\n"
            f"Tablero actual:\n{board_ascii}\n\n"
            f"JUGADAS LEGALES DISPONIBLES:\n[{legal_moves_str}]\n\n"
            f"Elige la mejor jugada de la lista anterior y responde en JSON:\n"
            '{\n  "move": "<jugada_en_formato_uci>",\n  "commentary": "<comentario en español>"\n}'
        )

        # Intentar obtener respuesta de Gemini con reintentos
        for attempt in range(2):
            try:
                raw_response = self._call_gemini_api(user_prompt, system_instruction)
                data = self._clean_json_response(raw_response)

                chosen_move_str = str(data.get("move", "")).strip()
                commentary = data.get("commentary", "Buena jugada.")

                # 1. Validar como UCI
                try:
                    move = chess.Move.from_uci(chosen_move_str.lower())
                    if move in board.legal_moves:
                        return move, commentary
                except Exception:
                    pass

                # 2. Validar si lo envió en SAN por error
                try:
                    move = board.parse_san(chosen_move_str)
                    if move in board.legal_moves:
                        return move, commentary
                except Exception:
                    pass

                # Si no es válida, ajustar prompt para el segundo intento
                user_prompt += f"\n\nATENCIÓN: '{chosen_move_str}' NO es una jugada legal válida. Elige estrictamente una de: [{legal_moves_str}]"

            except Exception as e:
                if attempt == 1:
                    # En caso de error de red o límite de cuota, usar respaldo local
                    fallback = get_fallback_move(board)
                    san = board.san(fallback)
                    return fallback, f"He jugado {san}. (Nota: Se utilizó cálculo de respaldo debido a latencia de red: {e})"

        # Si agotó intentos sin jugada válida, usar respaldo táctico
        fallback = get_fallback_move(board)
        san = board.san(fallback)
        return fallback, f"He jugado {san}. Concentrémonos en la posición."
