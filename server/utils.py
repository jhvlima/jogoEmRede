import math
import random

# Mantemos a simulação de trajetória como a principal forma de cálculo
def simular_trajetoria(angulo, forca):
    """
    Simula a trajetória passo a passo de um projétil.
    Retorna uma lista de coordenadas (x, y).
    """
    angulo_rad = math.radians(angulo)
    # Aumentar a escala da velocidade inicial para tornar a trajetória mais pronunciada
    velocidade_inicial = forca * 1.8 
    gravidade = 0.2  # Usar um valor de gravidade que "pareça bom" visualmente

    vx = velocidade_inicial * math.cos(angulo_rad)
    vy = -velocidade_inicial * math.sin(angulo_rad) # Y é negativo para subir no ecrã

    trajetoria = []
    x, y = 0, 0 # Posição inicial relativa

    # Simular até 300 passos ou até sair do ecrã
    for _ in range(300):
        vy += gravidade
        x += vx
        y += vy
        
        trajetoria.append({'x': round(x, 2), 'y': round(y, 2)})
        
        # Parar se o projétil atingir o chão (y > 0, pois começamos em 0)
        if y > 0:
            break
            
    return trajetoria

def calcular_impacto(jogada):
    """
    Calcula o impacto com base na nova simulação de trajetória.
    """
    angulo = jogada.get('angulo', 45)
    forca = jogada.get('forca', 50)
    
    trajetoria = simular_trajetoria(angulo, forca)
    
    # O alcance agora é a posição x final da trajetória
    alcance = trajetoria[-1]['x'] if trajetoria else 0

    # Distância do alvo (vamos torná-la mais precisa)
    # Supondo que o Jogador 1 está em x=100 e o Jogador 2 em x=800 no canvas de 900px
    distancia_alvo = 700 
    
    # A precisão agora é baseada na proximidade do alcance ao alvo
    erro_distancia = abs(alcance - distancia_alvo)
    
    # A precisão é maior quanto menor for o erro. 
    # Um erro de 0 é 100% de precisão. Um erro de 100 pixels é baixa.
    precisao = max(0, 1 - (erro_distancia / (distancia_alvo * 0.5))) # Meia distância do alvo como margem de erro
    
    # Adicionar um pouco de aleatoriedade
    precisao *= random.uniform(0.9, 1.1)

    # Determinar o tipo de acerto com base na nova precisão
    if precisao < 0.6: # Aumentar o limiar para erro
        tipo_acerto = 'erro'
        dano_base = 0
    elif precisao < 0.9: # Acerto no corpo
        tipo_acerto = 'corpo'
        dano_base = 15
    else: # Acerto na cabeça (requer alta precisão)
        tipo_acerto = 'cabeca'
        dano_base = 40
        
    return {
        'tipo': tipo_acerto,
        'precisao': precisao,
        'alcance': alcance,
        'distancia_alvo': distancia_alvo,
        'dano_base': dano_base,
        # Enviar a trajetória completa para o cliente!
        'trajetoria': trajetoria 
    }

# A função calcular_dano permanece a mesma
def calcular_dano(impacto_info):
    # ... (sem alterações aqui) ...
    if impacto_info['tipo'] == 'erro':
        return 0
    elif impacto_info['tipo'] == 'corpo':
        base_damage = 15
    elif impacto_info['tipo'] == 'cabeca': 
        base_damage = 40
    else:
        base_damage = 0
    
    precision_modifier = 0.8 + (impacto_info.get('precisao', 0) * 0.4)
    final_damage = int(base_damage * precision_modifier)
    
    return max(0, final_damage)