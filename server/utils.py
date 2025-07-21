import math
import random

def calcular_impacto(jogada):
    """
    Calculate impact based on angle, force, and hit detection
    Returns impact information including damage type
    """
    angulo = jogada.get('angulo', 45)  # degrees
    forca = jogada.get('forca', 50)    # percentage (0-100)
    
    # Convert angle to radians
    angulo_rad = math.radians(angulo)
    
    # Basic physics calculation for projectile trajectory
    # Assuming target is at a fixed distance and we calculate if we hit
    gravidade = 9.8
    velocidade_inicial = forca * 2  # Scale force to velocity
    
    # Calculate range (simplified physics)
    alcance = (velocidade_inicial ** 2 * math.sin(2 * angulo_rad)) / gravidade
    
    # Target distance (fixed for simplicity)
    distancia_alvo = 80  # meters
    
    # Calculate accuracy based on how close we are to optimal angle/force
    optimal_angle = math.degrees(math.asin(gravidade * distancia_alvo / (velocidade_inicial ** 2)) / 2)
    angle_error = abs(angulo - optimal_angle)
    
    # Add some randomness for realism
    random_factor = random.uniform(0.8, 1.2)
    accuracy = max(0, (90 - angle_error) / 90) * random_factor
    
    # Determine hit type based on accuracy
    if accuracy < 0.3:
        # Miss
        return {
            'tipo': 'erro',
            'precisao': accuracy,
            'alcance': alcance,
            'distancia_alvo': distancia_alvo,
            'dano_base': 0
        }
    elif accuracy < 0.7:
        # Body hit
        return {
            'tipo': 'corpo',
            'precisao': accuracy,
            'alcance': alcance,
            'distancia_alvo': distancia_alvo,
            'dano_base': 15
        }
    else:
        # Head hit (critical)
        return {
            'tipo': 'cabeca',
            'precisao': accuracy,
            'alcance': alcance,
            'distancia_alvo': distancia_alvo,
            'dano_base': 40
        }

def calcular_dano(impacto_info):
    """
    Calculate final damage based on impact information
    """
    if impacto_info['tipo'] == 'erro':
        return 0
    elif impacto_info['tipo'] == 'corpo':
        # Body hit: 15 pts base damage
        base_damage = 15
    elif impacto_info['tipo'] == 'cabeca':
        # Head hit: 40 pts base damage  
        base_damage = 40
    else:
        base_damage = 0
    
    # Apply precision modifier (±20% based on accuracy)
    precision_modifier = 0.8 + (impacto_info['precisao'] * 0.4)
    final_damage = int(base_damage * precision_modifier)
    
    return max(0, final_damage)

def validar_jogada(jogada):
    """
    Validate move data
    """
    required_fields = ['tipo', 'angulo', 'forca']
    
    for field in required_fields:
        if field not in jogada:
            return False, f"Campo obrigatório ausente: {field}"
    
    if jogada['tipo'] != 'jogada':
        return False, "Tipo deve ser 'jogada'"
    
    try:
        angulo = float(jogada['angulo'])
        forca = float(jogada['forca'])
        
        if not (0 <= angulo <= 90):
            return False, "Ângulo deve estar entre 0 e 90 graus"
        
        if not (0 <= forca <= 100):
            return False, "Força deve estar entre 0 e 100"
            
    except (ValueError, TypeError):
        return False, "Ângulo e força devem ser números válidos"
    
    return True, "Jogada válida"

def simular_trajetoria(angulo, forca, steps=50):
    """
    Simulate projectile trajectory for client visualization
    Returns list of (x, y) coordinates
    """
    angulo_rad = math.radians(angulo)
    velocidade_inicial = forca * 2
    gravidade = 9.8
    
    vx = velocidade_inicial * math.cos(angulo_rad)
    vy = velocidade_inicial * math.sin(angulo_rad)
    
    trajetoria = []
    dt = 0.1  # time step
    
    for i in range(steps):
        t = i * dt
        x = vx * t
        y = vy * t - 0.5 * gravidade * t * t
        
        if y < 0:  # Hit ground
            break
            
        trajetoria.append({'x': round(x, 2), 'y': round(y, 2)})
    
    return trajetoria
