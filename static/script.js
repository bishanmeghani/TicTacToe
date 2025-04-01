document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const cells = document.querySelectorAll('.cell');
    const resetButton = document.getElementById('resetButton');
    const continueButton = document.getElementById('continueButton');
    const playerIdElement = document.getElementById('playerId');
    const askToContinueButton = document.getElementById('askToContinueButton');
    const playerMessage = document.getElementById('playerMessage');
    const gameMessage = document.getElementById('gameMessage');
    let gameBoard = ['', '', '', '', '', '', '', '', ''];
    let currentPlayer = 'X';
    let mySymbol = null;
    let gameActive = true;
    const room = 'tic_tac_toe';
   
    const gamePrompt = document.getElementById('gamePrompt');
    const acceptContinueButton = document.getElementById('acceptContinueButton');
    const declineContinueButton = document.getElementById('declineContinueButton');

    socket.emit('join_game', { room });

    socket.on('player_assigned', (data) => {
        mySymbol = data.symbol;
        document.getElementById('playerMessage').innerText = `You are ${mySymbol}`;
        currentPlayer = mySymbol;
    });

    socket.on('update_board', (data) => {
        const { index, symbol } = data;
        gameBoard[index] = symbol;
        updateUI();
        currentPlayer = (symbol === 'X') ? 'O' : 'X';
        checkForWinOrDraw();
    });

    socket.on('load_game_state', (data) => {
        gameBoard = JSON.parse(data.board);
        currentPlayer = data.current_player;
        updateUI();
        gameActive = true;
        gameMessage.innerText = '';
    });

    socket.on('reset_board', () => {
        resetGameState()
        updateUI()
    });

    socket.on('askToContinue', () => {
        console.log("Received askToContinue request");
        gamePrompt.style.display = "block"; // Show modal
    });

    acceptContinueButton.addEventListener("click", () => {
        socket.emit("confirm_continue_game", { room });
        gamePrompt.style.display = "none";
        socket.emit("continue_game", { room });
    });

    declineContinueButton.addEventListener("click", () => {
        gamePrompt.style.display = "none"; // Hide modal
    });

    askToContinueButton.addEventListener('click', () => {
        setTimeout(() => {
            socket.emit('askToContinue', { room });
            console.log("Sent askToContinue event");
        }, 200); 
    });
    cells.forEach(cell => cell.addEventListener('click', cellClicked));
    resetButton.addEventListener('click', resetGame);
    continueButton.addEventListener('click', continueGame);
   
    function cellClicked(event) {
        const cellIndex = parseInt(event.target.id.replace('cell-', '')) - 1;
        if (gameBoard[cellIndex] !== '' || !gameActive || currentPlayer !== mySymbol) return;
        gameBoard[cellIndex] = mySymbol;
        socket.emit('make_move', { room, index: cellIndex, symbol: mySymbol });
        updateUI();
        checkForWinOrDraw();
    }

    function checkForWinOrDraw() {
        const winConditions = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]];
        for (let [a, b, c] of winConditions) {
            if (gameBoard[a] && gameBoard[a] === gameBoard[b] && gameBoard[a] === gameBoard[c]) {
                announceWinner(gameBoard[a]);
                gameActive = false;
                return;
            }
        }

        if (!gameBoard.includes('')) {
            announceDraw();
            gameActive = false;
        }
    }

    function announceWinner(player) {
        document.getElementById('gameMessage').innerText = `${player} wins!`;
    }

    function announceDraw() {
        document.getElementById('gameMessage').innerText = `Draw!`;
    }

    function updateUI() {
        cells.forEach((cell, index) => {
            cell.innerText = gameBoard[index] || '';
        });
    }

    function resetGame() {
        socket.emit('reset_game', { room });
        resetGameState();
        updateUI();
    }

    function continueGame() {
        socket.emit('continue_game', { room });
    }

    function resetGameState() {
        gameBoard = ['', '', '', '', '', '', '', '', ''];
        gameActive = true;
        currentPlayer = 'X';
        document.getElementById('gameMessage').innerText = '';
    }
});