#!/usr/bin/env python3
"""
i18n Bot Example

A multi-language bot with i18n integration using aiogram-cmds.
This example demonstrates how to create a bot that supports multiple languages.

Features:
- Multiple languages (English, Russian, Spanish)
- aiogram i18n integration
- Dynamic language switching
- Localized command descriptions
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware
from aiogram.utils.i18n import gettext as _

from aiogram_cmds import (
    CmdsConfig,
    CommandDef,
    CommandScopeManager,
    ProfileDef,
    ScopeDef,
    build_translator_from_i18n,
)

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

# Set up i18n
i18n = I18n(path="examples/locales", default_locale="en", domain="messages")
dp.message.middleware(SimpleI18nMiddleware(i18n))

# Create translator for aiogram-cmds
translator = build_translator_from_i18n(i18n)


async def on_startup():
    """Set up commands with i18n support."""
    logger.info("🚀 Starting i18n bot...")

    # Define configuration with multiple languages
    config = CmdsConfig(
        languages=["en", "ru", "es"],
        fallback_language="en",
        i18n_key_prefix="cmd",
        commands={
            "start": CommandDef(i18n_key="start.desc"),
            "help": CommandDef(i18n_key="help.desc"),
            "about": CommandDef(i18n_key="about.desc"),
            "language": CommandDef(i18n_key="language.desc"),
            "info": CommandDef(i18n_key="info.desc"),
        },
        profiles={
            "default": ProfileDef(
                include=["start", "help", "about", "language", "info"]
            ),
        },
        scopes=[
            ScopeDef(scope="all_private_chats", profile="default"),
        ],
    )

    # Create manager with i18n support
    manager = CommandScopeManager(bot, config=config, translator=translator)

    # Set up all command scopes
    await manager.setup_all()

    logger.info("✅ i18n bot started with multi-language support!")
    logger.info("🌍 Supported languages: English, Russian, Spanish")


# Message handlers
@dp.message(Command("start"))
async def handle_start(message: types.Message):
    """Handle /start command."""
    user_name = message.from_user.first_name or _("user")

    await message.answer(_("welcome.message", name=user_name))

    logger.info(f"User {message.from_user.id} started the bot")


@dp.message(Command("help"))
async def handle_help(message: types.Message):
    """Handle /help command."""
    await message.answer(_("help.message"))

    logger.info(f"User {message.from_user.id} requested help")


@dp.message(Command("about"))
async def handle_about(message: types.Message):
    """Handle /about command."""
    await message.answer(_("about.message"))

    logger.info(f"User {message.from_user.id} requested about")


@dp.message(Command("language"))
async def handle_language(message: types.Message):
    """Handle /language command."""
    # Create language selection keyboard
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en"),
                types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            ],
            [
                types.InlineKeyboardButton(text="🇪🇸 Español", callback_data="lang_es"),
            ],
        ]
    )

    await message.answer(_("language.message"), reply_markup=keyboard)

    logger.info(f"User {message.from_user.id} requested language selection")


@dp.message(Command("info"))
async def handle_info(message: types.Message):
    """Handle /info command."""
    user = message.from_user

    await message.answer(
        _(
            "info.message",
            user_id=user.id,
            first_name=user.first_name or _("unknown"),
            username=user.username or _("none"),
            language=user.language_code or _("unknown"),
        )
    )

    logger.info(f"User {user.id} requested info")


@dp.callback_query(F.data.startswith("lang_"))
async def handle_language_change(callback: types.CallbackQuery):
    """Handle language change."""
    lang_code = callback.data.split("_")[1]

    # Update user's language
    await i18n.set_locale(callback.from_user.id, lang_code)

    # Get language name
    lang_names = {"en": "English", "ru": "Русский", "es": "Español"}

    await callback.message.edit_text(
        _("language.changed", language=lang_names[lang_code])
    )

    # Update user's commands with new language
    manager = CommandScopeManager(bot, translator=translator)
    await manager.update_user_commands(
        user_id=callback.from_user.id,
        is_registered=True,
        has_vehicle=False,
        user_language=lang_code,
    )

    logger.info(f"User {callback.from_user.id} changed language to {lang_code}")


@dp.message()
async def handle_other_messages(message: types.Message):
    """Handle all other messages."""
    await message.answer(_("unknown.message"))

    logger.info(f"User {message.from_user.id} sent unknown message: {message.text}")


async def main():
    """Main function."""
    # Check if bot token is set
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Please set BOT_TOKEN environment variable")
        logger.error("   export BOT_TOKEN='your_bot_token_here'")
        return

    # Set up startup handler
    dp.startup.register(on_startup)

    try:
        # Start polling
        logger.info("🔄 Starting i18n bot polling...")
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
