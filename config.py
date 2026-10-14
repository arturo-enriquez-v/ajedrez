#!/usr/bin/env python3
"""
Módulo de configuración y gestión de credenciales para Google AI Studio.
Permite validar, cargar y guardar la clave API en .env de manera segura.
"""

import os
import sys
import json
import urllib.request
import urllib.error

ENV_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

def load_env_file():
    """Carga variables desde el archivo .env local si existe."""
    env_vars = {}
    if os.path.exists(ENV_FILE_PATH):
        try:
            with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip().strip("'\"")
        except Exception:
            pass
    return env_vars

def save_api_key_to_env(api_key: str):
    """Guarda o actualiza la clave GEMINI_API_KEY en el archivo .env."""
    existing_vars = load_env_file()
    existing_vars["GEMINI_API_KEY"] = api_key
    try:
        with open(ENV_FILE_PATH, "w", encoding="utf-8") as f:
            for k, v in existing_vars.items():
                f.write(f"{k}={v}\n")
        return True
    except Exception as e:
        print(f"\033[91mNo se pudo guardar en .env: {e}\033[0m")
        return False

def validate_api_key(api_key: str, timeout: int = 10):
    """
    Valida la API Key consultando la lista de modelos de Google AI Studio.
    Retorna una tupla (valido: bool, modelos: list, error_msg: str | None).
    """
    if not api_key or len(api_key.strip()) < 10:
        return False, [], "La clave proporcionada parece demasiado corta o vacía."

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key.strip()}"
    req = urllib.request.Request(url, headers={"User-Agent": "Terminal-Chess-Gemini/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                models = [
                    m.get("name", "").replace("models/", "")
                    for m in data.get("models", [])
                    if "generateContent" in m.get("supportedGenerationMethods", [])
                ]
                return True, models, None
            return False, [], f"Código de respuesta HTTP inesperado: {response.status}"
    except urllib.error.HTTPError as e:
        try:
            err_json = json.loads(e.read().decode("utf-8"))
            msg = err_json.get("error", {}).get("message", str(e))
        except Exception:
            msg = str(e)
        return False, [], f"Error de autenticación ({e.code}): {msg}"
    except urllib.error.URLError as e:
        return False, [], f"Error de red o conexión: {e.reason}"
    except Exception as e:
        return False, [], f"Error inesperado: {str(e)}"

def mask_key(key: str) -> str:
    """Oculta la mayoría de los caracteres de la clave para mostrarla con seguridad."""
    if len(key) <= 8:
        return "****"
    return key[:4] + "..." + key[-4:]

def get_or_prompt_api_key():
    """
    Pide o recupera la API Key de Google AI Studio.
    Si ya existe en el entorno o .env, pregunta si desea reutilizarla.
    Si no, solicita al usuario que la ingrese por terminal y la valida.
    """
    env_vars = load_env_file()
    saved_key = os.environ.get("GEMINI_API_KEY") or env_vars.get("GEMINI_API_KEY")

    if saved_key:
        print("\n\033[96m╔══════════════════════════════════════════════════════════════╗\033[0m")
        print("\033[96m║         🔑 CLAVE DE GOOGLE AI STUDIO DETECTADA              ║\033[0m")
        print("\033[96m╚══════════════════════════════════════════════════════════════╝\033[0m")
        print(f"Se encontró una clave guardada: \033[93m{mask_key(saved_key)}\033[0m")
        
        try:
            choice = input("¿Deseas usar esta clave? [\033[1;32mS\033[0m/n]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nOperación cancelada.")
            sys.exit(0)

        if choice in ("", "s", "si", "sí", "y", "yes"):
            print("Verificando clave con los servidores de Google AI Studio...")
            valid, models, err = validate_api_key(saved_key)
            if valid:
                print("\033[92m✔ Clave validada exitosamente con Google AI Studio.\033[0m")
                return saved_key, models
            else:
                print(f"\033[91m✖ La clave guardada falló: {err}\033[0m")
                print("Por favor, ingresa una nueva clave a continuación.")

    # Solicitar clave nueva
    while True:
        print("\n\033[94m╔══════════════════════════════════════════════════════════════╗\033[0m")
        print("\033[94m║        ⚙️  CONFIGURACIÓN DE GOOGLE AI STUDIO API KEY          ║\033[0m")
        print("\033[94m╚══════════════════════════════════════════════════════════════╝\033[0m")
        print("Para jugar contra la Inteligencia Artificial necesitas una API Key")
        print("gratuita de Google AI Studio.")
        print("\n👉 Obtén tu clave aquí: \033[1;36mhttps://aistudio.google.com/app/apikey\033[0m")
        print("(Escribe 'offline' para jugar contra el bot táctico local sin API)")
        print("(Escribe 'salir' para cancelar)\n")

        try:
            entered_key = input("\033[1;33mIntroduce tu Google AI Studio API Token: \033[0m").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperación cancelada.")
            sys.exit(0)

        if entered_key.lower() in ("salir", "exit", "quit"):
            print("Saliendo...")
            sys.exit(0)

        if entered_key.lower() == "offline":
            print("\033[93mIniciando en modo local offline (Bot Táctico integrado).\033[0m")
            return None, []

        if not entered_key:
            print("\033[91mLa clave no puede estar vacía. Intenta de nuevo.\033[0m")
            continue

        print("Validando clave con Google AI Studio...")
        valid, models, err = validate_api_key(entered_key)
        if valid:
            print("\033[92m✔ ¡Clave validada correctamente!\033[0m")
            try:
                save_choice = input("¿Deseas guardar esta clave en el archivo .env para futuras partidas? [\033[1;32mS\033[0m/n]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                save_choice = "s"

            if save_choice in ("", "s", "si", "sí", "y", "yes"):
                if save_api_key_to_env(entered_key):
                    print("\033[92m✔ Clave guardada de forma segura en .env\033[0m")
            return entered_key, models
        else:
            print(f"\033[91m✖ Error al validar la clave: {err}\033[0m")
            print("Verifica que copiaste la clave completa desde Google AI Studio.")
