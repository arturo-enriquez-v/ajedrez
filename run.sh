#!/usr/bin/env bash
# Script para iniciar el Ajedrez en Terminal con Gemini IA

set -e

# Comprobar si python3 está disponible
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 no está instalado o no se encuentra en el PATH."
    exit 1
fi

# Comprobar dependencia python-chess
if ! python3 -c "import chess" &> /dev/null; then
    echo "Instalando la librería python-chess..."
    python3 -m pip install --break-system-packages -r requirements.txt || python3 -m pip install -r requirements.txt
fi

# Ejecutar el juego
exec python3 main.py "$@"
