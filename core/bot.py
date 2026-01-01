import os
import telebot
import json
import uuid
import time
from telebot import types
from game import Othello

TOKEN = os.environ.get("TELEGRAM_TOKEN")
STATS_FILE = 'stats.json'
bot = telebot.TeleBot(TOKEN)

games = {}
user_stats = {}

waiting_user = None
random_games_sessions = {}


def load_stats():
    global user_stats
    try:
        with open(STATS_FILE, 'r') as f:
            user_stats = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        user_stats = {}


def save_stats():
    with open(STATS_FILE, 'w') as f:
        json.dump(user_stats, f, indent=4)


def update_stats(user_id, result):
    user_id = str(user_id)
    if user_id not in user_stats:
        user_stats[user_id] = {'win': 0, 'loss': 0, 'draw': 0, 'total': 0}
    user_stats[user_id][result] += 1
    user_stats[user_id]['total'] += 1
    save_stats()


@bot.inline_handler(lambda query: True)
def inline_query_handler(inline_query):
    try:
        user = inline_query.from_user
        game_id = str(uuid.uuid4())
        games[game_id] = Othello(player1_id=user.id, player1_name=user.first_name)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🤝 Accept Challenge", callback_data=f"accept_{game_id}"))
        response = types.InlineQueryResultArticle(
            id=game_id,
            title="🎲 Othello Game Challenge",
            description=f"{user.first_name} has invited you to play. Tap to join.",
            reply_markup=markup,
            input_message_content=types.InputTextMessageContent(
                f"⚫️ {user.first_name} has invited you to play Othello!\n\n⚪️ Waiting for an opponent to join..."
            )
        )
        bot.answer_inline_query(inline_query.id, [response], cache_time=1)
    except Exception as e:
        print(f"Error in inline_query_handler: {e}")


@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('🎲 New Game'), types.KeyboardButton('📊 My Stats'))
    bot.send_message(message.chat.id, "Welcome to Othello! ⚫️⚪️", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == '🎲 New Game')
def new_game_handler(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("🎮 Play vs AI", callback_data='vs_ai')
    btn_random = types.InlineKeyboardButton("⚔️ Random Opponent", callback_data='random_queue')
    btn2 = types.InlineKeyboardButton("🤝 Play with a Friend", switch_inline_query='')
    markup.row(btn1)
    markup.row(btn_random)
    markup.row(btn2)
    bot.send_message(message.chat.id, "Choose your opponent:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == '📊 My Stats')
def show_history_handler(message):
    user_id = str(message.from_user.id)
    if user_id in user_stats and user_stats[user_id]['total'] > 0:
        stats = user_stats[user_id]
        reply = (
            f"📈 Your Game Statistics:\n\n"
            f"Total games: {stats['total']}\n"
            f"✅ Wins: {stats['win']}\n"
            f"❌ Losses: {stats['loss']}\n"
            f"🤝 Draws: {stats['draw']}"
        )
    else:
        reply = "You haven't played any games yet."
    bot.send_message(message.chat.id, reply)


@bot.callback_query_handler(func=lambda call: True)
def main_callback_handler(call):
    if call.data == 'vs_ai':
        start_ai_game(call)
    elif call.data == 'random_queue':
        handle_random_queue(call)
    elif call.data.startswith('accept_'):
        accept_2p_game(call)
    elif call.data.startswith('move_'):
        handle_player_move(call)
    elif call.data.startswith('forfeit_'):
        handle_forfeit(call)


def handle_random_queue(call):
    global waiting_user
    user = call.from_user
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if waiting_user and waiting_user['id'] == user.id:
        waiting_user = None
        bot.edit_message_text("❌ You left the queue.", chat_id, message_id)
        return

    if waiting_user is None:
        waiting_user = {
            'id': user.id,
            'name': user.first_name,
            'chat_id': chat_id,
            'message_id': message_id
        }
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Cancel Search", callback_data="random_queue"))
        bot.edit_message_text(
            "🔍 Searching for an opponent...\n\nPlease wait for someone else to join.",
            chat_id, message_id, reply_markup=markup
        )
    else:
        opponent = waiting_user
        waiting_user = None

        game_id = str(uuid.uuid4())
        games[game_id] = Othello(
            player1_id=opponent['id'],
            player1_name=opponent['name'],
            player2_id=user.id,
            player2_name=user.first_name
        )

        random_games_sessions[game_id] = {
            'black': {'chat_id': opponent['chat_id'], 'msg_id': opponent['message_id']},
            'white': {'chat_id': chat_id, 'msg_id': message_id}
        }
        update_board_random(game_id)


def update_board_random(game_id):
    game = games.get(game_id)
    sessions = random_games_sessions.get(game_id)
    if not game or not sessions: return

    text = create_board_string(game, "rnd")
    markup = create_board_keyboard(game, "rnd", game_id)

    try:
        bot.edit_message_text(text, sessions['black']['chat_id'], sessions['black']['msg_id'], reply_markup=markup)
    except:
        pass

    try:
        bot.edit_message_text(text, sessions['white']['chat_id'], sessions['white']['msg_id'], reply_markup=markup)
    except:
        pass


def check_game_over_random(game_id):
    game = games.get(game_id)
    sessions = random_games_sessions.get(game_id)
    if not game: return True

    if not game.get_valid_moves(game.player_black) and not game.get_valid_moves(game.player_white):
        score = game.get_score()
        p1_score = score.get(game.player_black, 0)
        p2_score = score.get(game.player_white, 0)

        if p1_score > p2_score:
            result_text = f"🎉 {game.player1_name} Wins!"
            update_stats(game.player1_id, 'win')
            update_stats(game.player2_id, 'loss')
        elif p2_score > p1_score:
            result_text = f"🎉 {game.player2_name} Wins!"
            update_stats(game.player2_id, 'win')
            update_stats(game.player1_id, 'loss')
        else:
            result_text = "🤝 Draw!"
            update_stats(game.player1_id, 'draw')
            update_stats(game.player2_id, 'draw')

        final_text = f"{create_board_string(game, '')}\n\n--- Game Over ---\n{result_text}"

        try:
            bot.edit_message_text(final_text, sessions['black']['chat_id'], sessions['black']['msg_id'],
                                  reply_markup=None)
            bot.edit_message_text(final_text, sessions['white']['chat_id'], sessions['white']['msg_id'],
                                  reply_markup=None)
        except:
            pass

        games.pop(game_id, None)
        random_games_sessions.pop(game_id, None)
        return True
    return False

def start_ai_game(call):
    chat_id = call.message.chat.id
    user = call.from_user
    game_id = str(chat_id)
    games[game_id] = Othello(
        player1_id=user.id,
        player1_name=user.first_name,
        player2_name="AI"
    )
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"Game started vs AI! You are {user.first_name} (⚫️).",
        chat_id,
        call.message.message_id
    )
    time.sleep(0.5)
    send_board_single_player(game_id, call.message)


def accept_2p_game(call):
    game_id = call.data.split('_')[1]
    game = games.get(game_id)
    user = call.from_user

    if not game:
        bot.answer_callback_query(call.id, "This game has expired.", show_alert=True)
        return
    if game.player1_id == user.id:
        bot.answer_callback_query(call.id, "You can't play against yourself!", show_alert=True)
        return
    if game.player2_id is not None:
        bot.answer_callback_query(call.id, "This game has already started.", show_alert=True)
        return

    game.player2_id = user.id
    game.player2_name = user.first_name
    game.inline_message_id = call.inline_message_id
    bot.answer_callback_query(call.id, "You have accepted the challenge!")
    update_board_two_player(game_id)


def handle_forfeit(call):
    try:
        _, mode, game_id = call.data.split('_')
    except ValueError:
        bot.answer_callback_query(call.id, "Error processing.", show_alert=True)
        return

    game = games.get(game_id)
    forfeiting_user = call.from_user

    if not game:
        bot.answer_callback_query(call.id, "Game not found.", show_alert=True)
        return

    update_stats(forfeiting_user.id, 'loss')

    if mode == 'rnd':
        sessions = random_games_sessions.get(game_id)
        winner_name = game.player2_name if forfeiting_user.id == game.player1_id else game.player1_name
        winner_id = game.player2_id if forfeiting_user.id == game.player1_id else game.player1_id
        update_stats(winner_id, 'win')

        final_txt = f"🏳️ {forfeiting_user.first_name} surrendered.\n🎉 {winner_name} Wins!"
        try:
            bot.edit_message_text(final_txt, sessions['black']['chat_id'], sessions['black']['msg_id'], reply_markup=None)
            bot.edit_message_text(final_txt, sessions['white']['chat_id'], sessions['white']['msg_id'], reply_markup=None)
        except:
            pass
        games.pop(game_id, None)
        random_games_sessions.pop(game_id, None)
        return

    if mode == 'ai':
        final_text = "You Surrendered the game against the AI.\n\n🎉 The AI wins!"
    else:
        if forfeiting_user.id == game.player1_id:
            winner_id = game.player2_id
            winner_name = game.player2_name
        else:
            winner_id = game.player1_id
            winner_name = game.player1_name

        if winner_id:
            update_stats(winner_id, 'win')

        final_text = (
            f" Player {forfeiting_user.first_name} has Surrendered.\n\n"
            f"🎉 {winner_name} wins!"
        )

    full_final_text = f"--- Game Over ---\n{final_text}"

    if mode == 'ai':
        bot.edit_message_text(full_final_text, call.message.chat.id, call.message.message_id, reply_markup=None)
    elif hasattr(game, 'inline_message_id'):
        bot.edit_message_text(full_final_text, inline_message_id=game.inline_message_id, reply_markup=None)

    games.pop(game_id, None)
    bot.answer_callback_query(call.id, "You have Surrendered.")


def handle_player_move(call):
    try:
        _, mode, game_id, r_str, c_str = call.data.split('_')
        r, c = int(r_str), int(c_str)
    except ValueError:
        return

    game = games.get(game_id)
    if not game:
        return

    user_id = call.from_user.id

    if mode == 'rnd':
        current_player_id = game.get_current_player_id()
    elif mode == '2p':
        current_player_id = game.get_current_player_id()
    else:
        current_player_id = user_id

    if user_id != current_player_id:
        bot.answer_callback_query(call.id, "⏳ It's not your turn!", show_alert=True)
        return

    if game.make_move(r, c, game.current_player):
        bot.answer_callback_query(call.id)
        if mode == 'ai':
            process_game_turn_ai(game_id, call.message)
        elif mode == 'rnd':
            if not game.get_valid_moves(game.current_player):
                game.current_player = game.get_opponent(game.current_player)
                if not game.get_valid_moves(game.current_player):
                    check_game_over_random(game_id)
                    return

            if not check_game_over_random(game_id):
                update_board_random(game_id)
        else:
            if not game.get_valid_moves(game.current_player):
                game.current_player = game.get_opponent(game.current_player)
            if not check_game_over(game_id):
                update_board_two_player(game_id)
    else:
        bot.answer_callback_query(call.id, "❌ Invalid move!", show_alert=True)


def process_game_turn_ai(game_id, message):
    game = games.get(game_id)
    chat_id = message.chat.id

    send_board_single_player(game_id, message)
    time.sleep(1)

    if game.current_player == game.player_white:
        if check_game_over(game_id, message=message):
            return
        time.sleep(1.0)
        ai_move = game.get_ai_move()
        if ai_move:
            game.make_move(ai_move[0], ai_move[1], game.player_white)
        else:
            game.current_player = game.player_black

        send_board_single_player(game_id, message)

    if check_game_over(game_id, message=message):
        return

    if not game.get_valid_moves(game.player_black):
        bot.send_message(chat_id, "You have no valid moves! Turn passed to the AI.")
        game.current_player = game.player_white
        time.sleep(1)
        process_game_turn_ai(game_id, message)


def update_board_two_player(game_id):
    game = games.get(game_id)
    if not game or not hasattr(game, 'inline_message_id'):
        return
    text = create_board_string(game, "2p")
    markup = create_board_keyboard(game, "2p", game_id)
    try:
        bot.edit_message_text(text, inline_message_id=game.inline_message_id, reply_markup=markup)
    except Exception as e:
        if 'message is not modified' not in str(e): print(e)


def send_board_single_player(game_id, message):
    game = games.get(game_id)
    if not game:
        return
    text = create_board_string(game, "ai")
    markup = create_board_keyboard(game, "ai", game_id)
    try:
        bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup)
    except Exception as e:
        print(f"Error updating AI board: {e}")


def check_game_over(game_id, message=None):
    game = games.get(game_id)
    if not game:
        return True

    if not game.get_valid_moves(game.player_black) and not game.get_valid_moves(game.player_white):
        score = game.get_score()
        p1_score = score.get(game.player_black, 0)
        p2_score = score.get(game.player_white, 0)

        if p1_score > p2_score:
            result_text = f"🎉 {game.player1_name} wins!"
            update_stats(game.player1_id, 'win')
            update_stats(game.player2_id, 'loss')
        elif p2_score > p1_score:
            result_text = f"🎉 {game.player2_name} wins!"
            update_stats(game.player2_id, 'win')
            update_stats(game.player1_id, 'loss')
        else:
            result_text = "🤝 The game ended in a draw!"
            update_stats(game.player1_id, 'draw')
            update_stats(game.player2_id, 'draw')

        final_text = f"{create_board_string(game, '')}\n\n--- Game Over ---\n{result_text}"

        if message:
            bot.edit_message_text(final_text, message.chat.id, message.message_id, reply_markup=None)
        elif hasattr(game, 'inline_message_id'):
            bot.edit_message_text(final_text, inline_message_id=game.inline_message_id, reply_markup=None)

        games.pop(game_id, None)
        return True
    return False


def create_board_string(game, mode):
    score = game.get_score()
    p1_score = score.get(game.player_black, 0)
    p2_score = score.get(game.player_white, 0)

    if mode in ["ai", "2p", "rnd"]:
        current_player_name = game.get_current_player_name() or "Player"
        turn_text = f"{current_player_name}'s turn ({game.current_player})"
    else:
        turn_text = ""

    return f"Score: ⚫️ {p1_score} - {p2_score} ⚪️\n{turn_text}"


def create_board_keyboard(game, mode, game_id):
    markup = types.InlineKeyboardMarkup(row_width=8)
    valid_moves = []

    is_my_turn = False
    if mode == 'ai':
        is_my_turn = (game.current_player == game.player_black)
    else:
        is_my_turn = True

    if is_my_turn:
        valid_moves = game.get_valid_moves(game.current_player)

    buttons = []
    for r in range(game.board_size):
        row_buttons = []
        for c in range(game.board_size):
            text_btn = game.board[r][c]
            cb_data = f"move_{mode}_{game_id}_{r}_{c}"
            if text_btn == game.empty_square and (r, c) in valid_moves:
                text_btn = '🔷'
            row_buttons.append(types.InlineKeyboardButton(text_btn, callback_data=cb_data))
        buttons.append(row_buttons)

    markup.keyboard = buttons
    markup.add(
        types.InlineKeyboardButton(
            "❌ Surrender",
            callback_data=f"forfeit_{mode}_{game_id}"
        )
    )
    return markup


if __name__ == '__main__':
    load_stats()
    print("Bot is running...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Bot polling error: {e}")
            time.sleep(5)
