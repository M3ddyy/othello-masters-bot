# Telegram Othello Bot ⚫️⚪️

This project is a Telegram bot that allows users to play the classic board game **Othello**. Built using the `pyTelegramBotAPI` library in Python, the bot supports both single-player mode against a simple AI and two-player mode with friends.

---

## 🌟 Features

- ✅ **Single-player mode:** Play against a basic AI that chooses moves randomly.
- ✅ **Two-player mode:** Invite friends for a real-time game using Telegram's Inline Mode.
- ✅ **Graphical game board:** Emojis (⚫️, ⚪️, 🟢) represent pieces and legal moves.
- ✅ **Interactive user interface:** Make moves with a single click using Inline Keyboard buttons.
- ✅ **Player names displayed:** Shows each player's name in turn and win messages for a personalized experience.
- ✅ **Game statistics:** Records and displays each user's wins, losses, and draws in a JSON file.
- ✅ **Surrender option:** Players can forfeit the game using the "End Game" button.
- ✅ **Complete rules:** Implements all official Othello rules, including skipping a turn if no legal moves are available.

---

## 🚀 Setup & Installation

```bash
# 1. Clone the repository
git clone [YOUR_REPOSITORY_URL]
cd [PROJECT_FOLDER_NAME]

# 2. Install dependencies
pip install pyTelegramBotAPI

# 3. Set the Bot Token
# Go to BotFather on Telegram, create a new bot with /newbot
# Copy the token and paste it into core/bot.py where indicated

# 4. Enable Inline Mode
# Go to BotFather, send /mybots, select your bot
# Navigate to Bot Settings → Inline Mode → Turn on

# 5. Run the bot
python core/bot.py

# Project Structure
.
├── core/
│   ├── bot.py          # Main bot file: handles commands and user interactions
│   └── game.py         # Game engine: contains the Othello class and all game rules
├── stats.json          # Stores user win/loss/draw statistics
└── README.md           # This file
