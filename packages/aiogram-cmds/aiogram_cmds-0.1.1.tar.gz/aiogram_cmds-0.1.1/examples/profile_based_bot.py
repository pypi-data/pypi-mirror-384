#!/usr/bin/env python3
"""
Profile-Based Bot Example

A bot demonstrating advanced profile-based command management with aiogram-cmds.
This example shows how to create different command sets for different user types.

Features:
- Multiple user profiles (guest, user, admin)
- Profile-based command visibility
- Dynamic profile switching
- Custom profile resolver
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from aiogram_cmds.auto_setup import setup_commands_auto
from aiogram_cmds.customize import CmdsConfig, CommandDef, ProfileDef, ScopeDef
from aiogram_cmds.manager import CommandScopeManager
from aiogram_cmds.policy import Flags, ProfileResolver

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

# User database simulation (in real app, use proper database)
user_db = {
    # user_id: {"is_registered": bool, "is_admin": bool, "has_vehicle": bool}
}


def create_profile_resolver() -> ProfileResolver:
    """Create a custom profile resolver based on user data."""

    def resolve_profile(flags: Flags) -> str:
        user_id = getattr(flags, "user_id", None)

        if not user_id or user_id not in user_db:
            return "guest"

        user_data = user_db[user_id]

        if user_data.get("is_admin", False):
            return "admin"
        elif user_data.get("is_registered", False):
            return "user"
        else:
            return "guest"

    return resolve_profile


def create_custom_config() -> CmdsConfig:
    """Create a custom configuration with multiple profiles."""
    return CmdsConfig(
        languages=["en"],
        commands={
            "start": CommandDef(descriptions={"en": "Start the bot"}),
            "help": CommandDef(descriptions={"en": "Get help"}),
            "profile": CommandDef(descriptions={"en": "View your profile"}),
            "register": CommandDef(descriptions={"en": "Register your account"}),
            "vehicle": CommandDef(descriptions={"en": "Manage your vehicle"}),
            "admin": CommandDef(descriptions={"en": "Admin panel"}),
            "users": CommandDef(descriptions={"en": "List all users"}),
            "stats": CommandDef(descriptions={"en": "View statistics"}),
        },
        profiles={
            "guest": ProfileDef(include=["start", "help", "register"]),
            "user": ProfileDef(include=["start", "help", "profile", "vehicle"]),
            "admin": ProfileDef(
                include=[
                    "start",
                    "help",
                    "profile",
                    "vehicle",
                    "admin",
                    "users",
                    "stats",
                ]
            ),
        },
        scopes=[
            ScopeDef(scope="default", profile="guest"),
            ScopeDef(scope="all_private_chats", profile="user"),
        ],
    )


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command."""
    user_id = message.from_user.id

    # Initialize user in database if not exists
    if user_id not in user_db:
        user_db[user_id] = {
            "is_registered": False,
            "is_admin": False,
            "has_vehicle": False,
        }

    user_data = user_db[user_id]

    if user_data["is_registered"]:
        if user_data["is_admin"]:
            await message.answer("👋 Welcome back, Admin!")
        else:
            await message.answer("👋 Welcome back!")
    else:
        await message.answer(
            "👋 Welcome! I'm a profile-based bot.\n\n"
            "Available commands:\n"
            "• /register - Register your account\n"
            "• /help - Get help\n\n"
            "Register to unlock more features!"
        )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command."""
    user_id = message.from_user.id
    user_data = user_db.get(user_id, {})

    if user_data.get("is_admin", False):
        help_text = (
            "🔧 Admin Commands:\n"
            "• /start - Start the bot\n"
            "• /help - Show this help\n"
            "• /profile - View your profile\n"
            "• /vehicle - Manage your vehicle\n"
            "• /admin - Admin panel\n"
            "• /users - List all users\n"
            "• /stats - View statistics"
        )
    elif user_data.get("is_registered", False):
        help_text = (
            "👤 User Commands:\n"
            "• /start - Start the bot\n"
            "• /help - Show this help\n"
            "• /profile - View your profile\n"
            "• /vehicle - Manage your vehicle"
        )
    else:
        help_text = (
            "👋 Guest Commands:\n"
            "• /start - Start the bot\n"
            "• /help - Show this help\n"
            "• /register - Register your account"
        )

    await message.answer(help_text)


@dp.message(Command("register"))
async def cmd_register(message: types.Message):
    """Handle /register command."""
    user_id = message.from_user.id

    if user_id not in user_db:
        user_db[user_id] = {
            "is_registered": False,
            "is_admin": False,
            "has_vehicle": False,
        }

    user_data = user_db[user_id]

    if user_data["is_registered"]:
        await message.answer("✅ You're already registered!")
        return

    # Simulate registration process
    user_data["is_registered"] = True

    # Make first user an admin (for demo purposes)
    if len(user_db) == 1:
        user_data["is_admin"] = True
        await message.answer(
            "🎉 Registration successful! You're now the admin.\n\n"
            "Your commands have been updated. Try /help to see new options!"
        )
    else:
        await message.answer(
            "🎉 Registration successful!\n\n"
            "Your commands have been updated. Try /help to see new options!"
        )

    # Update user commands with new profile
    from aiogram_cmds.manager import CommandScopeManager

    # Get the manager instance (in real app, store this globally)
    manager = CommandScopeManager(
        bot=bot,
        config=create_custom_config(),
        profile_resolver=create_profile_resolver(),
    )

    await manager.update_user_commands(
        user_id=user_id,
        is_registered=user_data["is_registered"],
        has_vehicle=user_data["has_vehicle"],
        user_language="en",
        chat_id=message.chat.id,
    )


@dp.message(Command("profile"))
async def cmd_profile(message: types.Message):
    """Handle /profile command."""
    user_id = message.from_user.id
    user_data = user_db.get(user_id, {})

    if not user_data.get("is_registered", False):
        await message.answer("❌ You need to register first! Use /register")
        return

    profile_type = "admin" if user_data.get("is_admin", False) else "user"

    profile_text = (
        f"👤 Your Profile:\n"
        f"• ID: {user_id}\n"
        f"• Type: {profile_type}\n"
        f"• Registered: ✅\n"
        f"• Has Vehicle: {'✅' if user_data.get('has_vehicle', False) else '❌'}\n"
        f"• Admin: {'✅' if user_data.get('is_admin', False) else '❌'}"
    )

    await message.answer(profile_text)


@dp.message(Command("vehicle"))
async def cmd_vehicle(message: types.Message):
    """Handle /vehicle command."""
    user_id = message.from_user.id
    user_data = user_db.get(user_id, {})

    if not user_data.get("is_registered", False):
        await message.answer("❌ You need to register first! Use /register")
        return

    if user_data.get("has_vehicle", False):
        await message.answer("🚗 You already have a vehicle registered!")
    else:
        user_data["has_vehicle"] = True
        await message.answer("🚗 Vehicle registered successfully!")

        # Update commands to reflect new vehicle status
        manager = CommandScopeManager(
            bot=bot,
            config=create_custom_config(),
            profile_resolver=create_profile_resolver(),
        )

        await manager.update_user_commands(
            user_id=user_id,
            is_registered=user_data["is_registered"],
            has_vehicle=user_data["has_vehicle"],
            user_language="en",
            chat_id=message.chat.id,
        )


@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Handle /admin command (admin only)."""
    user_id = message.from_user.id
    user_data = user_db.get(user_id, {})

    if not user_data.get("is_admin", False):
        await message.answer("❌ Access denied. Admin privileges required.")
        return

    admin_text = (
        "🔧 Admin Panel:\n"
        f"• Total users: {len(user_db)}\n"
        f"• Registered users: {sum(1 for u in user_db.values() if u.get('is_registered', False))}\n"
        f"• Users with vehicles: {sum(1 for u in user_db.values() if u.get('has_vehicle', False))}\n"
        f"• Admins: {sum(1 for u in user_db.values() if u.get('is_admin', False))}"
    )

    await message.answer(admin_text)


@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    """Handle /users command (admin only)."""
    user_id = message.from_user.id
    user_data = user_db.get(user_id, {})

    if not user_data.get("is_admin", False):
        await message.answer("❌ Access denied. Admin privileges required.")
        return

    if not user_db:
        await message.answer("📝 No users found.")
        return

    users_text = "👥 Users:\n"
    for uid, data in user_db.items():
        status = (
            "admin"
            if data.get("is_admin", False)
            else ("user" if data.get("is_registered", False) else "guest")
        )
        vehicle = "🚗" if data.get("has_vehicle", False) else "🚶"
        users_text += f"• {uid}: {status} {vehicle}\n"

    await message.answer(users_text)


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Handle /stats command (admin only)."""
    user_id = message.from_user.id
    user_data = user_db.get(user_id, {})

    if not user_data.get("is_admin", False):
        await message.answer("❌ Access denied. Admin privileges required.")
        return

    stats_text = (
        "📊 Statistics:\n"
        f"• Total users: {len(user_db)}\n"
        f"• Registered: {sum(1 for u in user_db.values() if u.get('is_registered', False))}\n"
        f"• With vehicles: {sum(1 for u in user_db.values() if u.get('has_vehicle', False))}\n"
        f"• Admins: {sum(1 for u in user_db.values() if u.get('is_admin', False))}\n"
        f"• Guests: {sum(1 for u in user_db.values() if not u.get('is_registered', False))}"
    )

    await message.answer(stats_text)


async def main():
    """Main function to run the bot."""
    logger.info("Starting profile-based bot...")

    # Set up command management with custom configuration
    await setup_commands_auto(
        bot=bot,
        config=create_custom_config(),
        profile_resolver=create_profile_resolver(),
    )

    logger.info("Command management set up successfully!")
    logger.info("Bot is ready to handle messages...")

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
