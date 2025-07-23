# 📋 API Reference

## Server API

### GameServer Class

#### Constructor
```python
GameServer(host='0.0.0.0', port=8765)
```
Creates a new game server instance.

**Parameters:**
- `host` (str): IP address to bind to (default: '0.0.0.0' for all interfaces)
- `port` (int): Port number to listen on (default: 8765)

#### Methods

##### `send_message(client_socket, data)`
Sends a JSON message to a specific client with length prefix.

**Parameters:**
- `client_socket` (socket): Target client socket connection
- `data` (dict): Data to send as JSON

**Protocol:**
```
[4 bytes: message length in big-endian][JSON message data]
```

**Error Handling:**
- `OSError`: Network connection issues → calls `cleanup_client()`
- `Exception`: General errors → logs error and continues

**Example:**
```python
server.send_message(client_socket, {
    "tipo": "espera",
    "mensagem": "Aguardando oponente...",
    "jogador_id": 1
})
```

##### `receive_message(client_socket)`
Receives a length-prefixed JSON message from client.

**Returns:**
- `dict`: Parsed JSON message
- `None`: If client disconnected or error occurred

**Error Handling:**
- `ConnectionResetError`: Client disconnected → returns `None`
- `BrokenPipeError`: Connection broken → returns `None`
- `Exception`: Parse/network errors → logs and returns `None`

##### `broadcast_to_game(game_id, message)`
Sends a message to all players in a specific game.

**Parameters:**
- `game_id` (int): Target game identifier
- `message` (dict): Message to broadcast

**Safety Features:**
- Creates copy of player socket list to prevent iteration issues
- Handles individual send failures gracefully

##### `handle_client(client_socket, addr)`
Main client connection handler (runs in separate thread).

**Game Flow:**
1. **Matchmaking Phase:**
   - First player creates new game and waits
   - Second player joins existing game
   
2. **Game Setup:**
   - Both players receive game start notification
   - Initial game state synchronization
   
3. **Gameplay Loop:**
   - Receive and process player moves
   - Broadcast state updates
   - Check for game completion
   
4. **Cleanup:**
   - Handle disconnections
   - Clean up game resources

**Thread Safety:**
Uses `self.lock` for all shared data access.

##### `cleanup_client(client_socket)`
Comprehensive client cleanup and resource management.

**Cleanup Operations:**
- Remove client from connected clients list
- Remove from waiting players queue
- Remove player from active game
- Declare winner if opponent remains
- Delete empty games
- Close socket connection

**Game State Management:**
- Handles partial game cleanup (one player leaves)
- Manages complete game cleanup (both players leave)
- Prevents resource leaks

##### `start()`
Starts the server and enters main accept loop.

**Server Lifecycle:**
1. Bind to host:port
2. Listen for connections (queue size: 5)
3. Accept connections in infinite loop
4. Spawn thread for each client
5. Handle shutdown gracefully on KeyboardInterrupt

---

### EstadoDoJogo Class

#### Constructor
```python
EstadoDoJogo(game_id)
```

**Initial State:**
- Both players start with 100 HP
- Player 1 goes first
- Game not started until both players join
- Empty move history

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `game_id` | int | Unique game identifier |
| `vidas` | dict | `{1: hp1, 2: hp2}` player health |
| `turno` | int | Current player turn (1 or 2) |
| `players` | dict | `{player_id: websocket}` connections |
| `game_started` | bool | True when both players connected |
| `game_over` | bool | True when game finished |
| `winner` | int | Winning player ID (1 or 2) |
| `created_at` | float | Game creation timestamp |
| `last_move_time` | float | Last move timestamp |
| `move_history` | list | Complete move history |

#### Methods

##### `add_player(player_id, websocket)`
Adds a player to the game.

**Parameters:**
- `player_id` (int): Player identifier (1 or 2)
- `websocket` (socket): Player's connection

**Side Effects:**
- Sets `game_started = True` when second player joins
- Enables move processing

##### `is_player_turn(player_id)`
Validates if specified player can make a move.

**Parameters:**
- `player_id` (int): Player to check

**Returns:**
- `bool`: True if player can move

**Validation Rules:**
- Must be player's turn (`self.turno == player_id`)
- Game must be started (`self.game_started == True`)
- Game must not be over (`self.game_over == False`)

##### `apply_damage(target_player, damage)`
Applies damage to a player and checks for game over.

**Parameters:**
- `target_player` (int): Player receiving damage (1 or 2)
- `damage` (int): Health points to subtract

**Game Over Logic:**
- Health cannot go below 0
- Game ends when any player reaches 0 HP
- Winner is the surviving player

**Side Effects:**
- Updates `self.vidas[target_player]`
- May set `self.game_over = True`
- May set `self.winner`

##### `next_turn()`
Switches to the next player's turn.

**Logic:**
```python
self.turno = 2 if self.turno == 1 else 1
self.last_move_time = time.time()
```

**Precondition:**
- Only call if game is not over
- Handler is responsible for checking game state

##### `get_game_state()`
Returns complete game state as dictionary.

**Returns:**
```python
{
    'game_id': int,
    'vidas': dict,
    'turno': int,
    'game_started': bool,
    'game_over': bool,
    'winner': int or None,
    'players_connected': int
}
```

**Use Cases:**
- Debugging and logging
- State snapshots
- Client synchronization

##### `add_move_to_history(player_id, move_data)`
Records a move in the game history.

**Parameters:**
- `player_id` (int): Player making the move
- `move_data` (dict): Complete move information

**History Entry Format:**
```python
{
    'player_id': int,
    'timestamp': float,
    'move_data': dict
}
```

**⚠️ Memory Warning:**
History grows indefinitely - no cleanup mechanism implemented.

---

### Handler Functions

#### `processar_jogada(jogada_json, jogador_id, game_state)`
Processes a player move and returns game state update.

**Parameters:**
- `jogada_json` (str): JSON string containing move data
- `jogador_id` (int): Player making the move (1 or 2)
- `game_state` (EstadoDoJogo): Current game state

**Input Validation:**

1. **JSON Format:**
   ```python
   jogada = json.loads(jogada_json)  # May raise JSONDecodeError
   ```

2. **Message Type:**
   ```python
   if jogada.get("tipo") != "jogada":
       return error_response
   ```

3. **Turn Validation:**
   ```python
   if not game_state.is_player_turn(jogador_id):
       return error_response
   ```

4. **Required Fields:**
   ```python
   required_fields = ['angulo', 'forca']
   missing_fields = [field for field in required_fields if field not in jogada]
   ```

5. **Range Validation:**
   ```python
   if not (0 <= angulo <= 90):
       return error_response
   if not (0 <= forca <= 100):
       return error_response
   ```

**Processing Pipeline:**
1. Parse and validate input
2. Calculate impact using physics
3. Determine damage amount
4. Apply damage to opponent
5. Record move in history
6. Switch turns (if game continues)
7. Prepare response message

**Return Values:**

**Success Response:**
```python
{
    "tipo": "atualizacao",
    "jogador_atual": int,
    "proximo_turno": int,
    "vidas": dict,
    "dano_causado": int,
    "impacto": dict,
    "jogada": dict,
    "mensagem": str,
    "turno_atual": int,
    # Optional fields if game over:
    "game_over": bool,
    "vencedor": int
}
```

**Error Response:**
```python
{
    "tipo": "erro",
    "mensagem": str
}
```

---

### Utility Functions

#### `calcular_impacto(jogada)`
Calculates projectile impact based on physics simulation.

**Parameters:**
- `jogada` (dict): Move data containing `angulo` and `forca`

**Physics Model:**
```python
# Input parameters
angulo = jogada.get('angulo', 45)    # degrees (0-90)
forca = jogada.get('forca', 50)      # percentage (0-100)

# Constants
gravidade = 9.8                      # m/s²
velocidade_inicial = forca * 2       # scaling factor
distancia_alvo = 80                  # meters (fixed)

# Projectile range calculation
angulo_rad = math.radians(angulo)
alcance = (velocidade_inicial ** 2 * math.sin(2 * angulo_rad)) / gravidade

# Accuracy calculation
optimal_angle = math.degrees(math.asin(gravidade * distancia_alvo / (velocidade_inicial ** 2)) / 2)
angle_error = abs(angulo - optimal_angle)
accuracy = max(0, (90 - angle_error) / 90) * random.uniform(0.8, 1.2)
```

**Hit Detection Thresholds:**
- `accuracy < 0.3`: Miss (0 damage)
- `0.3 ≤ accuracy < 0.7`: Body hit (15 base damage)
- `accuracy ≥ 0.7`: Head hit (40 base damage)

**Returns:**
```python
{
    'tipo': str,           # 'erro', 'corpo', or 'cabeca'
    'precisao': float,     # 0.0 to 1.0+
    'alcance': float,      # calculated range in meters
    'distancia_alvo': int, # target distance (80m)
    'dano_base': int       # base damage before modifiers
}
```

#### `calcular_dano(impacto_info)`
Calculates final damage with precision modifiers.

**Parameters:**
- `impacto_info` (dict): Impact information from `calcular_impacto()`

**Damage Calculation:**
```python
# Base damage by hit type
base_damage_map = {
    'erro': 0,
    'corpo': 15,
    'cabeca': 40
}
base_damage = base_damage_map[impacto_info['tipo']]

# Precision modifier (±20% based on accuracy)
precision_modifier = 0.8 + (impacto_info['precisao'] * 0.4)
final_damage = int(base_damage * precision_modifier)

return max(0, final_damage)
```

**Examples:**
- Perfect head shot (accuracy=1.0): `40 * 1.2 = 48 damage`
- Poor body shot (accuracy=0.3): `15 * 0.92 = 13 damage`
- Near miss (accuracy=0.2): `0 damage`

#### `validar_jogada(jogada)`
Validates move data structure and ranges.

**Parameters:**
- `jogada` (dict): Move data to validate

**Validation Checks:**
1. Required fields present: `['tipo', 'angulo', 'forca']`
2. Message type is `'jogada'`
3. Numeric value validation
4. Range validation: `0 ≤ angulo ≤ 90`, `0 ≤ forca ≤ 100`

**Returns:**
- `(True, "Jogada válida")` on success
- `(False, error_message)` on failure

#### `simular_trajetoria(angulo, forca, steps=50)`
Generates projectile trajectory points for visualization.

**Parameters:**
- `angulo` (float): Launch angle in degrees
- `forca` (float): Launch force percentage
- `steps` (int): Number of trajectory points to generate

**Physics Simulation:**
```python
# Initial conditions
angulo_rad = math.radians(angulo)
velocidade_inicial = forca * 2
gravidade = 9.8

# Velocity components
vx = velocidade_inicial * math.cos(angulo_rad)
vy = velocidade_inicial * math.sin(angulo_rad)

# Generate trajectory points
dt = 0.1  # time step
for i in range(steps):
    t = i * dt
    x = vx * t
    y = vy * t - 0.5 * gravidade * t * t
    if y < 0: break  # hit ground
    trajectory.append({'x': round(x, 2), 'y': round(y, 2)})
```

**Returns:**
```python
[
    {'x': 0.0, 'y': 0.0},
    {'x': 1.5, 'y': 1.2},
    # ... more points
]
```

**Use Cases:**
- Client-side trajectory preview
- Server-side hit detection verification
- Animation path generation

---

## Client API

### WebSocket Connection

#### Connection Setup
```javascript
const socket = new WebSocket(`ws://${hostname}:8765`);

socket.onopen = onConnectionOpen;
socket.onmessage = handleServerMessage;
socket.onclose = onConnectionClose;
socket.onerror = onConnectionError;
```

#### Message Handling
```javascript
function handleServerMessage(event) {
    const data = JSON.parse(event.data);
    
    switch (data.tipo) {
        case 'espera':              // Waiting for opponent
        case 'inicio':              // Game started
        case 'atualizacao':         // Game state update
        case 'fim_jogo':            // Game ended
        case 'oponente_desconectou': // Opponent disconnected
        case 'erro':                // Error message
    }
}
```

### Game State Management

#### State Variables
```javascript
let socket;              // WebSocket connection
let playerId = null;     // This player's ID (1 or 2)
let currentTurn = null;  // Whose turn it is
let gameStarted = false; // Game active flag
let isDragging = false;  // Mouse input state
let projectileAnimation = null; // Animation state
```

#### State Updates
```javascript
function updateGameState(data) {
    // Update turn information
    if (data.turno_atual !== undefined) {
        currentTurn = data.turno_atual;
    }
    
    // Update health bars
    if (data.vidas) {
        updateHealthBars(data.vidas);
    }
    
    // Update turn message
    if (currentTurn === playerId) {
        showMessage("Seu turno! Mire e atire.", "green");
    } else {
        showMessage(`Aguardando Jogador ${currentTurn}...`, "gray");
    }
}
```

### Input Handling

#### Mouse Events
```javascript
canvas.addEventListener('mousedown', (e) => {
    if (currentTurn !== playerId || !gameStarted) return;
    
    isDragging = true;
    dragStart = getMousePosition(e);
    dragEnd = dragStart;
});

canvas.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    dragEnd = getMousePosition(e);
    // Update aiming line display
});

canvas.addEventListener('mouseup', (e) => {
    if (!isDragging) return;
    isDragging = false;
    
    // Calculate angle and force from drag vector
    const { angle, force } = calculateAimFromDrag(dragStart, dragEnd);
    
    // Send move to server
    sendMove(angle, force);
    
    // Clear aiming line
    dragEnd = null;
});
```

#### Move Calculation
```javascript
function calculateAimFromDrag(start, end) {
    const dx = start.x - end.x;
    const dy = start.y - end.y;
    
    // Calculate angle
    let angle = Math.atan2(dy, dx) * (180 / Math.PI);
    
    // Adjust for player position
    if (playerId === 2) {
        angle = 180 - angle;
    }
    
    // Clamp to valid range
    angle = Math.max(0, Math.min(90, angle));
    
    // Calculate force from drag distance
    const distance = Math.sqrt(dx * dx + dy * dy);
    const force = Math.min(100, distance / 3);
    
    return { angle, force };
}
```

### Rendering System

#### Game Loop
```javascript
function gameLoop() {
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw game elements
    drawTerrain();
    drawPlayers();
    drawAimingLine();
    drawProjectile();
    
    // Continue loop
    requestAnimationFrame(gameLoop);
}
```

#### Player Rendering
```javascript
function drawPlayers() {
    for (const [id, player] of Object.entries(players)) {
        ctx.fillStyle = player.color;
        ctx.fillRect(
            player.x - player.width / 2,
            player.y - player.height,
            player.width,
            player.height
        );
        
        // Highlight current player
        if (parseInt(id) === currentTurn) {
            ctx.strokeStyle = 'gold';
            ctx.lineWidth = 3;
            ctx.strokeRect(
                player.x - player.width / 2 - 2,
                player.y - player.height - 2,
                player.width + 4,
                player.height + 4
            );
        }
    }
}
```

#### Animation System
```javascript
function animateProjectile() {
    if (!projectileAnimation) return;
    
    const { path, step } = projectileAnimation;
    const position = path[step];
    
    if (position) {
        // Draw projectile
        ctx.beginPath();
        ctx.arc(position.x, position.y, 5, 0, Math.PI * 2);
        ctx.fillStyle = 'black';
        ctx.fill();
        
        // Advance animation
        projectileAnimation.step++;
    } else {
        // Animation complete
        projectileAnimation = null;
    }
}
```

### Physics Simulation (Client)

#### Trajectory Calculation
```javascript
function simulateTrajectory(startPos, angle, force, shooterId) {
    const angleRad = angle * (Math.PI / 180);
    
    // Physics parameters (different from server!)
    const initialVelocity = force * 1.5;
    const gravity = 0.2;
    
    // Direction based on player
    const direction = (shooterId === 1) ? 1 : -1;
    
    // Initial velocity components
    let vx = initialVelocity * Math.cos(angleRad) * direction;
    let vy = -initialVelocity * Math.sin(angleRad);
    
    // Starting position
    let x = startPos.x;
    let y = startPos.y - startPos.height / 2;
    
    const path = [];
    
    // Simulate trajectory
    for (let i = 0; i < 300; i++) {
        vy += gravity;  // Apply gravity
        x += vx;
        y += vy;
        
        // Check ground collision
        if (y > canvas.height - 50) break;
        
        path.push({ x, y });
    }
    
    return path;
}
```

**⚠️ Physics Inconsistency:**
Client uses different physics parameters than server:
- Server: `gravity = 9.8`, `velocity = force * 2`
- Client: `gravity = 0.2`, `velocity = force * 1.5`

This causes trajectory preview to not match actual server calculations.

---

## Message Protocol

### Client → Server Messages

#### Move Message
```json
{
    "tipo": "jogada",
    "angulo": 45,        // degrees (0-90)
    "forca": 75          // percentage (0-100)
}
```

**Validation Rules:**
- `tipo` must be exactly `"jogada"`
- `angulo` must be number between 0 and 90
- `forca` must be number between 0 and 100
- Both fields are required

### Server → Client Messages

#### Waiting Message
```json
{
    "tipo": "espera",
    "mensagem": "Aguardando oponente...",
    "jogador_id": 1,
    "game_id": 123
}
```

Sent when first player connects and waits for opponent.

#### Game Start Message
```json
{
    "tipo": "inicio",
    "mensagem": "Jogo iniciado! Jogador 1 começa.",
    "jogador_id": 1,
    "turno_atual": 1,
    "vidas": {"1": 100, "2": 100}
}
```

Sent to both players when second player joins.

#### Game Update Message
```json
{
    "tipo": "atualizacao",
    "jogador_atual": 1,
    "proximo_turno": 2,
    "vidas": {"1": 85, "2": 100},
    "dano_causado": 15,
    "impacto": {
        "tipo": "corpo",
        "precisao": 0.75,
        "alcance": 82.5,
        "distancia_alvo": 80,
        "dano_base": 15
    },
    "jogada": {
        "jogador": 1,
        "angulo": 45,
        "forca": 75
    },
    "mensagem": "Jogador 1 causou 15 de dano! (corpo)",
    "turno_atual": 2
}
```

Sent after each successful move.

#### Game End Message
```json
{
    "tipo": "fim_jogo",
    "vencedor": 2,
    "mensagem": "Jogador 2 venceu!"
}
```

Sent when a player's health reaches zero.

#### Disconnect Message
```json
{
    "tipo": "oponente_desconectou",
    "vencedor": 1,
    "mensagem": "Oponente desconectou. Você venceu!"
}
```

Sent when opponent leaves the game.

#### Error Message
```json
{
    "tipo": "erro",
    "mensagem": "Não é o seu turno!"
}
```

Sent for various error conditions:
- Invalid move format
- Wrong turn
- Invalid ranges
- Game not started
- JSON parse errors

---

## Error Codes and Handling

### Server Errors

| Error Type | Message | Cause | Resolution |
|------------|---------|-------|------------|
| Turn Error | "Não é o seu turno!" | Player moves out of turn | Wait for correct turn |
| Format Error | "Tipo de mensagem inválido" | Wrong message type | Send "jogada" type |
| Data Error | "Dados da jogada incompletos" | Missing fields | Include angulo and forca |
| Range Error | "Ângulo deve estar entre 0 e 90" | Invalid angle | Check input range |
| Range Error | "Força deve estar entre 0 e 100" | Invalid force | Check input range |
| Parse Error | "JSON inválido recebido" | Malformed JSON | Fix JSON format |
| Internal Error | "Erro interno ao processar jogada" | Server exception | Check server logs |

### Client Errors

| Error Type | Cause | Symptoms | Resolution |
|------------|-------|----------|------------|
| Connection Error | Server not running | "Desconectado" message | Start server |
| Port Error | Wrong port number | Connection timeout | Check port 8765 |
| Protocol Error | Wrong protocol | Connection fails | Use WebSocket |
| Input Error | Invalid mouse input | No movement sent | Check drag calculation |

### Network Errors

| Error Type | Description | Recovery |
|------------|-------------|----------|
| Connection Reset | Client disconnects abruptly | Server cleans up automatically |
| Broken Pipe | Network connection lost | Server removes client from game |
| Timeout | No response from client | Implement timeout handling |
| Message Corruption | Invalid message format | Validation rejects message |

---

## Performance Considerations

### Server Performance

#### Threading Model
- **Main Thread**: Accepts new connections
- **Worker Threads**: One per client connection
- **Synchronization**: Lock-protected shared state

#### Memory Usage
- **Games Dictionary**: Grows with concurrent games
- **Move History**: Grows indefinitely (memory leak)
- **Client Connections**: Cleaned up on disconnect

#### Scalability Limits
- **Thread Limit**: OS-dependent thread limits
- **Memory Growth**: Unbounded history storage
- **CPU Usage**: JSON parsing and physics calculations

### Client Performance

#### Rendering
- **60 FPS Target**: Uses `requestAnimationFrame`
- **Canvas Clearing**: Full redraw each frame
- **Animation**: Smooth projectile trajectories

#### Memory Usage
- **Trajectory Storage**: Temporary arrays for animation
- **Event Handlers**: Proper cleanup on page unload
- **WebSocket**: Automatic reconnection not implemented

### Optimization Recommendations

1. **Server Optimizations:**
   - Implement connection pooling with async/await
   - Add move history size limits
   - Use message queues for broadcasting
   - Add connection timeouts

2. **Client Optimizations:**
   - Implement dirty rectangle rendering
   - Add object pooling for animations
   - Compress trajectory data
   - Add offline mode support

3. **Network Optimizations:**
   - Use binary protocols for high-frequency data
   - Implement message compression
   - Add delta compression for state updates
   - Use WebRTC for peer-to-peer communication