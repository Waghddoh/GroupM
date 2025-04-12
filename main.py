import logging
import os
from telegram.helpers import escape_markdown
from telegram import ChatMemberAdministrator, ChatMemberOwner, Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest, TelegramError # For error handling
from telegram.constants import ChatMemberStatus # For checking user/bot status
# --- Configuration ---
# Get your bot token from BotFather on Telegram
# It's recommended to use environment variables for security
BOT_TOKEN = "8051475949:AAHy394IA7n-u2fyxQj7mqsHvTqcyJYaIf4" # Replace with your token or set env variable

# --- Logging Setup ---
# Enable logging to see errors and bot activity
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Set higher logging level for httpx to avoid GET/POST requests logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /start command.
    Sends a welcome message. In private chat, includes a button to add the bot to a group,
    requesting specific admin rights upon addition.
    """
    print("Update in Start Command" , update)
    user = update.effective_user
    chat = update.effective_chat
    bot_info = await context.bot.get_me()
    bot_username = bot_info.username
    
    

    # Check if the command is used in a group or private chat
    if chat.type == "private":
        # Create the URL for the "Add to Group" button, requesting admin rights
        add_group_url = f"https://t.me/{bot_username}?startgroup=botstart"

        # Create the inline keyboard button
        keyboard = [
            [InlineKeyboardButton("➕ Add me to a group (as Admin)", url=add_group_url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        start_message = (
            f"Hello {user.mention_html()}! 👋\n\n"
            "I'm a group management bot. Click the button below to add me to your group.\n\n"
            "ℹ️ <b>Important:</b> Please grant the requested admin permissions so I can manage the group effectively (delete messages, restrict users, pin messages, etc.).\n\n"
            "Use /help to see available commands."
        )
        
        await update.message.reply_html(
            start_message,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

    else: 
        start_payload = context.args[0] if context.args else None
        if start_payload == "verify_perms":
            try:
                bot_member = await context.bot.get_chat_member(chat.id, bot_info.id)
                if bot_member.status == 'administrator':
                    # You could add a more detailed check here for specific permissions
                    start_message = (
                        f"Hello everyone! 👋 I'm ready to help manage this group.\n\n"
                        f"Thanks for having me, {user.mention_html()}!"
                    )
                else:
                    start_message = (
                        f"Hello everyone! 👋 Thanks for adding me, {user.mention_html()}!\n\n"
                        f"⚠️ Please promote me to an admin with permissions (delete messages, restrict users, pin messages) so I can function correctly."
                    )
            except Exception as e:
                logger.error(f"Could not check bot status in group {chat.id}: {e}")
                start_message = (
                    f"Hello everyone! 👋 Thanks for adding me, {user.mention_html()}!\n\n"
                    f"⚠️ Please ensure I have admin permissions to function correctly."
                )
        else:
            # Handle regular /start command in the group (not triggered by the special add link)
            regular_start_message = (
                f"Hello {update.effective_user.mention_html()}! I'm already here to help manage the group."
                # You could add a quick permission check here too if desired
            )
            await update.message.reply_html(regular_start_message, disable_web_page_preview=True)

            # No button needed when already in a group
            await update.message.reply_html(start_message, disable_web_page_preview=True)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /help command.
    Displays a list of available commands.
    """
    # In the future, you can dynamically generate this list based on registered commands
    commands_list = [
        "/start - Initial greeting / Add to group button.",
        "/help - Shows this help message.",
        "/info - Show chat and user info (groups only).",
    ]
    help_text = "Here are the commands I understand:\n" + "\n".join(commands_list)
    await update.message.reply_text(help_text)

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /info command in groups.
    Shows basic information about the group and the user who invoked it.
    """
    user = update.effective_user
    chat = update.effective_chat

    if chat.type == "private":
        await update.message.reply_text("This command only works in groups.")
        return

    # --- Escape dynamic content for MarkdownV2 ---
    # Escape characters like *, _, `, [, etc. in names and titles
    safe_chat_title = escape_markdown(chat.title or "N/A", version=2)
    safe_user_fullname = escape_markdown(user.full_name or "N/A", version=2)
    safe_username = f"@{escape_markdown(user.username, version=2)}" if user.username else "N/A"

    # --- Use MarkdownV2 syntax ---
    info_text = (
        f"ℹ️ *Group Info*\n"  # Use * for bold
        f"*Title:* {safe_chat_title}\n"
        f"*Chat ID:* `{chat.id}`\n"  # Use ` for fixed-width code
        f"*Type:* {escape_markdown(chat.type or 'N/A', version=2)}\n\n" # Also escape chat type just in case
        f"👤 *User Info*\n"
        f"*Name:* {safe_user_fullname}\n"
        f"*User ID:* `{user.id}`\n"
        f"*Username:* {safe_username}"
    )
    await update.message.reply_markdown_v2(info_text) # Using HTML for easier formatting


async def pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /pin command to pin the message replied to.

    Requires the bot to have 'can_pin_messages' permission.
    Requires the user invoking the command to be an administrator.
    Only works in group chats.
    """
    chat = update.effective_chat
    user = update.effective_user
    message = update.message # The message containing the /pin command

    # 1. Check if the command is used in a group/supergroup
    if not chat or chat.type not in [chat.GROUP, chat.SUPERGROUP]:
        # Silently ignore or reply if needed, but typically pin only makes sense in groups
        # await message.reply_text("This command only works in groups.")
        logger.debug(f"/pin command ignored in non-group chat {chat.id if chat else 'N/A'}")
        return

    # 2. Check if the command is a reply to a message
    if not message.reply_to_message:
        await message.reply_text("Please reply to the message you want to pin.")
        return

    message_to_pin_id = message.reply_to_message.message_id
    chat_id = chat.id
    bot_id = context.bot.id

    try:
        # 3. Check bot's permissions
        bot_member = await context.bot.get_chat_member(chat_id, bot_id)
        if not isinstance(bot_member, (ChatMemberAdministrator, ChatMemberOwner)) or not bot_member.can_pin_messages:
             # Check if bot is admin and has the specific right
             # Note: Bot needs to be admin to have can_pin_messages typically
             if not getattr(bot_member, 'can_pin_messages', False):
                await message.reply_text("I don't have permission to pin messages in this group. Please grant me the 'Pin Messages' right.")
                return

        # 4. Check user's permissions (must be admin or creator)
        user_member = await context.bot.get_chat_member(chat_id, user.id)
        if user_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text("Only group admins can pin messages.")
            return
        # Optional stricter check: if user_member.status == ChatMemberStatus.ADMINISTRATOR and not user_member.can_pin_messages:
        #     await message.reply_text("You have admin status, but lack the specific permission to pin messages.")
        #     return


        # 5. Attempt to pin the message
        await context.bot.pin_chat_message(
            chat_id=chat_id,
            message_id=message_to_pin_id,
            disable_notification=False # Set to True to pin silently
        )
        # Send confirmation reply to the original /pin command message
        await message.reply_text("Message pinned successfully! 👍" , do_quote=False)
        logger.info(f"User {user.id} pinned message {message_to_pin_id} in chat {chat_id}")

        try:
            await message.delete()
        except Exception as delete_err:
            logger.warning(f"Could not delete /pin command message {message.message_id}: {delete_err}")


    except BadRequest as e:
        logger.error(f"Error pinning message {message_to_pin_id} in chat {chat_id}: {e}")
        if "message to pin not found" in e.message.lower():
            await message.reply_text("Sorry, I couldn't find the message you replied to (it might have been deleted).")
        elif "chat not found" in e.message.lower():
             await message.reply_text("Error: Chat not found.") # Should not happen if initial checks pass
        elif "not enough rights" in e.message.lower():
             await message.reply_text("Failed to pin. Please double-check my admin permissions.")
        else:
            await message.reply_text(f"An error occurred: {e.message}")
    except TelegramError as e:
        logger.error(f"Telegram error pinning message {message_to_pin_id} in chat {chat_id}: {e}")
        await message.reply_text("A Telegram error occurred while trying to pin the message.")
    except Exception as e:
        logger.exception(f"Unexpected error in pin_command for chat {chat_id}: {e}")
        await message.reply_text("An unexpected error occurred.")

# --- Bot Setup and Run ---

async def post_init(application: Application) -> None:
    """
    Sets the bot commands list that users see in Telegram clients.
    """
    await application.bot.set_my_commands([
        BotCommand("start", "Start interacting with the bot"),
        BotCommand("help", "Show help message"),
        BotCommand("info", "Show chat and user info (groups only)"),
        # Add other commands here
    ])
    logger.info("Bot commands set.")

def main() -> None:
    """Starts the bot."""
    # --- Input Validation ---
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        logger.error("FATAL: Telegram Bot Token not found. Please set the TELEGRAM_BOT_TOKEN environment variable or replace the placeholder in the script.")
        return

    # --- Application Setup ---
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # --- Register Handlers ---
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info_command, filters=filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("pin", pin_command, filters=filters.ChatType.GROUPS))

    # --- Start the Bot ---
    logger.info("Starting bot polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
