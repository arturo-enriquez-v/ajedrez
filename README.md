# ♟️ Ajedrez en Terminal con Google Gemini AI (Google AI Studio)

Un juego completo de ajedrez interactivo en la terminal que te permite jugar partidas contra la Inteligencia Artificial de Google (**Gemini**) utilizando tu API Token gratuito de **Google AI Studio**.

---

## 🚀 Requisitos

- **Python 3.10+**
- **python-chess** (se instala automáticamente o mediante `pip install -r requirements.txt`)
- **API Token de Google AI Studio** (gratis): [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

---

## 📦 Instalación

1. Clona o ingresa a la carpeta del proyecto:
   ```bash
   cd /home/arturo/Workspace/ajedrez
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🎮 Cómo Iniciar el Juego

Puedes iniciar el juego con el script ejecutable:
```bash
./run.sh
```

O directamente con Python:
```bash
python3 main.py
```

### 🔑 Configuración del API Token
Al iniciar por primera vez, el juego te pedirá tu clave de **Google AI Studio**:
```
╔══════════════════════════════════════════════════════════════╗
║        ⚙️  CONFIGURACIÓN DE GOOGLE AI STUDIO API KEY          ║
╚══════════════════════════════════════════════════════════════╝
Para jugar contra la Inteligencia Artificial necesitas una API Key
gratuita de Google AI Studio.

👉 Obtén tu clave aquí: https://aistudio.google.com/app/apikey

Introduce tu Google AI Studio API Token:
```

- La clave se valida en tiempo real contactando con los servidores de Google AI Studio.
- Puedes elegir guardarla en `.env` para que no tengas que escribirla cada vez.
- También puedes escribir `offline` si deseas probar el juego contra el bot táctico local sin internet.

---

## 🌟 Características Principales

### 1. Juega con Blancas o Negras (Tablero Invertible)
- Si eliges **Blancas**, juegas en la parte inferior e inicias la partida.
- Si eliges **Negras**, la IA juega con Blancas primero y el tablero se **invierte automáticamente** para que tus piezas queden en la parte inferior.

### 2. Soporte de Notación en Español, Inglés y UCI
Puedes ingresar tus jugadas de cualquier forma:
- **Español (SAN)**: `e4`, `Cf3` (Caballo a f3), `Ac4` (Alfil a c4), `Dh5` (Dama a h5), `Te1` (Torre a e1), `0-0` (Enroque corto), `e8=D` (Coronación a Dama).
- **Inglés (SAN)**: `e4`, `Nf3`, `Bc4`, `Qh5`, `Re1`, `O-O`, `e8=Q`.
- **Coordenadas UCI**: `e2e4`, `g1f3`, `f1c4`, `e7e8q`, `e2-e4`.

### 3. Personalidades de la IA
Puedes elegir el estilo de juego de Gemini:
1. **Gran Maestro Clásico**: Posicional, sólido y equilibrado (estilo Karpov).
2. **Ataque Agresivo y Táctico**: Ataques directos al rey y sacrificios dinámicos (estilo Tal/Kasparov).
3. **Comentarista Sarcástico**: Humor e ingenio con comentarios jocosos sobre la partida.
4. **Entrenador Didáctico**: Te explica el razonamiento detrás de cada jugada para ayudarte a mejorar.

### 4. Estilos de Piezas (¡Solución para terminales sin soporte Unicode!)
Si en tu terminal las piezas se ven con signos de interrogación `?`, puedes seleccionar cualquiera de estos estilos:
1. **Letras en Español (Recomendado)**:
   - **P** = Peón, **C** = Caballo, **A** = Alfil, **T** = Torre, **D** = Dama / Reina, **R** = Rey.
   - Blancas en Mayúsculas (`P`, `C`, `A`, `T`, `D`, `R`) y Negras en minúsculas (`p`, `c`, `a`, `t`, `d`, `r`).
   - 100% compatible con cualquier fuente y terminal (sin símbolos `?`).
2. **Letras en Español Mayúsculas**: Todas en mayúsculas, diferenciadas por el color de la casilla y la pieza.
3. **Letras Internacionales / FEN**: `P` (Pawn), `N` (Knight), `B` (Bishop), `R` (Rook), `Q` (Queen), `K` (King).
4. **Símbolos Unicode tradicionales**: `♔`, `♕`, `♖`, `♗`, `♘`, `♙` (para terminales con fuentes de ajedrez).
5. **Símbolos Unicode invertidos**: `♚`, `♛`, `♜`, `♝`, `♞`, `♟` (para fondos claros).

### 5. Tamaños del Tablero y Alineación Milimétrica de Coordenadas
Puedes ajustar el tamaño del tablero a tu preferencia con el comando `tamano` o al iniciar el juego:
1. **Mediano (5x1 - Recomendado)**: Casillas de 5 caracteres de ancho. Letras de columnas (a-h) y piezas perfectamente centradas, con espacio visual holgado.
2. **Grande (5x2)**: Casillas de 5x2 caracteres. Compensa la altura de los caracteres en terminal para lograr una **proporción cuadrada** auténtica de ajedrez.
3. **Compacto (3x1)**: Formato compacto original con coordenadas exactamente alineadas sobre cada casilla (sin desfasaje).

### 6. Temas Visuales del Tablero
1. **Verde Clásico (Chess.com)**: Casillas salvia y verde bosque con piezas de alto contraste.
2. **Madera Cálida (Lichess)**: Estilo tablero de madera natural.
3. **Alto Contraste Neón**: Piezas en blanco puro y cian brillante.
4. **Azul Océano**: Estilo marino en tonos azules.
5. **ASCII Básico**: Sin colores ni símbolos unicode, compatible con cualquier terminal.

### 7. Multijugador en Red Local (LAN) con Salas, Contraseña y Chat en Vivo
¡Juega contra amigos en la misma red Wi-Fi o Ethernet directamente desde la terminal!
- **Cero configuración externa:** No requiere servidores externos ni cuentas; utiliza sockets TCP directos.
- **Salas privadas con contraseña:** El anfitrión crea una sala y define una contraseña o PIN de acceso.
- **Detección automática de IP local:** El juego muestra la IP del anfitrión (ej. `192.168.1.50`) para compartirla fácilmente.
- **Chat en tiempo real:** Envía y recibe mensajes en vivo mientras juegas o mientras esperas el turno del rival (`c tu mensaje`).
- **Perspectiva personalizada:** Cada jugador ve el tablero desde su punto de vista (tablero invertido para las Negras) y con su propio estilo visual (tema, tamaño y piezas).

---

## ⌨️ Comandos Durante la Partida

Durante tu turno puedes ingresar los siguientes comandos:

| Comando | Descripción |
| :--- | :--- |
| `c <mensaje>` o `/c` | **Envía un mensaje de chat al rival en la sala (ej. `c buena jugada`)** |
| `tablas` o `draw` | Ofrece tablas (empate) al rival en partidas LAN |
| `tamano` o `size` | **Cambia el tamaño del tablero (Mediano, Grande, Compacto)** |
| `piezas` o `estilo` | **Cambia la apariencia de las piezas en tiempo real (Español / Inglés / Unicode)** |
| `tema` o `colores` | Cambia el tema de color del tablero en plena partida |
| `ayuda` o `help` | Abre la guía con todos los formatos y comandos |
| `moves` o `jugadas` | Lista todas las jugadas legales posibles en la posición actual |
| `deshacer` o `undo` | Retrocede tu última jugada (en modo IA) |
| `tablero` o `board` | Vuelve a redibujar el tablero y el panel |
| `fen` | Imprime la posición en notación FEN |
| `pgn` | Muestra el registro PGN de la partida actual |
| `rendirse` o `resign` | Rinde la partida ante el rival o la IA |
| `salir` o `quit` | Cierra el juego |

---

## 🛡️ Robustez y Motor de Respaldo

- **Garantía de jugadas legales**: Se envían las jugadas legales exactas en el prompt a Gemini estructurado en JSON.
- **Reintento automático**: Si por alguna razón la IA sugiere una jugada no válida, se le solicita corrección inmediata.
- **Modo Respaldo Táctico (Minimax con Poda Alfa-Beta)**: Si se pierde la conexión a internet o se agota la cuota de la API, el motor táctico local asume el control sin interrumpir la partida.
- **Exportación PGN**: Al finalizar la partida, puedes guardarla en formato `.pgn` en la carpeta `partidas_guardadas/`.

---

## 🛠️ Opciones por Línea de Comandos (CLI)

```bash
# === MODO MULTIJUGADOR LOCAL (LAN) ===
# Crear sala como anfitrión (Host)
python3 main.py --host

# Unirse a una sala indicando la IP del anfitrión
python3 main.py --join 192.168.1.50

# Especificar puerto personalizado (por defecto 5050)
python3 main.py --host --port 6000
python3 main.py --join 192.168.1.50 --port 6000

# === MODO INTELIGENCIA ARTIFICIAL ===
# Jugar con blancas automáticamente
python3 main.py --white

# Jugar con negras automáticamente
python3 main.py --black

# Jugar en modo local offline
python3 main.py --offline

# Elegir tema, piezas, tamaño y personalidad directamente
python3 main.py --theme verde --pieces espanol --size grande --personality agresivo
```
