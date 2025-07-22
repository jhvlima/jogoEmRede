# web_socket_bridge.py

import asyncio
import websockets
import socket
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GAME_SERVER_HOST = 'localhost'
GAME_SERVER_PORT = 8765
BRIDGE_WEBSOCKET_PORT = 8766

async def connect_to_game_server():
    """Tenta se conectar ao servidor de jogo TCP."""
    try:
        reader, writer = await asyncio.open_connection(GAME_SERVER_HOST, GAME_SERVER_PORT)
        logger.info(f"Ponte conectada ao servidor de jogo em {GAME_SERVER_HOST}:{GAME_SERVER_PORT}")
        return reader, writer
    except ConnectionRefusedError:
        logger.error("Falha ao conectar ao servidor de jogo. Ele está rodando?")
        return None, None

async def forward_to_game_server(tcp_writer, websocket):
    """Encaminha mensagens do cliente web (WebSocket) para o servidor de jogo (TCP)."""
    async for message in websocket:
        try:
            # Pega a mensagem do WebSocket e a envia para o servidor TCP com o prefixo de tamanho
            logger.info(f"[Web -> Jogo] Encaminhando: {message}")
            data = message.encode('utf-8')
            tcp_writer.write(len(data).to_bytes(4, 'big') + data)
            await tcp_writer.drain()
        except websockets.exceptions.ConnectionClosed:
            logger.info("Cliente web desconectado.")
            break
        except Exception as e:
            logger.error(f"Erro ao encaminhar para o servidor de jogo: {e}")
            break

async def forward_to_web_client(tcp_reader, websocket):
    """Encaminha mensagens do servidor de jogo (TCP) para o cliente web (WebSocket)."""
    while True:
        try:
            # Lê o prefixo de tamanho da mensagem TCP
            header = await tcp_reader.readexactly(4)
            if not header:
                break
            
            message_length = int.from_bytes(header, 'big')
            # Lê o corpo da mensagem
            data = await tcp_reader.readexactly(message_length)
            message = data.decode('utf-8')
            
            # Envia a mensagem para o cliente web via WebSocket
            logger.info(f"[Jogo -> Web] Encaminhando: {message}")
            await websocket.send(message)
        except (asyncio.IncompleteReadError, websockets.exceptions.ConnectionClosed):
            logger.info("Conexão encerrada (servidor de jogo ou cliente web).")
            break
        except Exception as e:
            logger.error(f"Erro ao encaminhar para o cliente web: {e}")
            break

async def handle_client(websocket):
    """Gerencia a conexão completa: web <-> ponte <-> jogo."""
    logger.info(f"Cliente web conectado de {websocket.remote_address}")
    
    tcp_reader, tcp_writer = await connect_to_game_server()
    if not tcp_writer:
        await websocket.close(1011, "Servidor de jogo indisponível.")
        return

    # Executa as duas tarefas de encaminhamento concorrentemente
    task_web_to_game = asyncio.create_task(forward_to_game_server(tcp_writer, websocket))
    task_game_to_web = asyncio.create_task(forward_to_web_client(tcp_reader, websocket))

    # Aguarda a primeira tarefa a ser concluída (o que indica uma desconexão)
    done, pending = await asyncio.wait(
        [task_web_to_game, task_game_to_web],
        return_when=asyncio.FIRST_COMPLETED
    )

    # Cancela as tarefas pendentes e fecha as conexões
    for task in pending:
        task.cancel()
    
    tcp_writer.close()
    await tcp_writer.wait_closed()
    
    if websocket.state.name != 'CLOSED':
        await websocket.close()
        
    logger.info("Sessão da ponte encerrada.")

async def main():
    logger.info(f"Servidor da ponte WebSocket escutando em ws://localhost:{BRIDGE_WEBSOCKET_PORT}")
    server = await websockets.serve(handle_client, "localhost", BRIDGE_WEBSOCKET_PORT)
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Ponte encerrada pelo usuário.")