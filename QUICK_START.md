# 🚀 Quick Start Guide

## Prerequisites
- Python 3.7+
- `websockets` library: `pip install --break-system-packages websockets`

## 1. Run Automated Tests (Recommended First Step)
```bash
# Test with automatic server startup/shutdown
python3 test_server.py --auto-server
```

If you see `🎉 All tests passed successfully!`, the system is working perfectly!

## 2. Manual Testing with Browser Interface

### Start the servers:
```bash
# Terminal 1: Start game server
cd server
python3 server.py

# Terminal 2: Start client HTTP server
python3 start_client_server.py
```

### Test the game:
1. Open browser to `http://localhost:8000`
2. Open a second browser window/tab to the same URL
3. First player will see "Aguardando oponente..."
4. Second player joining will start the game
5. Take turns entering angle (0-90°) and force (0-100)
6. Watch health bars decrease with each successful hit!

## 3. Understanding the Game

### Game Rules:
- **Turn-based**: Players alternate making shots
- **Damage system**: 
  - Miss = 0 damage
  - Body hit = ~15 damage  
  - Head shot = ~40 damage
- **Win condition**: Reduce opponent's health to 0

### Controls:
- **Angle**: 0-90 degrees (optimal around 42-45°)
- **Force**: 0-100 power (higher = further range)
- **Physics**: Realistic projectile motion with accuracy-based hit detection

### Tips for Good Shots:
- Try angle 42-45° with force 80-85 for consistent body hits
- Very high or low angles tend to miss
- Each shot has some randomization for realism

## 4. Development

### Project Structure:
- `server/` - Game logic and WebSocket server
- `client/` - HTML interface for testing
- `test_server.py` - Comprehensive test suite

### Adding Features:
1. Game logic changes go in `server/game_state.py` or `server/utils.py`
2. Communication protocol changes need updates in `server/handler.py`
3. UI changes go in `client/index.html`
4. Always add tests to `test_server.py` for new features

### Testing New Changes:
```bash
# Run tests after making changes
python3 test_server.py --auto-server
```

## 5. Troubleshooting

### "Connection refused" error:
- Make sure game server is running: `cd server && python3 server.py`
- Check that port 8765 is not in use: `lsof -i :8765`

### Client page won't load:
- Make sure HTTP server is running: `python3 start_client_server.py`
- Check that port 8000 is available: `lsof -i :8000`

### Tests failing:
- Check that no other server instances are running
- Kill background processes: `pkill -f server.py`
- Restart fresh: `python3 test_server.py --auto-server`

## 6. Architecture Highlights

✅ **Clean separation of concerns**: Game logic, networking, and UI are separate
✅ **Robust error handling**: Invalid moves are rejected with helpful messages  
✅ **Real-time multiplayer**: WebSocket-based instant communication
✅ **Comprehensive testing**: Automated tests cover all major scenarios
✅ **Scalable design**: Multiple concurrent games supported
✅ **Modern web standards**: JSON communication, responsive HTML interface

Ready to play! 🎮