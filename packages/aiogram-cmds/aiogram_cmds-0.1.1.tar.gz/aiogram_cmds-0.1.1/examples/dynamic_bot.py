#!/usr/bin/env python3
"""
Dynamic Bot Example

A bot demonstrating dynamic command management with aiogram-cmds.
This example shows how to add, remove, and update commands at runtime.

Features:
- Dynamic command addition/removal
- Real-time command updates
- Context-aware commands
- Temporary commands with expiration
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command

from aiogram_cmds.auto_setup import setup_commands_auto
from aiogram_cmds.customize import CmdsConfig, CommandDef, ProfileDef, ScopeDef
from aiogram_cmds.manager import CommandScopeManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Global manager instance
manager: CommandScopeManager = None

# Dynamic commands storage
dynamic_commands: dict[str, dict] = {}
temporary_commands: dict[str, datetime] = {}

# User sessions for context-aware commands
user_sessions: dict[int, dict] = {}


def create_dynamic_config() -> CmdsConfig:
    """Create a configuration that supports dynamic commands."""
    return CmdsConfig(
        languages=["en"],
        commands={
            "start": CommandDef(descriptions={"en": "Start the bot"}),
            "help": CommandDef(descriptions={"en": "Get help"}),
            "addcmd": CommandDef(descriptions={"en": "Add a dynamic command"}),
            "removecmd": CommandDef(descriptions={"en": "Remove a dynamic command"}),
            "listcmds": CommandDef(descriptions={"en": "List all commands"}),
            "tempcmd": CommandDef(descriptions={"en": "Add a temporary command"}),
            "session": CommandDef(descriptions={"en": "Start a session"}),
            "end": CommandDef(descriptions={"en": "End current session"}),
        },
        profiles={
            "user": ProfileDef(
                include=[
                    "start",
                    "help",
                    "addcmd",
                    "removecmd",
                    "listcmds",
                    "tempcmd",
                    "session",
                    "end",
                ]
            ),
        },
        scopes=[
            ScopeDef(scope="default", profile="user"),
            ScopeDef(scope="all_private_chats", profile="user"),
        ],
    )


async def update_user_commands(user_id: int, chat_id: int):
    """Update commands for a specific user."""
    if manager:
        await manager.update_user_commands(
            user_id=user_id,
            is_registered=True,
            has_vehicle=False,
            user_language="en",
            chat_id=chat_id,
        )


async def cleanup_expired_commands():
    """Remove expired temporary commands."""
    now = datetime.now()
    expired = [cmd for cmd, expiry in temporary_commands.items() if now > expiry]

    for cmd in expired:
        if cmd in dynamic_commands:
            del dynamic_commands[cmd]
        del temporary_commands[cmd]
        logger.info(f"Removed expired command: {cmd}")

    if expired:
        # Update all users' commands
        for user_id in user_sessions:
            await update_user_commands(user_id, user_id)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command."""
    user_id = message.from_user.id

    # Initialize user session
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "active": False,
            "context": None,
        }

    await message.answer(
        "🤖 Welcome to the Dynamic Bot!\n\n"
        "I can dynamically add, remove, and update commands at runtime.\n\n"
        "Try these commands:\n"
        "• /addcmd - Add a new command\n"
        "• /removecmd - Remove a command\n"
        "• /listcmds - List all commands\n"
        "• /tempcmd - Add a temporary command\n"
        "• /session - Start a context session\n"
        "• /help - Get detailed help"
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command."""
    help_text = (
        "🔧 Dynamic Bot Commands:\n\n"
        "**Core Commands:**\n"
        "• /start - Start the bot\n"
        "• /help - Show this help\n"
        "• /listcmds - List all available commands\n\n"
        "**Dynamic Commands:**\n"
        "• /addcmd <name> <response> - Add a new command\n"
        "• /removecmd <name> - Remove a command\n"
        "• /tempcmd <name> <response> <minutes> - Add temporary command\n\n"
        "**Session Commands:**\n"
        "• /session <context> - Start a context session\n"
        "• /end - End current session\n\n"
        "**Examples:**\n"
        '• /addcmd hello "Hello there!"\n'
        '• /tempcmd countdown "Time\'s up!" 5\n'
        "• /session math"
    )

    await message.answer(help_text)


@dp.message(Command("addcmd"))
async def cmd_addcmd(message: types.Message):
    """Handle /addcmd command."""
    user_id = message.from_user.id

    # Parse command arguments
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        await message.answer(
            "❌ Usage: /addcmd <name> <response>\n\n"
            'Example: /addcmd hello "Hello there!"'
        )
        return

    cmd_name = parts[1].lower()
    response = parts[2]

    # Validate command name
    if cmd_name in [
        "start",
        "help",
        "addcmd",
        "removecmd",
        "listcmds",
        "tempcmd",
        "session",
        "end",
    ]:
        await message.answer("❌ Cannot override built-in commands!")
        return

    # Add the dynamic command
    dynamic_commands[cmd_name] = {
        "response": response,
        "created_by": user_id,
        "created_at": datetime.now(),
    }

    # Update the configuration
    if manager and manager.config:
        manager.config.commands[cmd_name] = CommandDef(
            descriptions={"en": f"Dynamic command: {response[:50]}..."}
        )

        # Update user commands
        await update_user_commands(user_id, message.chat.id)

    await message.answer(f"✅ Command '/{cmd_name}' added successfully!")


@dp.message(Command("removecmd"))
async def cmd_removecmd(message: types.Message):
    """Handle /removecmd command."""
    user_id = message.from_user.id

    # Parse command arguments
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        await message.answer("❌ Usage: /removecmd <name>")
        return

    cmd_name = parts[1].lower()

    # Check if command exists
    if cmd_name not in dynamic_commands:
        await message.answer(f"❌ Command '/{cmd_name}' not found!")
        return

    # Remove the command
    del dynamic_commands[cmd_name]

    # Remove from temporary commands if it was temporary
    if cmd_name in temporary_commands:
        del temporary_commands[cmd_name]

    # Update the configuration
    if manager and manager.config and cmd_name in manager.config.commands:
        del manager.config.commands[cmd_name]

        # Update user commands
        await update_user_commands(user_id, message.chat.id)

    await message.answer(f"✅ Command '/{cmd_name}' removed successfully!")


@dp.message(Command("listcmds"))
async def cmd_listcmds(message: types.Message):
    """Handle /listcmds command."""
    if not dynamic_commands:
        await message.answer("📝 No dynamic commands found.")
        return

    commands_text = "📋 Dynamic Commands:\n\n"
    for cmd_name, cmd_data in dynamic_commands.items():
        created_at = cmd_data["created_at"].strftime("%H:%M:%S")
        is_temp = cmd_name in temporary_commands
        temp_info = (
            f" (expires {temporary_commands[cmd_name].strftime('%H:%M:%S')})"
            if is_temp
            else ""
        )
        commands_text += f"• /{cmd_name} - {cmd_data['response'][:30]}... (created {created_at}){temp_info}\n"

    await message.answer(commands_text)


@dp.message(Command("tempcmd"))
async def cmd_tempcmd(message: types.Message):
    """Handle /tempcmd command."""
    user_id = message.from_user.id

    # Parse command arguments
    parts = message.text.split(" ", 3)
    if len(parts) < 4:
        await message.answer(
            "❌ Usage: /tempcmd <name> <response> <minutes>\n\n"
            'Example: /tempcmd countdown "Time\'s up!" 5'
        )
        return

    cmd_name = parts[1].lower()
    response = parts[2]

    try:
        minutes = int(parts[3])
        if minutes <= 0 or minutes > 60:
            raise ValueError("Minutes must be between 1 and 60")
    except ValueError:
        await message.answer("❌ Minutes must be a number between 1 and 60")
        return

    # Validate command name
    if cmd_name in [
        "start",
        "help",
        "addcmd",
        "removecmd",
        "listcmds",
        "tempcmd",
        "session",
        "end",
    ]:
        await message.answer("❌ Cannot override built-in commands!")
        return

    # Add the temporary command
    expiry_time = datetime.now() + timedelta(minutes=minutes)
    dynamic_commands[cmd_name] = {
        "response": response,
        "created_by": user_id,
        "created_at": datetime.now(),
    }
    temporary_commands[cmd_name] = expiry_time

    # Update the configuration
    if manager and manager.config:
        manager.config.commands[cmd_name] = CommandDef(
            descriptions={"en": f"Temporary command: {response[:50]}..."}
        )

        # Update user commands
        await update_user_commands(user_id, message.chat.id)

    await message.answer(
        f"✅ Temporary command '/{cmd_name}' added!\n"
        f"⏰ Will expire in {minutes} minutes at {expiry_time.strftime('%H:%M:%S')}"
    )


@dp.message(Command("session"))
async def cmd_session(message: types.Message):
    """Handle /session command."""
    user_id = message.from_user.id

    # Parse command arguments
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        await message.answer("❌ Usage: /session <context>\n\nExample: /session math")
        return

    context = parts[1].lower()

    # Initialize user session if not exists
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "active": False,
            "context": None,
        }

    # Start session
    user_sessions[user_id]["active"] = True
    user_sessions[user_id]["context"] = context

    # Add context-specific commands
    context_commands = {
        "math": {
            "add": "2 + 2 = 4",
            "multiply": "3 × 4 = 12",
            "square": "5² = 25",
        },
        "weather": {
            "sunny": "☀️ It's sunny today!",
            "rainy": "🌧️ It's raining today!",
            "cloudy": "☁️ It's cloudy today!",
        },
        "games": {
            "dice": "🎲 You rolled a 4!",
            "coin": "🪙 Heads!",
            "random": "🎯 Your random number: 42",
        },
    }

    if context in context_commands:
        for cmd_name, response in context_commands[context].items():
            dynamic_commands[cmd_name] = {
                "response": response,
                "created_by": user_id,
                "created_at": datetime.now(),
                "context": context,
            }

    # Update commands
    if manager and manager.config:
        for cmd_name, cmd_data in context_commands.get(context, {}).items():
            manager.config.commands[cmd_name] = CommandDef(
                descriptions={"en": f"Context command: {cmd_data[:30]}..."}
            )

        await update_user_commands(user_id, message.chat.id)

    await message.answer(
        f"🎯 Session started: {context}\n"
        f"Context-specific commands are now available!\n"
        f"Use /end to finish the session."
    )


@dp.message(Command("end"))
async def cmd_end(message: types.Message):
    """Handle /end command."""
    user_id = message.from_user.id

    if user_id not in user_sessions or not user_sessions[user_id]["active"]:
        await message.answer("❌ No active session to end.")
        return

    context = user_sessions[user_id]["context"]

    # Remove context-specific commands
    commands_to_remove = []
    for cmd_name, cmd_data in dynamic_commands.items():
        if cmd_data.get("context") == context and cmd_data.get("created_by") == user_id:
            commands_to_remove.append(cmd_name)

    for cmd_name in commands_to_remove:
        del dynamic_commands[cmd_name]
        if cmd_name in temporary_commands:
            del temporary_commands[cmd_name]
        if manager and manager.config and cmd_name in manager.config.commands:
            del manager.config.commands[cmd_name]

    # End session
    user_sessions[user_id]["active"] = False
    user_sessions[user_id]["context"] = None

    # Update commands
    await update_user_commands(user_id, message.chat.id)

    await message.answer(f"✅ Session '{context}' ended. Context commands removed.")


# Handle dynamic commands
@dp.message(F.text.startswith("/"))
async def handle_dynamic_command(message: types.Message):
    """Handle dynamic commands."""
    # Skip if it's a built-in command (already handled)
    if message.text.split()[0][1:] in [
        "start",
        "help",
        "addcmd",
        "removecmd",
        "listcmds",
        "tempcmd",
        "session",
        "end",
    ]:
        return

    cmd_name = message.text.split()[0][1:].lower()

    if cmd_name in dynamic_commands:
        cmd_data = dynamic_commands[cmd_name]
        response = cmd_data["response"]

        # Add context information if in session
        user_id = message.from_user.id
        if user_id in user_sessions and user_sessions[user_id]["active"]:
            context = user_sessions[user_id]["context"]
            response = f"[{context}] {response}"

        await message.answer(response)


async def periodic_cleanup():
    """Periodically clean up expired commands."""
    while True:
        await asyncio.sleep(60)  # Check every minute
        await cleanup_expired_commands()


async def main():
    """Main function to run the bot."""
    global manager

    logger.info("Starting dynamic bot...")

    # Set up command management
    manager = await setup_commands_auto(
        bot=bot,
        config=create_dynamic_config(),
    )

    logger.info("Command management set up successfully!")

    # Start periodic cleanup task
    asyncio.create_task(periodic_cleanup())

    logger.info("Bot is ready to handle messages...")

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
