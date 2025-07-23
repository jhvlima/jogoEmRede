import json
import logging
from utils import calcular_impacto, calcular_dano

logger = logging.getLogger(__name__)

def processar_jogada(jogada_json, jogador_id, game_state):
    """
    Process a player's move and return the game state update
    """
    try:
        jogada = json.loads(jogada_json)
        
        # Validate message type
        if jogada.get("tipo") != "jogada":
            return {
                "tipo": "erro", 
                "mensagem": "Tipo de mensagem inválido. Use 'jogada'."
            }
        
        # Check if it's the player's turn
        if not game_state.is_player_turn(jogador_id):
            return {
                "tipo": "erro",
                "mensagem": f"Não é o seu turno! É o turno do jogador {game_state.turno}."
            }
        
        # Validate required move data
        required_fields = ['angulo', 'forca']
        missing_fields = [field for field in required_fields if field not in jogada]
        if missing_fields:
            return {
                "tipo": "erro",
                "mensagem": f"Dados da jogada incompletos. Campos obrigatórios: {missing_fields}"
            }
        
        # Process the move
        angulo = jogada['angulo']
        forca = jogada['forca']
    
        
        if not (0 <= forca <= 100):
            return {
                "tipo": "erro",
                "mensagem": "Força deve estar entre 0 e 100."
            }
        
        # Calculate impact and damage
        impacto_info = calcular_impacto(jogada)
        dano = calcular_dano(impacto_info)
        
        # Determine target player
        adversario = 2 if jogador_id == 1 else 1
        
        # Apply damage
        game_state.apply_damage(adversario, dano)
        
        # Add move to history
        game_state.add_move_to_history(jogador_id, jogada)
        
        # Switch turns first (before preparing response)
        if not game_state.is_game_over():
            game_state.next_turn()
        
        # Prepare response
        response = {
            "tipo": "atualizacao",
            "jogador_atual": jogador_id,
            "proximo_turno": adversario,
            "vidas": game_state.vidas,
            "dano_causado": dano,
            "impacto": impacto_info,
            "jogada": {
                "jogador": jogador_id,
                "angulo": angulo,
                "forca": forca
            },
            "mensagem": f"Jogador {jogador_id} causou {dano} de dano! ({impacto_info['tipo']})",
            "turno_atual": game_state.turno
        }
        
        # Check if game is over
        if game_state.is_game_over():
            winner = game_state.get_winner()
            response.update({
                "game_over": True,
                "vencedor": winner,
                "mensagem": f"Jogador {winner} venceu! Jogador {adversario} foi eliminado."
            })
        
        logger.info(f"Move processed: Player {jogador_id}, Damage: {dano}, Game Over: {game_state.is_game_over()}")
        
        return response
        
    except json.JSONDecodeError:
        return {
            "tipo": "erro",
            "mensagem": "JSON inválido recebido."
        }
    except Exception as e:
        logger.error(f"Error processing move: {e}")
        return {
            "tipo": "erro",
            "mensagem": "Erro interno ao processar jogada."
        }
