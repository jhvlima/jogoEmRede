import math
import random

def simular_trajetoria(angulo, forca):
    """
    Simula a trajetória passo a passo de um projétil.
    Retorna uma lista de coordenadas relativas (x, y).
    """
    angulo_rad = math.radians(angulo)
    # Ajustar estes valores até a física parecer boa
    velocidade_inicial = forca * 0.4
    gravidade = 0.2

    vx = velocidade_inicial * math.cos(angulo_rad)
    vy = velocidade_inicial * math.sin(angulo_rad)

    trajetoria = []
    x, y = 0, 0 # Posição inicial relativa

    for _ in range(300): # Simular por um número máximo de frames
        vy += gravidade
        x += vx
        y += vy
        
        trajetoria.append({'x': round(x, 2), 'y': round(y, 2)})
        
        # Parar se o projétil atingir o chão (coordenada y relativa volta a ser positiva)
        if y > 0:
            break
            
    return trajetoria

def calcular_impacto(jogada):
    """
    Calcula o impacto com base na simulação de trajetória.
    """
    angulo = jogada.get('angulo', 1)
    forca = jogada.get('forca', 1)
    
    trajetoria = simular_trajetoria(angulo, forca)
    
    alcance = trajetoria[-1]['x'] if trajetoria else 0

    # Distância entre os jogadores no canvas (100 vs 800 num canvas de 900)
    distancia_alvo = 700 
    
    erro_distancia = abs(alcance - distancia_alvo)
    
    # A precisão é maior quanto menor for o erro.
    # Um erro de 0 é 100% de precisão.
    precisao = max(0, 1 - (erro_distancia / 350)) # 350 é uma margem de erro aceitável
    precisao *= random.uniform(0.9, 1.1) # Adiciona um pouco de aleatoriedade

    if precisao < 0.7:
        tipo_acerto = 'erro'
        dano_base = 0
    elif precisao < 0.95:
        tipo_acerto = 'corpo'
        dano_base = 15
    else:
        tipo_acerto = 'cabeca'
        dano_base = 40
        
    return {
        'tipo': tipo_acerto,
        'precisao': precisao,
        'alcance': alcance,
        'distancia_alvo': distancia_alvo,
        'dano_base': dano_base,
        'trajetoria': trajetoria
    }

def calcular_dano(impacto_info):
    if impacto_info['tipo'] == 'erro':
        return 0
    
    base_damage = impacto_info.get('dano_base', 0)
    
    # Aplicar um modificador com base na precisão
    precision_modifier = 0.8 + (impacto_info.get('precisao', 0) * 0.4)
    final_damage = int(base_damage * precision_modifier)
    
    return max(0, final_damage)