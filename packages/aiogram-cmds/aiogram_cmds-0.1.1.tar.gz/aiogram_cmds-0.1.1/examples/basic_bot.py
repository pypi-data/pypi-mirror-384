#!/usr/bin/env python3
"""
Basic Bot Example

A simple bot demonstrating basic command management with aiogram-cmds.
This example shows the simplest way to get started with aiogram-cmds.

Features:
- Auto-setup with default commands
- Basic message handlers
- Simple user interaction
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from aiogram_cmds.auto_setup import setup_commands_auto

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Bot token (set via environment variable)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Create bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Global variable to store command manager
command_manager = None


async def on_startup():
    """Called when bot starts up."""
    global command_manager

    logger.info("🚀 Starting bot...")

    # Automatically set up commands with sensible defaults
    command_manager = await setup_commands_auto(bot)

    logger.info("✅ Bot started and commands set up!")
    logger.info("📋 Available commands: /start, /help")


async def on_shutdown():
    """Called when bot shuts down."""
    logger.info("👋 Bot shutting down...")


# Message handlers
@dp.message(Command("start"))
async def handle_start(message: types.Message):
    """Handle /start command."""
    user_name = message.from_user.first_name or "there"

    await message.answer(
        f"👋 Hello {user_name}!\n\n"
        f"Welcome to the Basic Bot example!\n\n"
        f"This bot demonstrates basic command management with aiogram-cmds.\n\n"
        f"Use /help to see available commands."
    )

    logger.info(f"User {message.from_user.id} ({user_name}) started the bot")


@dp.message(Command("help"))
async def handle_help(message: types.Message):
    """Handle /help command."""
    help_text = (
        "📋 Available commands:\n\n"
        "• /start - Start the bot and get welcome message\n"
        "• /help - Show this help message\n\n"
        "🤖 This is a basic bot example using aiogram-cmds.\n"
        "It demonstrates simple command management with auto-setup."
    )

    await message.answer(help_text)

    logger.info(f"User {message.from_user.id} requested help")


@dp.message(Command("info"))
async def handle_info(message: types.Message):
    """Handle /info command."""
    user = message.from_user

    info_text = (
        f"ℹ️ Bot Information:\n\n"
        f"• Bot Name: Basic Bot Example\n"
        f"• Version: aiogram-cmds demo\n"
        f"• Your ID: {user.id}\n"
        f"• Your Name: {user.first_name or 'Unknown'}\n"
        f"• Username: @{user.username or 'None'}\n"
        f"• Language: {user.language_code or 'Unknown'}\n\n"
        f"🔧 This bot uses aiogram-cmds for command management."
    )

    await message.answer(info_text)

    logger.info(f"User {user.id} requested bot info")


@dp.message(Command("ping"))
async def handle_ping(message: types.Message):
    """Handle /ping command."""
    await message.answer("🏓 Pong!")

    logger.info(f"User {message.from_user.id} pinged the bot")


@dp.message()
async def handle_other_messages(message: types.Message):
    """Handle all other messages."""
    user_name = message.from_user.first_name or "there"

    await message.answer(
        f"🤔 I don't understand that message, {user_name}.\n\n"
        f"Use /help to see available commands."
    )

    logger.info(f"User {message.from_user.id} sent unknown message: {message.text}")


async def main():
    """Main function."""
    # Check if bot token is set
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Please set BOT_TOKEN environment variable")
        logger.error("   export BOT_TOKEN='your_bot_token_here'")
        return

    # Set up startup and shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        # Start polling
        logger.info("🔄 Starting bot polling...")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
    finally:
        # Close bot session
        await bot.session.close()


if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
