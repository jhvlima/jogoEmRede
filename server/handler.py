from utils import calcular_impacto, calcular_dano
import json

def processar_jogada(jogada_json, jogador, state):
    jogada = json.loads(jogada_json)
    if jogada["tipo"] != "jogada":
        return json.dumps({"tipo": "erro", "mensagem": "Tipo de mensagem inválido"})

    impacto = calcular_impacto(jogada)
    dano = calcular_dano(impacto)

    adversario = 2 if jogador == 1 else 1
    state.vidas[adversario] -= dano
    state.turno = adversario

    return json.dumps({
        "tipo": "atualizacao",
        "jogadorAtual": state.turno,
        "vida": state.vidas,
        "mensagem": f"Jogador {jogador} causou {dano} de dano!"
    })
