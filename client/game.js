const ws = new WebSocket("ws://localhost:8765");

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.tipo === "inicio") {
        // mostra HUD
    } else if (data.tipo === "atualizacao") {
        // atualiza vida, mostra animação, etc.
    } else if (data.tipo === "fim") {
        alert(`Fim de jogo! Vencedor: ${data.vencedor}`);
    }
};

function enviarJogada(angulo, forca) {
    ws.send(JSON.stringify({
        tipo: "jogada",
        angulo: angulo,
        forca: forca
    }));
}
