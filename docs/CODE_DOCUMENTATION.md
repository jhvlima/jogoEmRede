# 📚 Code Documentation

## Project Overview

This is a real-time multiplayer artillery game built with Python (server) and JavaScript (client). Players take turns firing projectiles at each other in an Angry Birds-style gameplay.

## Architecture

```
┌─────────────────┐    WebSocket     ┌─────────────────┐
│   Client (JS)   │ ◄──────────────► │  Server (Python)│
│                 │                  │                 │
│ • HTML Canvas   │                  │ • Game Logic    │
│ • Mouse Input   │                  │ • Turn Management│
│ • Animations    │                  │ • Physics       │
└─────────────────┘                  └─────────────────┘
```

## Server Components

### 📁 `server/server.py`

**Purpose**: Main game server handling client connections and game orchestration.

#### Class: `GameServer`

**Attributes**:
- `host` (str): Server bind address (default: '0.0.0.0')
- `port` (int): Server port (default: 8765)
- `games` (dict): Active games mapping game_id → EstadoDoJogo
- `waiting_players` (list): Players waiting for an opponent
- `connected_clients` (dict): Socket → player info mapping
- `lock` (threading.Lock): Thread synchronization

**Key Methods**:

```python
def send_message(self, client_socket, data):
    """
    Sends JSON message to client with length prefix.
    
    Args:
        client_socket: Target client socket
        data: Dictionary to send as JSON
        
    Error Handling:
        - OSError: Connection issues → cleanup client
        - Exception: General errors → log and ignore
    """

def receive_message(self, client_socket):
    """
    Receives length-prefixed JSON message from client.
    
    Returns:
        dict: Parsed JSON data
        None: If client disconnected or error occurred
        
    Protocol:
        [4 bytes length][message data]
    """

def broadcast_to_game(self, game_id, message):
    """
    Sends message to all players in a specific game.
    
    Args:
        game_id: Target game identifier
        message: Data to broadcast
        
    Safety: Creates socket list copy to prevent modification during iteration
    """

def handle_client(self, client_socket, addr):
    """
    Main client handler - manages entire client lifecycle.
    
    Flow:
        1. Player matchmaking (first player waits, second joins)
        2. Game initialization with state sync
        3. Move processing loop
        4. Game completion and cleanup
        
    Thread Safety: Uses self.lock for shared data access
    """

def cleanup_client(self, client_socket):
    """
    Comprehensive client cleanup and game state management.
    
    Handles:
        - Player removal from games
        - Winner declaration if opponent leaves
        - Game deletion when empty
        - Socket closure
    """
```

**Threading Model**:
- Main thread: Accepts connections
- Worker threads: One per client connection
- Synchronization: Lock-protected shared state

---

### 📁 `server/game_state.py`

**Purpose**: Core game state management and business logic.

#### Class: `EstadoDoJogo`

**Game State Attributes**:
```python
game_id: int              # Unique game identifier
vidas: dict              # {player_id: health_points}
turno: int               # Current player's turn (1 or 2)
players: dict            # {player_id: websocket}
game_started: bool       # True when both players connected
game_over: bool          # True when game finished
winner: int              # Winning player ID
created_at: float        # Game creation timestamp
last_move_time: float    # Last move timestamp
move_history: list       # Complete move history
```

**Key Methods**:

```python
def add_player(self, player_id, websocket):
    """
    Adds player to game and starts game if both players present.
    
    Args:
        player_id: 1 or 2
        websocket: Client connection
        
    Side Effect: Sets game_started=True when 2 players
    """

def is_player_turn(self, player_id):
    """
    Validates if it's the specified player's turn.
    
    Returns:
        bool: True if player can move
        
    Conditions:
        - Must be player's turn
        - Game must be started
        - Game must not be over
    """

def apply_damage(self, target_player, damage):
    """
    Applies damage and checks for game over condition.
    
    Args:
        target_player: Player receiving damage (1 or 2)
        damage: Health points to subtract
        
    Side Effects:
        - Updates player health (minimum 0)
        - Sets game_over=True if health reaches 0
        - Sets winner to surviving player
    """

def next_turn(self):
    """
    Switches to next player's turn.
    
    Logic: turno = 2 if turno == 1 else 1
    Updates: last_move_time to current time
    """

def get_game_state(self):
    """
    Returns complete game state as dictionary.
    
    Useful for: Debugging, logging, state snapshots
    """
```

**Game Flow**:
1. Game created with 100 HP for each player
2. First player joins → waiting state
3. Second player joins → game starts
4. Players alternate turns until one reaches 0 HP

---

### 📁 `server/handler.py`

**Purpose**: Message processing and game move validation.

#### Function: `processar_jogada(jogada_json, jogador_id, game_state)`

**Input Validation**:
```python
# Message type validation
if jogada.get("tipo") != "jogada":
    return error_response

# Turn validation  
if not game_state.is_player_turn(jogador_id):
    return error_response

# Required fields validation
required_fields = ['angulo', 'forca']
missing_fields = [field for field in required_fields if field not in jogada]

# Range validation
if not (0 <= angulo <= 90):
    return error_response
if not (0 <= forca <= 100):
    return error_response
```

**Move Processing Pipeline**:
1. **Parse and validate** JSON input
2. **Check turn** ownership
3. **Validate ranges** (angle: 0-90°, force: 0-100%)
4. **Calculate impact** using physics simulation
5. **Apply damage** to target player
6. **Record move** in game history
7. **Switch turns** (if game continues)
8. **Return response** with updated state

**Response Format**:
```json
{
    "tipo": "atualizacao",
    "jogador_atual": 1,
    "proximo_turno": 2,
    "vidas": {"1": 85, "2": 100},
    "dano_causado": 15,
    "impacto": {"tipo": "corpo", "precisao": 0.75},
    "jogada": {"jogador": 1, "angulo": 45, "forca": 75},
    "mensagem": "Jogador 1 causou 15 de dano! (corpo)",
    "turno_atual": 2
}
```

---

### 📁 `server/utils.py`

**Purpose**: Physics calculations and game mechanics.

#### Function: `calcular_impacto(jogada)`

**Physics Simulation**:
```python
# Input parameters
angulo = jogada.get('angulo', 45)  # degrees
forca = jogada.get('forca', 50)    # percentage (0-100)

# Physics constants
gravidade = 9.8
velocidade_inicial = forca * 2
distancia_alvo = 80  # meters (fixed)

# Projectile range calculation
angulo_rad = math.radians(angulo)
alcance = (velocidade_inicial ** 2 * math.sin(2 * angulo_rad)) / gravidade

# Accuracy calculation
optimal_angle = math.degrees(math.asin(gravidade * distancia_alvo / (velocidade_inicial ** 2)) / 2)
angle_error = abs(angulo - optimal_angle)
accuracy = max(0, (90 - angle_error) / 90) * random_factor
```

**Hit Detection**:
- **Miss** (accuracy < 0.3): 0 damage
- **Body Hit** (accuracy 0.3-0.7): 15 base damage
- **Head Hit** (accuracy > 0.7): 40 base damage

#### Function: `calcular_dano(impacto_info)`

**Damage Calculation**:
```python
# Base damage by hit type
base_damage = {
    'erro': 0,
    'corpo': 15,
    'cabeca': 40
}[impacto_info['tipo']]

# Precision modifier (±20% based on accuracy)
precision_modifier = 0.8 + (impacto_info['precisao'] * 0.4)
final_damage = int(base_damage * precision_modifier)
```

#### Function: `simular_trajetoria(angulo, forca, steps=50)`

**Trajectory Generation**:
```python
# Physics parameters
angulo_rad = math.radians(angulo)
velocidade_inicial = forca * 2
gravidade = 9.8

# Velocity components
vx = velocidade_inicial * math.cos(angulo_rad)
vy = velocidade_inicial * math.sin(angulo_rad)

# Trajectory points
for i in range(steps):
    t = i * dt
    x = vx * t
    y = vy * t - 0.5 * gravidade * t * t
    if y < 0: break  # Hit ground
    trajetoria.append({'x': round(x, 2), 'y': round(y, 2)})
```

---

## Client Components

### 📁 `client/script.js`

**Purpose**: Client-side game interface and server communication.

#### Game State Variables

```javascript
// UI Elements
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const turnMessageEl = document.getElementById('turnMessage');
const p1HpBar = document.getElementById('player1-hp-bar');
const p2HpBar = document.getElementById('player2-hp-bar');

// Game State
let socket;              // WebSocket connection
let playerId = null;     // This player's ID (1 or 2)
let currentTurn = null;  // Whose turn it is
let gameStarted = false; // Game active flag

// Input State  
let isDragging = false;  // Mouse drag state
let dragStart = null;    // Drag start coordinates
let dragEnd = null;      // Drag end coordinates
let projectileAnimation = null; // Animation state
```

#### WebSocket Communication

```javascript
function connectToServer() {
    // ⚠️ BUG: Port should be 8765, not 8766
    socket = new WebSocket(`ws://${window.location.hostname}:8766`);
    
    socket.onopen = () => console.log("Conectado ao servidor.");
    socket.onmessage = handleServerMessage;
    socket.onclose = () => updateTurnMessage("Desconectado.", "red");
    socket.onerror = (err) => console.error("WebSocket Error:", err);
}

function handleServerMessage(event) {
    const data = JSON.parse(event.data);
    switch (data.tipo) {
        case 'espera':     // Waiting for opponent
        case 'inicio':     // Game started
        case 'atualizacao': // Game state update  
        case 'fim_jogo':   // Game ended
        case 'oponente_desconectou': // Opponent left
    }
}
```

#### Input Handling

```javascript
// Mouse interaction for aiming and shooting
canvas.addEventListener('mousedown', (e) => {
    if (currentTurn !== playerId || !gameStarted) return;
    isDragging = true;
    dragStart = getMousePos(e);
    dragEnd = dragStart;
});

canvas.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    dragEnd = getMousePos(e);
    // Shows aiming line in real-time
});

canvas.addEventListener('mouseup', (e) => {
    if (!isDragging) return;
    isDragging = false;
    
    // Convert mouse drag to angle and force
    const dx = dragStart.x - dragEnd.x;
    const dy = dragStart.y - dragEnd.y;
    
    let angle = Math.atan2(dy, dx) * (180 / Math.PI);
    angle = (playerId === 2) ? 180 - angle : angle;
    angle = Math.max(0, Math.min(90, angle));
    
    const distance = Math.sqrt(dx * dx + dy * dy);
    const force = Math.min(100, distance / 3);
    
    sendMove(angle, force);
});
```

#### Animation System

```javascript
function drawGame() {
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw terrain
    drawTerrain();
    
    // Draw players
    drawPlayers();
    
    // Draw aiming line (while dragging)
    if (isDragging && dragEnd) {
        drawAimingLine();
    }
    
    // Animate projectile
    if (projectileAnimation) {
        animateProjectile();
    }
    
    // Continue animation loop
    requestAnimationFrame(drawGame);
}

function animateProjectile() {
    const pos = projectileAnimation.path[projectileAnimation.step];
    if (pos) {
        // Draw projectile at current position
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 5, 0, Math.PI * 2);
        ctx.fillStyle = 'black';
        ctx.fill();
        projectileAnimation.step++;
    } else {
        projectileAnimation = null; // Animation complete
    }
}
```

#### Physics Simulation (Client-side)

```javascript
function simulateTrajectory(startPos, angle, force, shooterId) {
    const angleRad = angle * (Math.PI / 180);
    
    // ⚠️ Different from server physics!
    const initialVelocity = force * 1.5;  // Server uses force * 2
    const gravity = 0.2;                  // Server uses 9.8
    
    const direction = (shooterId === 1) ? 1 : -1;
    let vx = initialVelocity * Math.cos(angleRad) * direction;
    let vy = -initialVelocity * Math.sin(angleRad);
    
    let x = startPos.x;
    let y = startPos.y - startPos.height / 2;
    const path = [];
    
    for (let i = 0; i < 300; i++) {
        vy += gravity;
        x += vx;
        y += vy;
        
        if (y > canvas.height - 50) break; // Hit ground
        path.push({ x, y });
    }
    return path;
}
```

---

### 📁 `client/index.html`

**Purpose**: Game UI structure and styling.

#### HTML Structure

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Batalha de Artilharia para 2 Jogadores</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="style.css">
</head>
<body class="bg-blue-50 flex flex-col items-center justify-center min-h-screen p-4">
    <!-- Game header with title and turn message -->
    <div class="w-full max-w-4xl text-center mb-4 p-4 bg-white rounded-lg shadow-md">
        <h1 class="text-2xl font-bold text-gray-800 mb-2 retro-font">Batalha de Artilharia</h1>
        <p id="turnMessage" class="text-lg font-semibold text-blue-700 h-8"></p>
    </div>

    <!-- Game canvas with overlaid UI elements -->
    <div class="relative w-full max-w-4xl">
        <canvas id="gameCanvas" width="900" height="480"></canvas>
        
        <!-- Player 1 Health Bar (top-left) -->
        <div class="absolute top-4 left-4 w-1/4">
            <div class="player-info">
                <h2 class="font-bold text-blue-600 retro-font text-sm">Jogador 1</h2>
                <div class="hp-bar-container mt-1">
                    <div id="player1-hp-bar" class="hp-bar"></div>
                </div>
            </div>
        </div>
        
        <!-- Player 2 Health Bar (top-right) -->
        <div class="absolute top-4 right-4 w-1/4">
            <div class="player-info text-right">
                <h2 class="font-bold text-red-600 retro-font text-sm">Jogador 2</h2>
                <div class="hp-bar-container mt-1">
                    <div id="player2-hp-bar" class="hp-bar bg-red-500"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Instructions -->
    <div id="instructions" class="mt-4 text-gray-600">
        Clique e arraste no canvas para mirar e atirar!
    </div>

    <script src="script.js"></script>
</body>
</html>
```

#### Key UI Components

1. **Game Canvas**: 900x480px drawing surface
2. **Turn Message**: Dynamic status display
3. **Health Bars**: Visual HP indicators for both players
4. **Responsive Layout**: Tailwind CSS for modern styling

---

## Testing Components

### 📁 `test_server.py`

**Purpose**: Comprehensive automated testing suite.

#### Class: `GameTestClient`

**Test Client Features**:
```python
class GameTestClient:
    def __init__(self, player_name, server_url="ws://localhost:8765"):
        self.player_name = player_name
        self.server_url = server_url
        self.websocket = None
        self.messages = []
        self.connected = False
        self.player_id = None
        
    async def connect(self):
        """Establish WebSocket connection to test server"""
        
    async def listen(self):
        """Listen for messages and store in self.messages"""
        
    async def send_move(self, angle, force):
        """Send a game move to the server"""
        
    def get_latest_message(self, msg_type=None):
        """Get most recent message of specified type"""
```

#### Test Scenarios

1. **Connection Tests**: Server startup, client connection
2. **Matchmaking Tests**: Two-player game creation
3. **Turn Management Tests**: Turn enforcement and switching
4. **Move Validation Tests**: Invalid input rejection
5. **Game Completion Tests**: Win conditions and cleanup
6. **Concurrent Games Tests**: Multiple simultaneous games
7. **Error Handling Tests**: Malformed input, disconnections

---

## Configuration Files

### 📁 `client/style.css`

**Purpose**: Custom styling for game UI.

```css
.retro-font {
    font-family: 'Press Start 2P', cursive;
}

.hp-bar-container {
    width: 100%;
    height: 20px;
    background-color: #e5e7eb;
    border-radius: 10px;
    overflow: hidden;
    border: 2px solid #374151;
}

.hp-bar {
    height: 100%;
    background: linear-gradient(to right, #10b981, #34d399);
    transition: width 0.5s ease;
    border-radius: 8px;
}

#gameCanvas {
    border: 4px solid #374151;
    border-radius: 12px;
    background: linear-gradient(to bottom, #87ceeb 0%, #98fb98 100%);
}
```

### Key Design Principles

1. **Retro Gaming Aesthetic**: Pixel fonts and classic colors
2. **Responsive Design**: Adapts to different screen sizes
3. **Visual Feedback**: Smooth animations and transitions
4. **Accessibility**: High contrast and clear typography

---

## Protocol Specification

### WebSocket Message Format

All messages are JSON with the following structure:

#### Client → Server Messages

```json
{
    "tipo": "jogada",
    "angulo": 45,        // degrees (0-90)
    "forca": 75          // percentage (0-100)
}
```

#### Server → Client Messages

**Waiting for Opponent**:
```json
{
    "tipo": "espera",
    "mensagem": "Aguardando oponente...",
    "jogador_id": 1,
    "game_id": 123
}
```

**Game Started**:
```json
{
    "tipo": "inicio",
    "mensagem": "Jogo iniciado! Jogador 1 começa.",
    "jogador_id": 1,
    "turno_atual": 1,
    "vidas": {"1": 100, "2": 100}
}
```

**Game State Update**:
```json
{
    "tipo": "atualizacao",
    "jogador_atual": 1,
    "proximo_turno": 2,
    "vidas": {"1": 85, "2": 100},
    "dano_causado": 15,
    "impacto": {"tipo": "corpo", "precisao": 0.75},
    "jogada": {"jogador": 1, "angulo": 45, "forca": 75},
    "mensagem": "Jogador 1 causou 15 de dano! (corpo)",
    "turno_atual": 2
}
```

**Game End**:
```json
{
    "tipo": "fim_jogo",
    "vencedor": 2,
    "mensagem": "Jogador 2 venceu!"
}
```

**Error Message**:
```json
{
    "tipo": "erro",
    "mensagem": "Não é o seu turno!"
}
```

---

## Development Guidelines

### Code Style

1. **Python**: Follow PEP 8, use type hints where possible
2. **JavaScript**: Use modern ES6+ features, consistent naming
3. **Error Handling**: Comprehensive try-catch blocks
4. **Logging**: Use structured logging with appropriate levels

### Testing

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Full game scenarios
4. **Performance Tests**: Load and stress testing

### Security

1. **Input Validation**: Validate all user input
2. **Rate Limiting**: Prevent spam and DoS attacks  
3. **Authentication**: Add user authentication system
4. **Sanitization**: Clean all user-provided data

### Performance

1. **Connection Pooling**: Use async/await for better scalability
2. **Memory Management**: Clean up resources properly
3. **Caching**: Cache frequently accessed data
4. **Monitoring**: Add performance metrics and logging