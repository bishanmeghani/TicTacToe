from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import uuid
import sqlite3
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, async_mode='eventlet')
rooms = {}

def init_db():
    conn = sqlite3.connect('tictactoe.db')
    cursor = conn.cursor()
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS WinStats (
            player TEXT PRIMARY KEY,
            wins INTEGER DEFAULT 0           
        )
    ''')
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS GameState (
            room TEXT PRIMARY KEY,
            board TEXT NOT NULL,
            current_player TEXT NOT NULL           
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    player_id = str(uuid.uuid4())
    return render_template('index.html', player_id = player_id)

@socketio.on('askToContinue')
def handle_ask_continue(data):
    room = data['room']
    emit('askToContinue', {'room': room}, room=room, include_self=False)

@socketio.on('confirm_continue_game')
def handle_confirm_continue_game(data):
    room = data['room']
    emit('continue_game_confirmed', {}, room=room)


@socketio.on('join_game')
def handle_join_game(data):
    room = data['room']
    join_room(room)

    if room not in rooms:
        rooms[room] = {'players': [], 'board': ['', '', '', '', '', '', '', '', ''], 'current_player': 'X'}

    symbol = 'X' if len(rooms[room]['players']) % 2 == 0 else 'O'
    rooms[room]['players'].append(symbol)

    emit('player_assigned', {'symbol': symbol})
    emit('player_joined', {'player': request.sid}, room=room)

@socketio.on('make_move')
def handle_make_move(data):
    room = data['room']
    index = data['index']
    symbol = data['symbol']

    if room in rooms:
        if rooms[room]['current_player'] != symbol:
            return
        
        rooms[room]['board'][index] = symbol
        rooms[room]['current_player'] = 'O' if symbol == 'X' else 'X'
        save_game_state(room, rooms[room]['board'], rooms[room]['current_player'])
        emit('update_board', {'index': index, 'symbol': symbol}, room=room)
        check_for_win_or_draw(room)

@socketio.on('continue_game')
def handle_continue_game(data):
    room = data['room']
    conn = sqlite3.connect('tictactoe.db')
    cursor = conn.cursor()
    cursor.execute('SELECT board, current_player FROM GameState WHERE room = ?', (room,))
    row = cursor.fetchone()
    conn.close()

    if row:
        board_str, current_player = row
        board = json.loads(board_str)
        if room in rooms:
            players = rooms[room]['players']
        else:
            players = []
        rooms[room] = {'board': board, 'current_player': current_player, 'players': players}
        emit('load_game_state', {'board': json.dumps(board), 'current_player': current_player}, room=room)

def check_for_win_or_draw(room):
    board = rooms[room]['board']
    win_conditions = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]

    for condition in win_conditions:
        a, b, c = condition
        if board[a] != '' and board[a] == board[b] == board[c]:
            emit('winner', {'winner': board[a]}, room=room)
            update_win_stats(board[a])
            return
        
    if '' not in board:
        emit('draw', {}, room=room)

def update_win_stats(winner):
    conn = sqlite3.connect('tictactoe.db')
    cursor = conn.cursor()
    cursor.execute('SELECT wins FROM WinStats WHERE player = ?', (winner,))
    row = cursor.fetchone()
    if row:
        cursor.execute('UPDATE WinStats SET wins = wins + 1 WHERE player = ?', (winner,))
    else:
        cursor.execute('INSERT INTO WinStats (player, wins) VALUES (?, 1)', (winner,))
    conn.commit()    
    conn.close()

def save_game_state(room, board, current_player):
    conn = sqlite3.connect('tictactoe.db')
    cursor = conn.cursor()
    board_str = json.dumps(board)
    cursor.execute('INSERT OR REPLACE INTO GameState (room, board, current_player) VALUES (?, ?, ?)''', (room, board_str, current_player))
    conn.commit()    
    conn.close()

@socketio.on('reset_game')
def handle_reset_game(data):
    room = data['room']
    if room in rooms:
        rooms[room]['board'] = ['','','','','','','','','']
        rooms[room]['current_player'] = 'X'
        rooms[room]['players'] = []

        conn = sqlite3.connect('tictactoe.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM GameState WHERE room = ?', (room,))
        conn.commit()    
        conn.close()

    emit('reset_board', {}, room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)