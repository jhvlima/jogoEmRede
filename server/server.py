import asyncio
import websockets
import json
from handler import processar_jogada
from game_state import EstadoDoJogo

estado = EstadoDoJogo()
clientes = []

async def handler(websocket):
    clientes.append(websocket)
    jogador_id = len(clientes)

    if jogador_id < 2:
        await websocket.send(json.dumps({"tipo": "espera"}))
        return

    await websocket.send(json.dumps({
        "tipo": "inicio",
        "jogador": jogador_id
    }))

    try:
        async for message in websocket:
            resposta = processar_jogada(message, jogador_id, estado)
            for c in clientes:
                await c.send(resposta)
    except websockets.ConnectionClosed:
        print(f"Jogador {jogador_id} desconectado.")
    finally:
        clientes.remove(websocket)

async def main():
    print("Servidor WebSocket iniciando em ws://0.0.0.0:8765")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # mantém o servidor rodando para sempre

if __name__ == "__main__":
    asyncio.run(main())
