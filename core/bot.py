import os
import telebot
from telebot import types
from core.game import Game

TOKEN = os.environ.get("TELEGRAM_TOKEN")
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
    bot.reply_to(message, "سلام! ربات اتللو آماده‌ست 🎮")

@bot.message_handler(commands=['newgame'])
def new_game(message):
    global game
    game = Game()
    bot.send_message(
        message.chat.id,
        f"شروع بازی! نوبت بازیکن: {game.current_player}",
        reply_markup=get_board_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_move(call):
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


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
