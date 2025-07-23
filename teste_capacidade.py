import time
import json
from locust import User, task, between
from websocket import create_connection, WebSocketException

# --- Configurações ---
BRIDGE_HOST = "ws://localhost:8766"

class GameClient:
    """
    Um wrapper para o cliente WebSocket que se conecta à ponte.
    """
    def __init__(self, host):
        try:
            self.ws = create_connection(host)
        except WebSocketException as e:
            raise ConnectionRefusedError(f"Não foi possível conectar a {host}: {e}")

    def receive(self):
        try:
            return self.ws.recv()
        except WebSocketException:
            return None

    def send(self, data):
        try:
            self.ws.send(json.dumps(data))
        except WebSocketException:
            pass
            
    def close(self):
        self.ws.close()

class GameUser(User):
    """
    Representa um jogador virtual (um utilizador do Locust).
    """
    wait_time = between(2, 5)  # Cada jogador espera entre 2 e 5 segundos entre as jogadas

    def on_start(self):
        """
        Chamado quando um jogador virtual é iniciado.
        Conecta-se à ponte e espera o jogo começar.
        """
        try:
            self.client = GameClient(BRIDGE_HOST)
            self.player_id = None
            
            # Espera a mensagem de 'espera' ou 'inicio'
            while True:
                msg_str = self.client.receive()
                if not msg_str: break
                
                msg = json.loads(msg_str)
                if msg.get("tipo") == "espera":
                    self.player_id = msg.get("jogador_id")
                elif msg.get("tipo") == "inicio":
                    if not self.player_id: # Se era o jogador 2
                        self.player_id = 2 
                    break # O jogo começou, pode ir para as tarefas
        except Exception:
            self.environment.runner.quit() # Aborta o teste se a conexão inicial falhar

    @task
    def fazer_jogada(self):
        """
        A tarefa principal: simula um jogador fazendo uma jogada.
        """
        if not self.client:
            return
        
        # Simula uma jogada com ângulo e força aleatórios
        jogada = {
            "tipo": "jogada",
            "angulo": 45,
            "forca": 75
        }
        self.client.send(jogada)
        
        # Ouve a resposta para garantir que o ciclo se completa
        self.client.receive()

    def on_stop(self):
        """
        Chamado quando um jogador virtual é parado.
        """
        if self.client:
            self.client.close()