import os
import telebot

TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not TOKEN:
    raise ValueError("توکن ربات پیدا نشد! مطمئن شو TELEGRAM_TOKEN تنظیم شده.")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! ربات اتللو آماده‌ست 🎮")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
