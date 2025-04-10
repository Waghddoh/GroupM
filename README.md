# Telegram Group Management Bot

## Description

This Python script implements a basic Telegram bot designed for group management tasks using the `python-telegram-bot` library. It provides essential commands to interact with users and manage group settings.

## Features

The bot currently supports the following commands:

*   `/start`:
    *   In private chat: Sends a welcome message with a button to add the bot to a group, requesting necessary admin permissions.
    *   In group chat: Sends a welcome message and can verify its admin permissions if added via the special link.
*   `/help`: Displays a list of available commands and their descriptions.
*   `/info` (Groups only): Shows information about the current group (Title, ID, Type) and the user who invoked the command (Name, ID, Username).
*   `/pin` (Groups only): Pins the message replied to. Requires both the bot and the invoking user to have pin permissions.

## Setup

1.  **Prerequisites:**
    *   Python 3.x
    *   `python-telegram-bot` library (`pip install python-telegram-bot`)

2.  **Bot Token:**
    *   Obtain a bot token from BotFather on Telegram.
    *   Replace the placeholder `BOT_TOKEN = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"` in `main.py` with your actual token, or preferably, set it as an environment variable named `TELEGRAM_BOT_TOKEN`.

3.  **Run the Bot:**
    ```bash
    python main.py
    ```

## Dependencies

*   [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

## How it Works

The bot uses command handlers (`CommandHandler`) to react to specific user commands (`/start`, `/help`, etc.). It interacts with the Telegram Bot API to send messages, retrieve chat/user information, and perform administrative actions like pinning messages. Error handling and logging are included for easier debugging.
