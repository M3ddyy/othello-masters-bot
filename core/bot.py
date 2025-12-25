import os
import telebot
import json
from telebot import types
from game import Othello
import time

TOKEN = os.environ.get("TELEGRAM_TOKEN")
STATS_FILE = 'stats.json'
bot = telebot.TeleBot(TOKEN)

games = {}
user_stats = {}


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


@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    itembtn1 = types.KeyboardButton('🎲 بازی جدید')
    itembtn2 = types.KeyboardButton('📊 سابقه من')
    markup.add(itembtn1, itembtn2)
    bot.send_message(
        message.chat.id,
        "به بازی اتللو خوش آمدید! ⚫️⚪️\nبرای شروع، 'بازی جدید' را انتخاب کنید.",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == '🎲 بازی جدید')
def new_game_handler(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("🎮 بازی با هوش مصنوعی", callback_data='vs_ai')
    markup.row(btn1)
    bot.send_message(message.chat.id, "حریف خود را انتخاب کنید:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == '📊 سابقه من')
def show_history_handler(message):
    user_id = str(message.from_user.id)
    if user_id in user_stats:
        stats = user_stats[user_id]
        reply = (
            f"📈 آمار بازی‌های شما:\n\n"
            f"کل بازی‌ها: {stats['total']}\n"
            f"✅ برد: {stats['win']}\n"
            f"❌ باخت: {stats['loss']}\n"
            f"🤝 مساوی: {stats['draw']}"
        )
    else:
        reply = "شما هنوز هیچ بازی ثبت شده‌ای ندارید. یک بازی جدید شروع کنید!"
    bot.send_message(message.chat.id, reply)


@bot.callback_query_handler(func=lambda call: True)
def main_callback_handler(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    if call.data == 'vs_ai':
        bot.answer_callback_query(call.id)
        games[chat_id] = Othello()
        bot.edit_message_text("بازی شروع شد! شما ⚫️ هستید.", chat_id, call.message.message_id)
        time.sleep(1)
        send_board(chat_id)
        return

    if call.data.startswith('move_'):
        handle_player_move(call)


def handle_player_move(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    game = games.get(chat_id)

    if not game or game.current_player != game.player_black:
        bot.answer_callback_query(call.id, "⏳ نوبت شما نیست!", show_alert=True)
        return

    _, r_str, c_str = call.data.split('_')
    r, c = int(r_str), int(c_str)

    if game.make_move(r, c, game.player_black):
        bot.answer_callback_query(call.id, f"حرکت شما: {r + 1},{c + 1}")
        process_game_turn(chat_id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "حرکت غیرمجاز! ❌", show_alert=True)


def process_game_turn(chat_id, message_id):
    game = games.get(chat_id)
    user_id = chat_id

    send_board(chat_id, message_id)
    time.sleep(1)

    while game.current_player == game.player_white:
        if check_game_over(chat_id, message_id):
            return

        bot.edit_message_text(f"{create_board_string(game)}\n\n⏳ نوبت هوش مصنوعی (⚪️)...",
                              chat_id, message_id, reply_markup=None)
        time.sleep(1.5)

        ai_move = game.get_ai_move()
        if ai_move:
            game.make_move(ai_move[0], ai_move[1], game.player_white)
            send_board(chat_id, message_id)
            time.sleep(1)
        else:
            game.current_player = game.get_opponent(game.current_player)
            bot.send_message(chat_id, "هوش مصنوعی حرکتی برای انجام نداشت. نوبت شماست.")
            break

    if check_game_over(chat_id, message_id):
        return

    if not game.get_valid_moves(game.player_black):
        bot.send_message(chat_id, "شما حرکتی برای انجام ندارید! نوبت به هوش مصنوعی واگذار می‌شود.")
        game.current_player = game.get_opponent(game.current_player)
        process_game_turn(chat_id, message_id)
    else:
        send_board(chat_id, message_id)


def check_game_over(chat_id, message_id):
    game = games.get(chat_id)
    player_moves = game.get_valid_moves(game.player_black)
    opponent_moves = game.get_valid_moves(game.player_white)

    if not player_moves and not opponent_moves:
        score = game.get_score()
        black_score = score.get(game.player_black, 0)
        white_score = score.get(game.player_white, 0)

        if black_score > white_score:
            result_text = f"🎉 تبریک! شما برنده شدید! 🎉\nنتیجه: ⚫️ {black_score} - {white_score} ⚪️"
            update_stats(chat_id, 'win')
        elif white_score > black_score:
            result_text = f"😕 شما باختید.\nنتیجه: ⚫️ {black_score} - {white_score} ⚪️"
            update_stats(chat_id, 'loss')
        else:
            result_text = f"🤝 بازی مساوی شد!\nنتیجه: ⚫️ {black_score} - {white_score} ⚪️"
            update_stats(chat_id, 'draw')

        bot.edit_message_text(f"{create_board_string(game)}\n\n--- بازی تمام شد ---\n{result_text}",
                              chat_id, message_id, reply_markup=None)
        del games[chat_id]
        return True
    return False


def create_board_keyboard(game):
    markup = types.InlineKeyboardMarkup(row_width=8)
    buttons = []
    valid_moves = game.get_valid_moves(game.current_player)

    for r in range(game.board_size):
        row_buttons = []
        for c in range(game.board_size):
            if game.board[r][c] == game.empty_square:
                if game.current_player == game.player_black and (r, c) in valid_moves:
                    button_text = ' '
                else:
                    button_text = ' '
                row_buttons.append(types.InlineKeyboardButton(button_text, callback_data=f"move_{r}_{c}"))
            else:
                row_buttons.append(types.InlineKeyboardButton(game.board[r][c], callback_data=f"move_{r}_{c}"))
        buttons.append(row_buttons)

    markup.keyboard = buttons
    return markup


def create_board_string(game):
    score = game.get_score()
    black_score = score.get(game.player_black, 0)
    white_score = score.get(game.player_white, 0)

    turn_text = "نوبت شما (⚫️)" if game.current_player == game.player_black else "نوبت هوش مصنوعی (⚪️)"

    return f"امتیاز: ⚫️ {black_score} - {white_score} ⚪️\n\n{turn_text}"


def send_board(chat_id, message_id=None):
    game = games.get(chat_id)
    if not game: return

    text = create_board_string(game)
    markup = create_board_keyboard(game)

    try:
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)
    except telebot.apihelper.ApiTelegramException as e:
        if 'message is not modified' in e.description:
            pass
        else:
            raise


if __name__ == '__main__':
    load_stats()
    print("Bot is running...")
    bot.polling(none_stop=True)
