# 🎮 Jogos Interativos em Rede

# Descrição
Jogo pvp onde dois jogadores tem o objetivo de eliminar o oponete.
O jogo é no estilo AngryBirds onde a cada rodada ambos atacam em turnos e escolhendo a força e angulação do lançamento do projétil.
O dano recebido é proporcional ao local de impacto sendo:
 - 0 pts de dano: errou o alvo
 - 15 pts de dano: corpo
 - 40 pts de dano: cabeça

[Link do diagrama de estados do jogo](https://lucid.app/lucidchart/f5570b3b-39c5-4891-b228-780d3c2bc7c7/edit?viewport_loc=500%2C-222%2C3151%2C1310%2C0_0&invitationId=inv_f8d46880-384f-4065-b7c6-3845da9e27f0)

# Tecnologias Utilizadas
### Servidor
- Python: Linguagem principal para a lógica do servidor.
- Asyncio: Biblioteca padrão do Python para programação assíncrona e concorrente, permitindo gerenciar múltiplos clientes de forma eficiente.
- Websockets: Biblioteca para a criação de um servidor WebSocket, possibilitando a comunicação em tempo real e de baixa latência com os clientes.

### Cliente
- HTML: Estrutura da página do jogo.
- CSS: Estilização básica da interface.
- JavaScript: Lógica do cliente, renderização no Canvas e comunicação com o servidor via API WebSocket nativa do navegador.

### Ponte
- WebSocket Bridge: Um script Python que atua como uma ponte entre o servidor e o cliente, permitindo a comunicação em tempo real e a troca de mensagens entre eles.
- TCP/IP: Protocolo de comunicação utilizado para a troca de mensagens entre o servidor e o cliente, garantindo uma conexão confiável e ordenada.

### Formato de Dados
- JSON: Utilizado para a serialização de todos os dados trocados entre o servidor e os clientes, garantindo uma comunicação leve e padronizada

# Funcionalidades Implementadas
 - Gerenciar o estado do jogo e a lógica de regras.
 - Sincronização de ações entre jogadores.
 - Sistema de turnos, se aplicável.

# Instruções de Execução
### 1. Clone o Repositório
git clone http://github.com/jhvlima/jogoEmRede.git
cd jogoEmRede

### 2. Crie e Ative um Ambiente Virtual (Recomendado)
``` bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências do servidors
``` bash
pip install websockets
pip install --break-system-packages websockets
```

### 4. Inicie o servidor 
``` bash
python3 server/server.py
```
 Inicie o servidor WebSocket que gerencia a lógica do jogo e a comunicação entre os jogadores.
``` bash
python3 web_socket_bridge.py 
```

Inicie o servidor HTTP que serve os arquivos estáticos (HTML, CSS, JS) do jogo.
``` bash
python3 client.py
```

### 6. Conecte os Jogadores
O terminal mostrará uma mensagem como: Abrindo o jogo em seu navegador padrão: http://localhost:8000/index.html
Jogador 1: Em um navegador, acesse http://<IP_DO_SERVIDOR>:8000.
Jogador 2: Em outro navegador, acesse o mesmo endereço: http://<IP_DO_SERVIDOR>:8000.
O jogo começará automaticamente quando o segundo jogador se conectar.

# Como Testar
1. Siga as Instruções de Execução para iniciar o servidor.
2. Abra o primeiro cliente no navegador. A mensagem "Aguardando oponente..." deve ser exibida.
3. Abra o segundo cliente. A mensagem deve mudar para "Seu Turno" para o Jogador 1.
4. Jogue como Jogador 1: clique, arraste e solte para atirar. Observe a trajetória do projétil.
5. Após a jogada ser concluída, verifique se o turno passa corretamente para o Jogador 2.
6. Jogue como Jogador 2 e tente acertar o Jogador 1. Verifique se a barra de vida do Jogador 1 diminui.
7. Continue jogando até que a vida de um dos jogadores chegue a zero. Uma mensagem de vitória deve ser exibida.
8. Teste a desconexão: feche a aba de um dos jogadores. O jogo deve parar, e o jogador restante deve ser declarado vencedor.

# Possíveis Melhorias Futuras
- Chat no Jogo: Implementar um sistema de mensagens em tempo real para que os jogadores possam se comunicar durante a partida.
- Sistema de Salas: Criar um lobby onde os jogadores possam ver uma lista de partidas disponíveis ou criar suas próprias salas de jogo (públicas ou privadas com senha).
- Cenário Destrutível: Adicionar elementos ao cenário que possam ser destruídos pelos projéteis, alterando a dinâmica do campo de batalha.
- Variedade de Armas: Permitir que os jogadores escolham entre diferentes tipos de projéteis com características distintas (ex: maior dano, maior área de explosão).
- Efeitos do Ambiente: Adicionar um fator de vento aleatório a cada turno que afete a trajetória do projétil, aumentando o desafio.