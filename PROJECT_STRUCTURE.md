# 🎮 Multiplayer Game Project Structure

## Architecture Overview

This project implements a real-time multiplayer game using Python WebSockets with a clean separation of concerns. The architecture follows these principles:

- **Server-side game logic**: All game state and rule validation happens on the server
- **Client-side rendering**: HTML/JavaScript clients handle UI and user input
- **JSON communication**: Standardized message protocol between client and server
- **Stateless design**: Each game session is isolated and manageable

## Directory Structure

```
workspace/
├── server/                     # Server-side game logic
│   ├── server.py              # Main WebSocket server & connection management  
│   ├── game_state.py          # Game state management & business logic
│   ├── handler.py             # Move processing & validation
│   └── utils.py               # Physics calculations & damage system
├── client/                    # Client-side interface
│   ├── index.html             # Simple HTML client for testing
│   └── game.html              # Enhanced visual client with animations
├── test_server.py             # Comprehensive automated test suite
├── start_client_server.py     # HTTP server for serving client files
├── requirements.txt           # Python dependencies
└── readme.md                  # Original project documentation
```

## Component Architecture

### 1. Server Components (`/server/`)

#### `server.py` - Connection & Session Management
- **Responsibilities**: WebSocket connections, player matchmaking, game session lifecycle
- **Key Features**:
  - Automatic player pairing (first player waits, second player starts game)
  - Multiple concurrent game sessions
  - Graceful disconnect handling
  - Message broadcasting to game participants

#### `game_state.py` - Game State & Business Logic  
- **Responsibilities**: Game state tracking, turn management, win/lose conditions
- **Key Features**:
  - Per-game state isolation
  - Turn validation and switching
  - Health tracking and damage application
  - Game over detection
  - Move history logging

#### `handler.py` - Move Processing & Validation
- **Responsibilities**: Input validation, move processing, response generation
- **Key Features**:
  - JSON message validation
  - Turn enforcement (prevents out-of-turn moves)
  - Parameter range validation (angle 0-90°, force 0-100)
  - Error handling with descriptive messages

#### `utils.py` - Physics & Game Mechanics
- **Responsibilities**: Projectile physics, hit detection, damage calculation
- **Key Features**:
  - Realistic projectile trajectory calculations
  - Accuracy-based hit system (miss/body/head hits)
  - Damage scaling: 0 pts (miss), 15 pts (body), 40 pts (head)
  - Physics simulation for client visualization

### 2. Client Components (`/client/`)

#### `index.html` - Simple Test Client
- **Responsibilities**: Basic user interface, server communication
- **Key Features**:
  - Real-time connection status
  - Turn-based move input (angle/force sliders)
  - Health bar visualization
  - Message logging and error display

#### `game.html` - Enhanced Visual Client
- **Responsibilities**: Advanced user interface with animations
- **Key Features**:
  - Interactive canvas with drag-to-aim controls
  - Real-time projectile animation with physics
  - Visual player models and battlefield
  - Trajectory preview and aiming assistance
  - Smooth health animations and visual feedback

### 3. Testing & Development Tools

#### `test_server.py` - Automated Test Suite
- **Responsibilities**: Comprehensive server testing, regression prevention
- **Test Coverage**:
  - Basic connection and disconnection
  - Two-player game flow
  - Turn enforcement and validation
  - Invalid input handling
  - Game completion scenarios
  - Multiple concurrent games

#### `start_client_server.py` - Development HTTP Server
- **Responsibilities**: Serving static client files during development
- **Features**: Simple HTTP server for local testing

## Communication Protocol

### Message Types

#### Client → Server
```json
{
  "tipo": "jogada",
  "angulo": 45,      // 0-90 degrees
  "forca": 75        // 0-100 force percentage
}
```

#### Server → Client

**Waiting for opponent:**
```json
{
  "tipo": "espera",
  "mensagem": "Aguardando oponente...",
  "jogador_id": 1,
  "game_id": 1
}
```

**Game start:**
```json
{
  "tipo": "inicio", 
  "mensagem": "Jogo iniciado! Jogador 1 começa.",
  "turno_atual": 1,
  "vidas": {"1": 100, "2": 100}
}
```

**Move result:**
```json
{
  "tipo": "atualizacao",
  "jogador_atual": 1,
  "proximo_turno": 2, 
  "vidas": {"1": 100, "2": 85},
  "dano_causado": 15,
  "impacto": {
    "tipo": "corpo",
    "precisao": 0.65,
    "alcance": 2295.9,
    "distancia_alvo": 80,
    "dano_base": 15
  },
  "jogada": {"jogador": 1, "angulo": 45, "forca": 75},
  "mensagem": "Jogador 1 causou 15 de dano! (corpo)",
  "turno_atual": 2
}
```

**Game over:**
```json
{
  "tipo": "fim_jogo",
  "vencedor": 1,
  "mensagem": "Jogador 1 venceu!"
}
```

**Error handling:**
```json
{
  "tipo": "erro",
  "mensagem": "Não é o seu turno! É o turno do jogador 2."
}
```

## Game Mechanics

### Physics System
- **Projectile motion**: Realistic ballistic trajectory calculation
- **Hit detection**: Accuracy-based system with randomization
- **Damage zones**:
  - Miss (accuracy < 30%): 0 damage
  - Body hit (30% ≤ accuracy < 70%): 15 base damage  
  - Head hit (accuracy ≥ 70%): 40 base damage
- **Precision modifier**: ±20% damage variation based on shot accuracy

### Turn Management
- **Strict turn enforcement**: Server validates each move against current turn
- **Automatic turn switching**: Successful moves advance to next player
- **Turn timeout**: Future enhancement opportunity

### Win Conditions
- **Health depletion**: Player wins when opponent reaches 0 HP
- **Disconnect handling**: Remaining player declared winner

## Scalability Features

### Multiple Concurrent Games
- **Session isolation**: Each game operates independently
- **Dynamic matchmaking**: Players automatically paired as they connect
- **Resource management**: Completed games cleaned up automatically

### Error Resilience
- **Graceful disconnect handling**: Games cleaned up when players leave
- **Input validation**: All user input validated server-side
- **Error recovery**: Descriptive error messages help users correct issues

## Development Workflow

### Running the System
1. **Start game server**: `cd server && python3 server.py`
2. **Start client server**: `python3 start_client_server.py`
3. **Open browsers**: Navigate to `http://localhost:8000`
4. **Test**: Open two browser windows to simulate two players

### Testing
- **Automated tests**: `python3 test_server.py`
- **Auto-server tests**: `python3 test_server.py --auto-server`
- **Manual testing**: Use the HTML client interface

### Future Enhancements
- **Authentication**: Player accounts and login system
- **Rooms/Lobbies**: Private games and spectator mode
- **Enhanced graphics**: Canvas-based game visualization
- **Mobile support**: Touch-friendly interface
- **Chat system**: In-game communication
- **Replay system**: Game recording and playback
- **Tournament mode**: Bracket-style competitions