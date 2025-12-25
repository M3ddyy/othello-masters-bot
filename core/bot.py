import os
import telebot
from telebot import types
from core.game import Game

TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("توکن ربات پیدا نشد! مطمئن شو TELEGRAM_TOKEN ست شده.")

bot = telebot.TeleBot(TOKEN)
game = Game()

def get_board_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=8)
    buttons = []
    for i in range(8):
        for j in range(8):
            cell = game.board[i][j]
            if cell == 'B':
                text = '⚫'
            elif cell == 'W':
                text = '⚪'
            else:
                text = '\u200b'
            buttons.append(types.InlineKeyboardButton(text=text, callback_data=f"{i},{j}"))
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! ربات اتللو آماده‌ست 🎮\n/newgame برای شروع بازی")

@bot.message_handler(commands=['newgame'])
def new_game(message):
    global game
    game = Game()
    game.players['B'] = message.chat.id
    bot.send_message(message.chat.id, "شما بازیکن سیاه ⚫ هستید. منتظر بازیکن سفید باشید و از /join استفاده کنید.")

@bot.message_handler(commands=['join'])
def join_game(message):
    if message.chat.id == game.players.get('B'):
        bot.send_message(message.chat.id, "شما قبلاً بازیکن سیاه هستید!")
        return

    if 'W' not in game.players:
        game.players['W'] = message.chat.id
        bot.send_message(message.chat.id, "شما بازیکن سفید ⚪ هستید!")
        bot.send_message(game.players['B'], "بازیکن دوم به بازی پیوست! بازی شروع شد")

        keyboard = get_board_keyboard()
        for pid in game.players.values():
            bot.send_message(pid, f"شروع بازی! نوبت بازیکن: {game.current_player}", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "بازی پر شده!")

@bot.callback_query_handler(func=lambda call: True)
def handle_move(call):
    player_id = game.players.get(game.current_player)
    if call.message.chat.id != player_id:
        bot.answer_callback_query(call.id, "فعلاً نوبت شما نیست")
        return

    x, y = map(int, call.data.split(','))
    if not game.make_move(x, y):
        bot.answer_callback_query(call.id, "حرکت نامعتبر!")
        return

    new_text = f"نوبت بازیکن: {game.current_player}"
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=new_text,
        reply_markup=get_board_keyboard()
    )
    bot.answer_callback_query(call.id, "حرکت انجام شد!")

    if game.is_game_over():
        b_count, w_count = game.get_score()
        winner = 'B' if b_count > w_count else 'W' if w_count > b_count else 'هیچکس'
        for pid in game.players.values():
            bot.send_message(pid, f"بازی تمام شد! ⚫: {b_count} ⚪: {w_count}\nبرنده: {winner}")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
