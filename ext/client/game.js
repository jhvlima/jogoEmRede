let websocket = null;
let connected = false;
let playerId = null;
let currentTurn = null;
let gameStarted = false;

function addMessage(text, type = 'info') {
    const messages = document.getElementById('messages');
    const message = document.createElement('div');
    message.className = `message ${type}`;
    message.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
}

function updateStatus(text, className = 'waiting') {
    const status = document.getElementById('status');
    status.textContent = text;
    status.className = `status ${className}`;
}

function updateHealth(player1Health, player2Health) {
    document.getElementById('health1').textContent = player1Health;
    document.getElementById('health2').textContent = player2Health;
    document.getElementById('healthBar1').style.width = `${player1Health}%`;
    document.getElementById('healthBar2').style.width = `${player2Health}%`;
}

function updateMoveButton() {
    const moveBtn = document.getElementById('moveBtn');
    const canMove = connected && gameStarted && currentTurn === playerId;
    moveBtn.disabled = !canMove;
    
    if (canMove) {
        moveBtn.textContent = 'Fazer Jogada - SUA VEZ!';
        moveBtn.style.backgroundColor = '#28a745';
    } else if (gameStarted && currentTurn !== playerId) {
        moveBtn.textContent = 'Aguardando turno do oponente...';
        moveBtn.style.backgroundColor = '#6c757d';
    } else {
        moveBtn.textContent = 'Aguardando jogo iniciar...';
        moveBtn.style.backgroundColor = '#6c757d';
    }
}

async function connect() {
    const serverUrl = document.getElementById('serverUrl').value;
    
    try {
        websocket = new WebSocket(serverUrl);
        
        websocket.onopen = function() {
            connected = true;
            document.getElementById('connectBtn').disabled = true;
            document.getElementById('disconnectBtn').disabled = false;
            updateStatus('Conectado - Aguardando oponente...', 'waiting');
            addMessage('Conectado ao servidor!', 'info');
        };
        
        websocket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleMessage(data);
        };
        
        websocket.onclose = function() {
            connected = false;
            gameStarted = false;
            document.getElementById('connectBtn').disabled = false;
            document.getElementById('disconnectBtn').disabled = true;
            document.getElementById('gameControls').classList.remove('active');
            updateStatus('Desconectado', 'waiting');
            updateMoveButton();
            addMessage('Desconectado do servidor', 'error');
        };
        
        websocket.onerror = function(error) {
            addMessage(`Erro de conexão: ${error}`, 'error');
            updateStatus('Erro de conexão', 'error');
        };
        
    } catch (error) {
        addMessage(`Erro ao conectar: ${error}`, 'error');
        updateStatus('Erro de conexão', 'error');
    }
}

function disconnect() {
    if (websocket) {
        websocket.close();
    }
}

function handleMessage(data) {
    addMessage(`Recebido: ${JSON.stringify(data)}`, 'info');
    
    switch (data.tipo) {
        case 'espera':
            playerId = data.jogador_id;
            updateStatus(`Você é o Jogador ${playerId} - Aguardando oponente...`, 'waiting');
            break;
            
        case 'inicio':
            gameStarted = true;
            currentTurn = data.turno_atual;
            document.getElementById('gameControls').classList.add('active');
            updateStatus('Jogo iniciado!', 'playing');
            updateHealth(data.vidas[1], data.vidas[2]);
            updateMoveButton();
            addMessage('Jogo iniciado! Boa sorte!', 'game');
            break;
            
        case 'atualizacao':
            updateHealth(data.vidas[1], data.vidas[2]);
            currentTurn = data.turno_atual;
            updateMoveButton();
            addMessage(data.mensagem, 'game');
            
            if (data.dano_causado !== undefined) {
                addMessage(`Dano causado: ${data.dano_causado} (${data.impacto.tipo})`, 'game');
            }
            break;
            
        case 'fim_jogo':
            gameStarted = false;
            updateMoveButton();
            updateStatus(`Fim de jogo! Vencedor: Jogador ${data.vencedor}`, 'playing');
            addMessage(`🎉 ${data.mensagem}`, 'game');
            break;
            
        case 'oponente_desconectou':
            gameStarted = false;
            updateMoveButton();
            updateStatus(`Você venceu! Oponente desconectou.`, 'playing');
            addMessage(data.mensagem, 'game');
            break;
            
        case 'erro':
            addMessage(`❌ Erro: ${data.mensagem}`, 'error');
            break;
            
        default:
            addMessage(`Tipo de mensagem desconhecido: ${data.tipo}`, 'error');
    }
}

function sendMove() {
    if (!connected || !gameStarted || currentTurn !== playerId) {
        addMessage('Não é possível fazer jogada agora', 'error');
        return;
    }
    
    const angle = parseInt(document.getElementById('angle').value);
    const force = parseInt(document.getElementById('force').value);
    
    if (angle < 0 || angle > 90) {
        addMessage('Ângulo deve estar entre 0 e 90 graus', 'error');
        return;
    }
    
    if (force < 0 || force > 100) {
        addMessage('Força deve estar entre 0 e 100', 'error');
        return;
    }
    
    const move = {
        tipo: 'jogada',
        angulo: angle,
        forca: force
    };
    
    websocket.send(JSON.stringify(move));
    addMessage(`Jogada enviada: Ângulo=${angle}°, Força=${force}`, 'info');
}

// Initialize
updateMoveButton();