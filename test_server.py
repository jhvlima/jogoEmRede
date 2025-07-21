#!/usr/bin/env python3
"""
Comprehensive test suite for the multiplayer game server
"""

import asyncio
import websockets
import json
import time
from threading import Thread
import sys
import os

# Add server directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

class GameTestClient:
    def __init__(self, player_name, server_url="ws://localhost:8765"):
        self.player_name = player_name
        self.server_url = server_url
        self.websocket = None
        self.messages = []
        self.connected = False
        self.player_id = None
        
    async def connect(self):
        """Connect to the game server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            print(f"[{self.player_name}] Connected to server")
            return True
        except Exception as e:
            print(f"[{self.player_name}] Failed to connect: {e}")
            return False
    
    async def listen(self):
        """Listen for messages from server"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.messages.append(data)
                print(f"[{self.player_name}] Received: {data}")
                
                # Store player ID when game starts
                if data.get('tipo') == 'espera' and 'jogador_id' in data:
                    self.player_id = data['jogador_id']
                elif data.get('tipo') == 'inicio':
                    # Game started, determine player ID from turn info
                    if not self.player_id:
                        # Assume we're player 2 if we don't have an ID yet
                        self.player_id = 2
                        
        except websockets.ConnectionClosed:
            print(f"[{self.player_name}] Connection closed")
            self.connected = False
        except Exception as e:
            print(f"[{self.player_name}] Error listening: {e}")
            self.connected = False
    
    async def send_move(self, angulo, forca):
        """Send a move to the server"""
        if not self.connected or not self.websocket:
            return False
            
        move = {
            "tipo": "jogada",
            "angulo": angulo,
            "forca": forca
        }
        
        try:
            await self.websocket.send(json.dumps(move))
            print(f"[{self.player_name}] Sent move: angle={angulo}, force={forca}")
            return True
        except Exception as e:
            print(f"[{self.player_name}] Failed to send move: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            print(f"[{self.player_name}] Disconnected")
    
    def get_last_message(self, message_type=None):
        """Get the last message of a specific type"""
        if message_type:
            for msg in reversed(self.messages):
                if msg.get('tipo') == message_type:
                    return msg
        return self.messages[-1] if self.messages else None

async def test_basic_connection():
    """Test basic server connection"""
    print("\n=== Testing Basic Connection ===")
    
    client = GameTestClient("TestPlayer1")
    
    # Test connection
    connected = await client.connect()
    assert connected, "Should be able to connect to server"
    
    # Wait for initial message and start listening
    listen_task = asyncio.create_task(client.listen())
    await asyncio.sleep(1.0)  # Increased wait time
    
    # Should receive waiting message
    last_msg = client.get_last_message()
    assert last_msg and last_msg.get('tipo') == 'espera', f"Expected 'espera' message, got {last_msg}"
    
    # Clean up
    listen_task.cancel()
    
    await client.disconnect()
    print("✓ Basic connection test passed")

async def test_two_player_game():
    """Test full two-player game scenario"""
    print("\n=== Testing Two-Player Game ===")
    
    # Create two test clients
    player1 = GameTestClient("Player1")
    player2 = GameTestClient("Player2")
    
    # Connect both players
    assert await player1.connect(), "Player 1 should connect"
    assert await player2.connect(), "Player 2 should connect"
    
    # Start listening tasks
    task1 = asyncio.create_task(player1.listen())
    task2 = asyncio.create_task(player2.listen())
    
    # Wait for game to start
    await asyncio.sleep(1)
    
    # Both players should have received game start message
    p1_msg = player1.get_last_message('inicio')
    p2_msg = player2.get_last_message('inicio')
    
    assert p1_msg, "Player 1 should receive game start message"
    assert p2_msg, "Player 2 should receive game start message"
    
    print("✓ Game started successfully")
    
    # Test game moves
    moves_tested = 0
    current_turn = 1
    
    for round_num in range(3):  # Test 3 rounds
        print(f"\n--- Round {round_num + 1} ---")
        
        # Player 1's turn
        if current_turn == 1:
            success = await player1.send_move(45, 75)  # Good shot
            assert success, "Player 1 move should be sent successfully"
            moves_tested += 1
            
            await asyncio.sleep(0.5)  # Wait for server response
            
            # Check if both players received update
            p1_update = player1.get_last_message('atualizacao')
            p2_update = player2.get_last_message('atualizacao')
            
            assert p1_update, "Player 1 should receive game update"
            assert p2_update, "Player 2 should receive game update"
            
            current_turn = 2
        
        # Player 2's turn  
        if current_turn == 2:
            success = await player2.send_move(50, 80)  # Good shot
            assert success, "Player 2 move should be sent successfully"
            moves_tested += 1
            
            await asyncio.sleep(0.5)
            
            # Check updates
            p1_update = player1.get_last_message('atualizacao')
            p2_update = player2.get_last_message('atualizacao')
            
            assert p1_update, "Player 1 should receive update after P2 move"
            assert p2_update, "Player 2 should receive update after P2 move"
            
            current_turn = 1
    
    print(f"✓ Successfully tested {moves_tested} moves")
    
    # Test invalid move (wrong turn)
    print("\n--- Testing Invalid Moves ---")
    
    # Try to make move when it's not your turn
    if current_turn == 1:
        await player2.send_move(30, 60)  # Player 2 tries to move on P1's turn
    else:
        await player1.send_move(30, 60)  # Player 1 tries to move on P2's turn
    
    await asyncio.sleep(0.5)
    
    # Should receive error message
    error_msg = player2.get_last_message('erro') if current_turn == 1 else player1.get_last_message('erro')
    assert error_msg, "Should receive error for invalid turn"
    print("✓ Invalid turn properly rejected")
    
    # Clean up
    task1.cancel()
    task2.cancel()
    await player1.disconnect()
    await player2.disconnect()
    
    print("✓ Two-player game test passed")

async def test_invalid_moves():
    """Test various invalid move scenarios"""
    print("\n=== Testing Invalid Moves ===")
    
    player1 = GameTestClient("TestPlayer1")
    player2 = GameTestClient("TestPlayer2")
    
    await player1.connect()
    await player2.connect()
    
    task1 = asyncio.create_task(player1.listen())
    task2 = asyncio.create_task(player2.listen())
    
    await asyncio.sleep(1)  # Wait for game start
    
    # Test invalid JSON
    if player1.websocket:
        await player1.websocket.send("invalid json")
        await asyncio.sleep(0.2)
    
    # Test missing fields
    invalid_move = {"tipo": "jogada", "angulo": 45}  # Missing 'forca'
    await player1.websocket.send(json.dumps(invalid_move))
    await asyncio.sleep(0.2)
    
    # Test invalid ranges
    invalid_move2 = {"tipo": "jogada", "angulo": 150, "forca": 75}  # Invalid angle
    await player1.websocket.send(json.dumps(invalid_move2))
    await asyncio.sleep(0.2)
    
    invalid_move3 = {"tipo": "jogada", "angulo": 45, "forca": 150}  # Invalid force
    await player1.websocket.send(json.dumps(invalid_move3))
    await asyncio.sleep(0.2)
    
    # Should receive error messages
    error_count = len([msg for msg in player1.messages if msg.get('tipo') == 'erro'])
    assert error_count >= 3, f"Should receive at least 3 error messages, got {error_count}"
    
    print("✓ Invalid moves properly rejected")
    
    task1.cancel()
    task2.cancel()
    await player1.disconnect()
    await player2.disconnect()

async def test_game_completion():
    """Test game completion scenario"""
    print("\n=== Testing Game Completion ===")
    
    player1 = GameTestClient("Player1")
    player2 = GameTestClient("Player2")
    
    await player1.connect()
    await player2.connect()
    
    task1 = asyncio.create_task(player1.listen())
    task2 = asyncio.create_task(player2.listen())
    
    await asyncio.sleep(1)
    
    # Simulate a game where player 1 wins by doing enough damage
    # We'll send multiple high-damage moves
    for i in range(4):  # Should be enough to kill opponent
        if i % 2 == 0:  # Player 1's turn
            await player1.send_move(42, 85)  # Optimal shot for headshot
        else:  # Player 2's turn
            await player2.send_move(45, 70)  # Decent shot
        
        await asyncio.sleep(0.5)
        
        # Check for game over
        game_over_msg = player1.get_last_message('fim_jogo')
        if game_over_msg:
            print(f"✓ Game ended with winner: {game_over_msg.get('vencedor')}")
            break
    
    task1.cancel()
    task2.cancel()
    await player1.disconnect()
    await player2.disconnect()

async def run_all_tests():
    """Run all test scenarios"""
    print("Starting Game Server Tests...")
    print("Make sure the server is running on localhost:8765")
    
    try:
        await test_basic_connection()
        await test_two_player_game()
        await test_invalid_moves()
        await test_game_completion()
        
        print("\n🎉 All tests passed successfully!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False
    
    return True

def start_server_for_testing():
    """Start the server in a separate process for testing"""
    import subprocess
    import time
    
    # Start server
    server_process = subprocess.Popen([
        sys.executable, 
        os.path.join(os.path.dirname(__file__), 'server', 'server.py')
    ])
    
    # Wait for server to start
    time.sleep(2)
    
    return server_process

if __name__ == "__main__":
    # Option to auto-start server for testing
    if "--auto-server" in sys.argv:
        print("Starting server automatically...")
        server_process = start_server_for_testing()
        
        try:
            # Run tests
            result = asyncio.run(run_all_tests())
        finally:
            # Clean up server
            server_process.terminate()
            server_process.wait()
        
        sys.exit(0 if result else 1)
    else:
        # Manual mode - expect server to be running
        result = asyncio.run(run_all_tests())
        sys.exit(0 if result else 1)