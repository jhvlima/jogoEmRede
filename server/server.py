import socket
import threading
import json
import logging
from handler import processar_jogada
from game_state import EstadoDoJogo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameServer:
    def __init__(self, host='0.0.0.0', port=8765):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.games = {}
        self.waiting_players = []
        self.connected_clients = {}  # socket -> player_info
        self.lock = threading.Lock()

    def send_message(self, client_socket, data):
        """Encodes and sends a JSON message with a length prefix."""
        try:
            message = json.dumps(data).encode('utf-8')
            message_length = len(message).to_bytes(4, 'big')
            client_socket.sendall(message_length + message)
        except OSError as e:
            logger.error(f"Error sending message: {e}")
            self.cleanup_client(client_socket)
        except Exception as e:
            logger.error(f"An unexpected error occurred during send: {e}")


    def receive_message(self, client_socket):
        """Decodes a message with a length prefix."""
        try:
            message_length_bytes = client_socket.recv(4)
            if not message_length_bytes:
                return None
            
            message_length = int.from_bytes(message_length_bytes, 'big')
            message = client_socket.recv(message_length)
            return json.loads(message.decode('utf-8'))
        except (ConnectionResetError, BrokenPipeError):
             logger.warning("Client disconnected abruptly.")
             return None
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None


    def broadcast_to_game(self, game_id, message):
        """Broadcasts a message to all players in a game."""
        if game_id not in self.games:
            return
            
        game = self.games[game_id]
        
        # Make a copy of player sockets to avoid issues if a player disconnects
        sockets_to_broadcast = list(game.players.values())
        
        for client_socket in sockets_to_broadcast:
            self.send_message(client_socket, message)


    def handle_client(self, client_socket, addr):
        logger.info(f"New connection from {addr}")
        
        player_info = None
        
        with self.lock:
            if not self.waiting_players:
                # First player starts a new game
                game_id = len(self.games) + 1
                game = EstadoDoJogo(game_id)
                self.games[game_id] = game
                
                player_info = {'game_id': game_id, 'player_id': 1, 'socket': client_socket}
                game.add_player(1, client_socket)
                self.connected_clients[client_socket] = player_info
                self.waiting_players.append(player_info)
                
                self.send_message(client_socket, {
                    "tipo": "espera", "mensagem": "Aguardando oponente...",
                    "jogador_id": 1, "game_id": game_id
                })
            else:
                # Second player joins the waiting game
                waiting_player_info = self.waiting_players.pop(0)
                game_id = waiting_player_info['game_id']
                game = self.games[game_id]
                
                player_info = {'game_id': game_id, 'player_id': 2, 'socket': client_socket}
                game.add_player(2, client_socket)
                self.connected_clients[client_socket] = player_info
                
                # Notify both players that the game has started
                start_message = {
                    "tipo": "inicio",
                    "mensagem": "Jogo iniciado! Jogador 1 começa.",
                    "turno_atual": game.turno, "vidas": game.vidas
                }
                
                # Send personalized message to each player
                p1_socket = self.games[game_id].players[1]
                p2_socket = self.games[game_id].players[2]

                p1_start_message = start_message.copy()
                p1_start_message['jogador_id'] = 1
                self.send_message(p1_socket, p1_start_message)

                p2_start_message = start_message.copy()
                p2_start_message['jogador_id'] = 2
                self.send_message(p2_socket, p2_start_message)

        try:
            while True:
                jogada_json = self.receive_message(client_socket)
                if jogada_json is None:
                    break # Client disconnected
                
                current_player_info = self.connected_clients.get(client_socket)
                if not current_player_info:
                    break

                game = self.games.get(current_player_info['game_id'])
                if not game:
                    break
                
                # The handler expects a string, so we re-encode it
                resposta = processar_jogada(json.dumps(jogada_json), current_player_info['player_id'], game)
                
                self.broadcast_to_game(current_player_info['game_id'], resposta)
                
                if game.is_game_over():
                    winner = game.get_winner()
                    self.broadcast_to_game(current_player_info['game_id'], {
                        "tipo": "fim_jogo", "vencedor": winner, "mensagem": f"Jogador {winner} venceu!"
                    })
                    # Game cleanup is handled in the cleanup_client method
                    break

        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
        finally:
            self.cleanup_client(client_socket)


    def cleanup_client(self, client_socket):
        with self.lock:
            if client_socket in self.connected_clients:
                player_info = self.connected_clients.pop(client_socket)
                game_id = player_info.get('game_id')
                player_id = player_info.get('player_id')
                
                logger.info(f"Cleaning up player {player_id} from game {game_id}")
                
                # Remove from waiting list if they were there
                self.waiting_players = [p for p in self.waiting_players if p['socket'] != client_socket]
                
                if game_id and game_id in self.games:
                    game = self.games[game_id]
                    if player_id in game.players:
                        del game.players[player_id]

                    # If a player disconnects, the other one wins
                    if len(game.players) == 1 and game.game_started:
                        remaining_player_id = list(game.players.keys())[0]
                        self.broadcast_to_game(game_id, {
                            "tipo": "oponente_desconectou",
                            "vencedor": remaining_player_id,
                            "mensagem": "Oponente desconectou. Você venceu!"
                        })
                        # Clean up the game
                        if game_id in self.games:
                             del self.games[game_id]
                    elif len(game.players) == 0:
                        # Clean up game if both players left
                        if game_id in self.games:
                            del self.games[game_id]

            client_socket.close()
            logger.info("Client socket closed.")

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        logger.info(f"Server started on {self.host}:{self.port}")
        
        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                thread.daemon = True
                thread.start()
            except KeyboardInterrupt:
                logger.info("Server is shutting down.")
                break
            except Exception as e:
                logger.error(f"Error accepting connections: {e}")
                break
        
        self.server_socket.close()

if __name__ == "__main__":
    server = GameServer()
    server.start()