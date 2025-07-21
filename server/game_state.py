import time

class EstadoDoJogo:
    def __init__(self, game_id):
        self.game_id = game_id
        self.vidas = {1: 100, 2: 100}
        self.turno = 1
        self.players = {}  # player_id -> websocket
        self.game_started = False
        self.game_over = False
        self.winner = None
        self.created_at = time.time()
        self.last_move_time = None
        self.move_history = []
    
    def add_player(self, player_id, websocket):
        """Add a player to the game"""
        self.players[player_id] = websocket
        if len(self.players) == 2:
            self.game_started = True
    
    def is_player_turn(self, player_id):
        """Check if it's the specified player's turn"""
        return self.turno == player_id and self.game_started and not self.game_over
    
    def apply_damage(self, target_player, damage):
        """Apply damage to a player and update game state"""
        if target_player in self.vidas:
            self.vidas[target_player] = max(0, self.vidas[target_player] - damage)
            
            # Check for game over
            if self.vidas[target_player] <= 0:
                self.game_over = True
                self.winner = 1 if target_player == 2 else 2
    
    def next_turn(self):
        """Switch to the next player's turn"""
        if not self.game_over:
            self.turno = 2 if self.turno == 1 else 1
            self.last_move_time = time.time()
    
    def is_game_over(self):
        """Check if the game is over"""
        return self.game_over or any(vida <= 0 for vida in self.vidas.values())
    
    def get_winner(self):
        """Get the winner of the game"""
        if self.winner:
            return self.winner
        
        # Determine winner based on remaining health
        if self.vidas[1] <= 0:
            return 2
        elif self.vidas[2] <= 0:
            return 1
        else:
            return None
    
    def add_move_to_history(self, player_id, move_data):
        """Add a move to the game history"""
        move_entry = {
            'player_id': player_id,
            'timestamp': time.time(),
            'move_data': move_data
        }
        self.move_history.append(move_entry)
    
    def get_game_state(self):
        """Get the current game state as a dictionary"""
        return {
            'game_id': self.game_id,
            'vidas': self.vidas,
            'turno': self.turno,
            'game_started': self.game_started,
            'game_over': self.game_over,
            'winner': self.winner,
            'players_connected': len(self.players)
        }
