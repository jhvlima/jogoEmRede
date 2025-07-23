import asyncio
import websockets
import json
import random
import time

# --- Configurações do Teste ---
NUMERO_DE_CLIENTES = 100  # O número de jogadores simultâneos que quer simular
URL_DA_PONTE = "ws://localhost:8766"
TEMPO_ENTRE_JOGADAS = 2 # Segundos que cada cliente espera antes de enviar uma nova jogada

async def jogador_virtual(numero_jogador):
    """
    Esta função simula o comportamento completo de um único jogador.
    """
    try:
        # Conecta-se à ponte, tal como o cliente web faria
        async with websockets.connect(URL_DA_PONTE) as websocket:
            print(f"[Jogador {numero_jogador}] Conectado ao servidor.")
            
            # 1. Espera pelo início do jogo
            game_started = False
            my_player_id = 0
            while not game_started:
                message_str = await websocket.recv()
                message = json.loads(message_str)
                if message.get("tipo") == "inicio":
                    my_player_id = message.get("jogador_id", 2) # Assume jogador 2 se não tiver ID
                    game_started = True
                    print(f"[Jogador {numero_jogador}] Jogo iniciado. Sou o jogador {my_player_id}.")
                elif message.get("tipo") == "espera":
                    my_player_id = message.get("jogador_id")

            # 2. Loop principal do jogo: envia jogadas periodicamente
            while True:
                # Cria uma jogada aleatória
                jogada = {
                    "tipo": "jogada",
                    "angulo": random.randint(30, 60),
                    "forca": random.randint(50, 90)
                }
                
                await websocket.send(json.dumps(jogada))
                print(f"[Jogador {numero_jogador}] Enviou uma jogada.")
                
                # Ouve a resposta (não precisa de a processar, apenas confirmar que chega)
                await websocket.recv()
                
                # Espera um pouco antes da próxima jogada
                await asyncio.sleep(TEMPO_ENTRE_JOGADAS)

    except websockets.exceptions.ConnectionClosed as e:
        print(f"[Jogador {numero_jogador}] Desconectado: {e.reason} (Código: {e.code})")
    except ConnectionRefusedError:
        print(f"[Jogador {numero_jogador}] ERRO: Não foi possível conectar. A ponte está a ser executada?")
    except Exception as e:
        print(f"[Jogador {numero_jogador}] Ocorreu um erro inesperado: {e}")


async def main():
    print("--- INICIANDO TESTE DE CAPACIDADE ---")
    print(f"A simular {NUMERO_DE_CLIENTES} clientes a conectarem-se a {URL_DA_PONTE}")
    print("Certifique-se de que o 'server.py' e o 'web_socket_bridge.py' estão a ser executados.")
    
    # Cria e inicia todas as tarefas dos jogadores virtuais
    tarefas = [jogador_virtual(i) for i in range(1, NUMERO_DE_CLIENTES + 1)]
    await asyncio.gather(*tarefas)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTeste de capacidade interrompido.")