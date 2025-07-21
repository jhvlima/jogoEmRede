import asyncio
import websockets
import json
import logging
from handler import processar_jogada
from game_state import EstadoDoJogo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameServer:
    def __init__(self):
        self.games = {}  # game_id -> game_instance
        self.waiting_players = []
        self.connected_clients = {}  # websocket -> player_info
    
    async def handle_client(self, websocket):
        try:
            logger.info(f"New client connected: {websocket.remote_address}")
            
            # Add to waiting players or create/join game
            if len(self.waiting_players) == 0:
                # First player - create new game
                game_id = len(self.games) + 1
                game = EstadoDoJogo(game_id)
                self.games[game_id] = game
                
                player_info = {
                    'game_id': game_id,
                    'player_id': 1,
                    'websocket': websocket
                }
                
                game.add_player(1, websocket)
                self.connected_clients[websocket] = player_info
                self.waiting_players.append(player_info)
                
                await websocket.send(json.dumps({
                    "tipo": "espera",
                    "mensagem": "Aguardando oponente...",
                    "jogador_id": 1,
                    "game_id": game_id
                }))
                
            else:
                # Second player - join existing game
                waiting_player = self.waiting_players.pop(0)
                game_id = waiting_player['game_id']
                game = self.games[game_id]
                
                player_info = {
                    'game_id': game_id,
                    'player_id': 2,
                    'websocket': websocket
                }
                
                game.add_player(2, websocket)
                self.connected_clients[websocket] = player_info
                
                # Notify both players that game is starting
                await self.broadcast_to_game(game_id, {
                    "tipo": "inicio",
                    "mensagem": "Jogo iniciado! Jogador 1 começa.",
                    "turno_atual": game.turno,
                    "vidas": game.vidas
                })
            
            # Listen for messages
            async for message in websocket:
                await self.handle_message(websocket, message)
                
        except websockets.ConnectionClosed:
            logger.info(f"Client disconnected: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            await self.cleanup_client(websocket)
    
    async def handle_message(self, websocket, message):
        try:
            if websocket not in self.connected_clients:
                return
                
            player_info = self.connected_clients[websocket]
            game_id = player_info['game_id']
            player_id = player_info['player_id']
            
            if game_id not in self.games:
                return
                
            game = self.games[game_id]
            
            # Process the move
            resposta = processar_jogada(message, player_id, game)
            
            # Broadcast response to both players
            await self.broadcast_to_game(game_id, resposta)
            
            # Check for game over
            if game.is_game_over():
                winner = game.get_winner()
                await self.broadcast_to_game(game_id, {
                    "tipo": "fim_jogo",
                    "vencedor": winner,
                    "mensagem": f"Jogador {winner} venceu!"
                })
                # Clean up the game
                del self.games[game_id]
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await websocket.send(json.dumps({
                "tipo": "erro",
                "mensagem": "Erro interno do servidor"
            }))
    
    async def broadcast_to_game(self, game_id, message):
        if game_id not in self.games:
            return
            
        game = self.games[game_id]
        message_json = json.dumps(message) if isinstance(message, dict) else message
        
        for player_id, websocket in game.players.items():
            try:
                await websocket.send(message_json)
            except websockets.ConnectionClosed:
                logger.info(f"Player {player_id} in game {game_id} disconnected")
    
    async def cleanup_client(self, websocket):
        if websocket in self.connected_clients:
            player_info = self.connected_clients[websocket]
            game_id = player_info['game_id']
            
            # Remove from waiting players if still waiting
            self.waiting_players = [p for p in self.waiting_players if p['websocket'] != websocket]
            
            # Handle game cleanup
            if game_id in self.games:
                game = self.games[game_id]
                if len(game.players) == 1:
                    # Only one player left, end the game
                    remaining_player = None
                    for pid, ws in game.players.items():
                        if ws != websocket:
                            remaining_player = pid
                            break
                    
                    if remaining_player:
                        await self.broadcast_to_game(game_id, {
                            "tipo": "oponente_desconectou",
                            "vencedor": remaining_player,
                            "mensagem": "Oponente desconectou. Você venceu!"
                        })
                    
                    del self.games[game_id]
            
            del self.connected_clients[websocket]

async def main():
    server = GameServer()
    logger.info("Servidor WebSocket iniciando em ws://0.0.0.0:8765")
    
    async with websockets.serve(server.handle_client, "0.0.0.0", 8765):
        await asyncio.Future()  # mantém o servidor rodando para sempre

if __name__ == "__main__":
    asyncio.run(main())
