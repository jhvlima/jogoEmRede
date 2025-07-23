// --- Elementos da UI ---
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const turnMessageEl = document.getElementById('turnMessage');
const p1HpBar = document.getElementById('player1-hp-bar');
const p2HpBar = document.getElementById('player2-hp-bar');

// --- Estado do Jogo ---
let socket;
let playerId = null;
let currentTurn = null;
let gameStarted = false;

// --- Estado do Cliente ---
let isDragging = false;
let dragStart = null;
let dragEnd = null;
let projectileAnimation = null; // { path: [], step: 0 }

const players = {
    1: { x: 100, y: canvas.height - 50, width: 50, height: 30, color: '#007bff' },
    2: { x: canvas.width - 100, y: canvas.height - 50, width: 50, height: 30, color: '#dc3545' }
};

// --- Comunicação com o Servidor ---
function connectToServer() {
    socket = new WebSocket(`ws://${window.location.hostname}:8766`);
    socket.onopen = () => console.log("Conectado ao servidor.");
    socket.onmessage = handleServerMessage;
    socket.onclose = () => updateTurnMessage("Desconectado.", "red");
    socket.onerror = (err) => console.error("WebSocket Error:", err);
}

function handleServerMessage(event) {
    const data = JSON.parse(event.data);
    switch (data.tipo) {
        case 'espera':
            playerId = data.jogador_id;
            updateTurnMessage(`Aguardando oponente... (Você é o Jogador ${playerId})`, "#555");
            break;
        case 'inicio':
            gameStarted = true;
            playerId = data.jogador_id;
            currentTurn = data.turno_atual;
            updateUI(data);
            break;
        case 'atualizacao':
            currentTurn = data.turno_atual;
            updateUI(data);
            if (data.impacto && data.impacto.trajetoria) {
                const shooterId = data.jogada.jogador;
                const startPos = players[shooterId];
                // Inicia a animação com o caminho exato calculado pelo servidor
                animateProjectileFromServer(data.impacto.trajetoria, startPos);
            }
            break;
        case 'fim_jogo':
            gameStarted = false;
            updateTurnMessage(`Fim de Jogo! Jogador ${data.vencedor} venceu!`, "gold");
            wait(5000)
            break;
        case 'oponente_desconectou':
            gameStarted = false;
            updateTurnMessage(`Oponente desconectou. Você venceu!`, "green");
            break;
    }
}

function sendMove(angle, force) {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({
        tipo: "jogada",
        angulo: angle,
        forca: force
    }));
}

// --- Lógica de Input do Jogador (Arrastar o mouse) ---
canvas.addEventListener('mousedown', (e) => {
    if (currentTurn !== playerId || !gameStarted) return;
    const rect = canvas.getBoundingClientRect();
    isDragging = true;
    dragStart = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    dragEnd = dragStart;
});

canvas.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const rect = canvas.getBoundingClientRect();
    dragEnd = { x: e.clientX - rect.left, y: e.clientY - rect.top };
});

canvas.addEventListener('mouseup', (e) => {
    if (!isDragging) return;
    isDragging = false;
    
    const dx = dragStart.x - dragEnd.x;
    const dy = dragStart.y - dragEnd.y;
    
    let angle = Math.atan2(dy, dx) * (180 / Math.PI);
    angle = (playerId === 2) ? 180 - angle : angle;

    const distance = Math.sqrt(dx * dx + dy * dy);
    const force = Math.min(100, distance / 2.5); 
    sendMove(angle, force);
    dragEnd = null;
});

// --- Lógica de Renderização e Animação ---
function drawGame() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    drawGround();
    drawPlayers();
    drawAimLine();

    if (projectileAnimation) {
        drawProjectileFrame();
    }
    
    requestAnimationFrame(drawGame);
}

function updateUI(state) {
    p1HpBar.style.width = `${state.vidas[1]}%`;
    p2HpBar.style.width = `${state.vidas[2]}%`;
    
    if (currentTurn === playerId) {
        updateTurnMessage("Seu turno! Mire e atire.", "#16a34a");
    } else {
        updateTurnMessage(`Aguardando Jogador ${currentTurn}...`, "#555");
    }
}

function updateTurnMessage(message, color) {
    turnMessageEl.textContent = message;
    turnMessageEl.style.color = color;
}

function drawGround() {
    ctx.fillStyle = '#654321';
    ctx.fillRect(0, canvas.height - 50, canvas.width, 50);
    ctx.fillStyle = '#228b22';
    ctx.fillRect(0, canvas.height - 50, canvas.width, 10);
}

function drawPlayers() {
    for (const id in players) {
        const p = players[id];
        ctx.fillStyle = p.color;
        ctx.fillRect(p.x - p.width / 2, p.y - p.height, p.width, p.height);
    }
}

function drawAimLine() {
    if (isDragging && dragEnd) {
        const player = players[playerId];
        ctx.beginPath();
        ctx.moveTo(player.x, player.y - player.height / 2);
        ctx.lineTo(dragEnd.x, dragEnd.y);
        ctx.strokeStyle = "rgba(255, 255, 255, 0.7)";
        ctx.setLineDash([5, 10]);
        ctx.stroke();
        ctx.setLineDash([]);
    }
}

function drawProjectileFrame() {
    const pos = projectileAnimation.path[projectileAnimation.step];
    if (pos) {
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 5, 0, Math.PI * 2);
        ctx.fillStyle = 'black';
        ctx.fill();
        projectileAnimation.step++;
    } else {
        projectileAnimation = null; // Fim da animação
    }
}

function animateProjectileFromServer(trajectoryPath, startPosition) {
    const absolutePath = trajectoryPath.map(pos => {
        const direction = (startPosition === players[1]) ? 1 : -1;
        return {
            x: startPosition.x + (pos.x * direction),
            y: startPosition.y - startPosition.height / 2 + pos.y
        };
    });

    projectileAnimation = { path: absolutePath, step: 0 };
}

// --- Inicialização ---
connectToServer();
drawGame();