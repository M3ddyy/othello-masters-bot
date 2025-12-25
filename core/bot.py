import os
import telebot
import json
import uuid
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

@bot.inline_handler(lambda query: True)
def inline_query_handler(inline_query):
    try:
        user = inline_query.from_user
        game_id = str(uuid.uuid4())
        games[game_id] = Othello(player1_id=user.id, player1_name=user.first_name)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🤝 قبول کردن چالش", callback_data=f"accept_{game_id}"))
        response = types.InlineQueryResultArticle(
            id=game_id,
            title="🎲 چالش بازی اتللو",
            description=f"{user.first_name} شما را به یک بازی دعوت کرده. کلیک کنید.",
            reply_markup=markup,
            input_message_content=types.InputTextMessageContent(
                f"⚫️ {user.first_name} شما را به یک بازی اتللو دعوت کرده!\n\n⚪️ منتظر حریف برای پیوستن..."
            )
        )
        bot.answer_inline_query(inline_query.id, [response], cache_time=1)
    except Exception as e:
        print(f"Error in inline_query_handler: {e}")

@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('🎲 بازی جدید'), types.KeyboardButton('📊 سابقه من'))
    bot.send_message(message.chat.id, "به بازی اتللو خوش آمدید! ⚫️⚪️", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '🎲 بازی جدید')
def new_game_handler(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("🎮 بازی با هوش مصنوعی", callback_data='vs_ai')
    btn2 = types.InlineKeyboardButton("🤝 بازی با دوست", switch_inline_query='')
    markup.row(btn1)
    markup.row(btn2)
    bot.send_message(message.chat.id, "حریف خود را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '📊 سابقه من')
def show_history_handler(message):
    user_id = str(message.from_user.id)
    if user_id in user_stats and user_stats[user_id]['total'] > 0:
        stats = user_stats[user_id]
        reply = (
            f"📈 آمار بازی‌های شما:\n\n"
            f"کل بازی‌ها: {stats['total']}\n"
            f"✅ برد: {stats['win']}\n"
            f"❌ باخت: {stats['loss']}\n"
            f"🤝 مساوی: {stats['draw']}"
        )
    else:
        reply = "شما هنوز هیچ بازی ثبت شده‌ای ندارید."
    bot.send_message(message.chat.id, reply)

@bot.callback_query_handler(func=lambda call: True)
def main_callback_handler(call):
    if call.data == 'vs_ai':
        start_ai_game(call)
    elif call.data.startswith('accept_'):
        accept_2p_game(call)
    elif call.data.startswith('move_'):
        handle_player_move(call)
    elif call.data.startswith('forfeit_'):
        handle_forfeit(call)

def start_ai_game(call):
    chat_id = call.message.chat.id
    user = call.from_user
    game_id = str(chat_id)
    games[game_id] = Othello(
        player1_id=user.id,
        player1_name=user.first_name,
        player2_name="هوش مصنوعی"
    )
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"بازی با هوش مصنوعی شروع شد! شما {user.first_name} (⚫️) هستید.",
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
        bot.answer_callback_query(call.id, "این بازی منقضی شده است.", show_alert=True)
        return
    if game.player1_id == user.id:
        bot.answer_callback_query(call.id, "نمی‌توانید با خودتان بازی کنید!", show_alert=True)
        return
    if game.player2_id is not None:
        bot.answer_callback_query(call.id, "این بازی قبلاً شروع شده.", show_alert=True)
        return

    game.player2_id = user.id
    game.player2_name = user.first_name
    game.inline_message_id = call.inline_message_id
    bot.answer_callback_query(call.id, "شما چالش را پذیرفتید!")
    update_board_two_player(game_id)

def handle_forfeit(call):
    try:
        _, mode, game_id = call.data.split('_')
    except ValueError:
        bot.answer_callback_query(call.id, "خطا در پردازش درخواست.", show_alert=True)
        return

    game = games.get(game_id)
    forfeiting_user = call.from_user

    if not game:
        bot.answer_callback_query(call.id, "بازی یافت نشد.", show_alert=True)
        return

    update_stats(forfeiting_user.id, 'loss')

    if mode == 'ai':
        final_text = " شما در مقابل هوش مصنوعی تسلیم شدید.\n\n🎉 هوش مصنوعی برنده شد!"
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
            f" بازیکن {forfeiting_user.first_name} تسلیم شد.\n\n"
            f"🎉 {winner_name} برنده شد!"
        )

    full_final_text = f"--- بازی تمام شد ---\n{final_text}"

    if mode == 'ai':
        bot.edit_message_text(
            full_final_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
    elif hasattr(game, 'inline_message_id'):
        bot.edit_message_text(
            full_final_text,
            inline_message_id=game.inline_message_id,
            reply_markup=None
        )

    games.pop(game_id, None)
    bot.answer_callback_query(call.id, "شما بازی را واگذار کردید.")

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
    current_player_id = game.get_current_player_id() if mode == '2p' else user_id

    if user_id != current_player_id:
        bot.answer_callback_query(call.id, "⏳ نوبت شما نیست!", show_alert=True)
        return

    if game.make_move(r, c, game.current_player):
        bot.answer_callback_query(call.id)
        if mode == 'ai':
            process_game_turn_ai(game_id, call.message)
        else:
            if not game.get_valid_moves(game.current_player):
                game.current_player = game.get_opponent(game.current_player)
            if not check_game_over(game_id):
                update_board_two_player(game_id)
    else:
        bot.answer_callback_query(call.id, "حرکت غیرمجاز! ❌", show_alert=True)


def process_game_turn_ai(game_id, message):
    game = games.get(game_id)
    chat_id = message.chat.id

    send_board_single_player(game_id, message)
    time.sleep(1)

    if game.current_player == game.player_white:
        if check_game_over(game_id, message=message):
            return
        time.sleep(1.5)
        ai_move = game.get_ai_move()
        if ai_move:
            game.make_move(ai_move[0], ai_move[1], game.player_white)
        else:
            game.current_player = game.player_black

        send_board_single_player(game_id, message)

    if check_game_over(game_id, message=message):
        return

    if not game.get_valid_moves(game.player_black):
        bot.send_message(chat_id, "شما حرکتی ندارید! نوبت به AI واگذار شد.")
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
        if 'message is not modified' not in str(e):
            print(e)

def send_board_single_player(game_id, message):
    game = games.get(game_id)
    if not game:
        return
    text = create_board_string(game, "ai")
    markup = create_board_keyboard(game, "ai", game_id)
    bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup)

def check_game_over(game_id, message=None):
    game = games.get(game_id)
    if not game:
        return True

    if not game.get_valid_moves(game.player_black) and not game.get_valid_moves(game.player_white):
        score = game.get_score()
        p1_score = score.get(game.player_black, 0)
        p2_score = score.get(game.player_white, 0)

        if p1_score > p2_score:
            result_text = f"🎉 {game.player1_name} ({game.player_black}) برنده شد!"
            update_stats(game.player1_id, 'win')
            update_stats(game.player2_id, 'loss')
        elif p2_score > p1_score:
            result_text = f"🎉 {game.player2_name} ({game.player_white}) برنده شد!"
            update_stats(game.player2_id, 'win')
            update_stats(game.player1_id, 'loss')
        else:
            result_text = "🤝 بازی مساوی شد!"
            update_stats(game.player1_id, 'draw')
            update_stats(game.player2_id, 'draw')

        final_text = f"{create_board_string(game, '')}\n\n--- بازی تمام شد ---\n{result_text}"

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

    if mode in ["ai", "2p"]:
        current_player_name = game.get_current_player_name() or "بازیکن"
        turn_text = f"نوبت {current_player_name} ({game.current_player})"
    else:
        turn_text = ""

    return f"امتیاز: ⚫️ {p1_score} - {p2_score} ⚪️\n{turn_text}"

def create_board_keyboard(game, mode, game_id):
    markup = types.InlineKeyboardMarkup(row_width=8)
    valid_moves = []
    player_turn = (mode == 'ai' and game.current_player == game.player_black) or mode == '2p'
    if player_turn:
        valid_moves = game.get_valid_moves(game.current_player)

    buttons = []
    for r in range(game.board_size):
        row_buttons = []
        for c in range(game.board_size):
            text_btn = game.board[r][c]
            cb_data = f"move_{mode}_{game_id}_{r}_{c}"
            if text_btn == game.empty_square and (r, c) in valid_moves:
                text_btn = '🟩'
            row_buttons.append(types.InlineKeyboardButton(text_btn, callback_data=cb_data))
        buttons.append(row_buttons)

    markup.keyboard = buttons
    markup.add(
        types.InlineKeyboardButton(
            "❌ اتمام بازی (تسلیم)",
            callback_data=f"forfeit_{mode}_{game_id}"
        )
    )
    return markup

if __name__ == '__main__':
    load_stats()
    print("Bot is running...")
    bot.polling(none_stop=True)
