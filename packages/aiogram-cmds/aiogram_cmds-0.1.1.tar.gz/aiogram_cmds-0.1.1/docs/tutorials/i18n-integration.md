# i18n Integration Tutorial

This tutorial shows how to integrate aiogram-cmds with aiogram's i18n using `I18n` and `SimpleI18nMiddleware`.

## 🎯 What We'll Build

A multi-language bot with:
- Support for English, Russian, and Spanish
- Localized command descriptions
- Dynamic language switching
- Proper fallback handling

## 📋 Prerequisites

- Completed [Basic Setup Tutorial](basic-setup.md)
- aiogram i18n system knowledge
- Basic understanding of translation files

## 🚀 Step 1: Install Dependencies

```bash
pip install aiogram-cmds
```

## 🚀 Step 2: Set Up Translation Files

Create the following directory structure:

```
locales/
├── en/
│   └── LC_MESSAGES/
│       └── messages.po
├── ru/
│   └── LC_MESSAGES/
│       └── messages.po
└── es/
    └── LC_MESSAGES/
        └── messages.po
```

### English translations (`locales/en/LC_MESSAGES/messages.po`)

```po
msgid "cmd.start.desc"
msgstr "Start the bot"

msgid "cmd.help.desc"
msgstr "Show help information"

msgid "cmd.about.desc"
msgstr "About this bot"

msgid "cmd.settings.desc"
msgstr "Bot settings"

msgid "cmd.language.desc"
msgstr "Change language"

msgid "welcome.message"
msgstr "👋 Welcome to my bot! Use /help to see available commands."

msgid "help.message"
msgstr "📋 Available commands:\n\n/start - Start the bot\n/help - Show this help message\n/about - About this bot\n/settings - Bot settings\n/language - Change language"

msgid "about.message"
msgstr "ℹ️ About this bot:\n\nThis is a multi-language bot built with aiogram-cmds."

msgid "settings.message"
msgstr "⚙️ Bot settings:\n\n/language - Change language"

msgid "language.message"
msgstr "🌍 Choose your language:"

msgid "language.changed"
msgstr "✅ Language changed to {language}"

msgid "unknown.message"
msgstr "🤔 I don't understand that message. Use /help to see available commands."
```

### Russian translations (`locales/ru/LC_MESSAGES/messages.po`)

```po
msgid "cmd.start.desc"
msgstr "Запустить бота"

msgid "cmd.help.desc"
msgstr "Показать справку"

msgid "cmd.about.desc"
msgstr "О боте"

msgid "cmd.settings.desc"
msgstr "Настройки бота"

msgid "cmd.language.desc"
msgstr "Изменить язык"

msgid "welcome.message"
msgstr "👋 Добро пожаловать в моего бота! Используйте /help для просмотра доступных команд."

msgid "help.message"
msgstr "📋 Доступные команды:\n\n/start - Запустить бота\n/help - Показать эту справку\n/about - О боте\n/settings - Настройки бота\n/language - Изменить язык"

msgid "about.message"
msgstr "ℹ️ О боте:\n\nЭто многоязычный бот, созданный с помощью aiogram-cmds."

msgid "settings.message"
msgstr "⚙️ Настройки бота:\n\n/language - Изменить язык"

msgid "language.message"
msgstr "🌍 Выберите ваш язык:"

msgid "language.changed"
msgstr "✅ Язык изменен на {language}"

msgid "unknown.message"
msgstr "🤔 Я не понимаю это сообщение. Используйте /help для просмотра доступных команд."
```

### Spanish translations (`locales/es/LC_MESSAGES/messages.po`)

```po
msgid "cmd.start.desc"
msgstr "Iniciar el bot"

msgid "cmd.help.desc"
msgstr "Mostrar ayuda"

msgid "cmd.about.desc"
msgstr "Acerca del bot"

msgid "cmd.settings.desc"
msgstr "Configuración del bot"

msgid "cmd.language.desc"
msgstr "Cambiar idioma"

msgid "welcome.message"
msgstr "👋 ¡Bienvenido a mi bot! Usa /help para ver los comandos disponibles."

msgid "help.message"
msgstr "📋 Comandos disponibles:\n\n/start - Iniciar el bot\n/help - Mostrar esta ayuda\n/about - Acerca del bot\n/settings - Configuración del bot\n/language - Cambiar idioma"

msgid "about.message"
msgstr "ℹ️ Acerca del bot:\n\nEste es un bot multilingüe construido con aiogram-cmds."

msgid "settings.message"
msgstr "⚙️ Configuración del bot:\n\n/language - Cambiar idioma"

msgid "language.message"
msgstr "🌍 Elige tu idioma:"

msgid "language.changed"
msgstr "✅ Idioma cambiado a {language}"

msgid "unknown.message"
msgstr "🤔 No entiendo ese mensaje. Usa /help para ver los comandos disponibles."
```

## 🚀 Step 3: Compile Translation Files

```bash
# Install gettext tools
# Ubuntu/Debian: sudo apt-get install gettext
# macOS: brew install gettext
# Windows: Download from https://mlocati.github.io/articles/gettext-iconv-windows.html

# Compile translations
cd locales
for lang in en ru es; do
    msgfmt $lang/LC_MESSAGES/messages.po -o $lang/LC_MESSAGES/messages.mo
done
```

## 🚀 Step 4: Create the Bot

Create `bot.py`:

```python
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware, gettext as _
from aiogram_cmds import CommandScopeManager, CmdsConfig, CommandDef, ProfileDef, ScopeDef
from aiogram_cmds import build_translator_from_i18n

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Create bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Set up i18n
i18n = I18n(path="locales", default_locale="en", domain="messages")
dp.message.middleware(SimpleI18nMiddleware(i18n))

# Create translator for aiogram-cmds
translator = build_translator_from_i18n(i18n)

async def on_startup():
    """Set up commands with i18n support."""
    
    config = CmdsConfig(
        languages=["en", "ru", "es"],
        fallback_language="en",
        i18n_key_prefix="cmd",
        commands={
            "start": CommandDef(i18n_key="start.desc"),
            "help": CommandDef(i18n_key="help.desc"),
            "about": CommandDef(i18n_key="about.desc"),
            "settings": CommandDef(i18n_key="settings.desc"),
            "language": CommandDef(i18n_key="language.desc"),
        },
        profiles={
            "default": ProfileDef(include=["start", "help", "about", "settings", "language"]),
        },
        scopes=[
            ScopeDef(scope="all_private_chats", profile="default"),
        ],
    )
    
    manager = CommandScopeManager(
        bot, 
        config=config, 
        translator=translator
    )
    await manager.setup_all()
    
    logger.info("✅ Bot started with i18n support!")

# Message handlers
@dp.message(Command("start"))
async def handle_start(message: types.Message):
    await message.answer(_("welcome.message"))

@dp.message(Command("help"))
async def handle_help(message: types.Message):
    await message.answer(_("help.message"))

@dp.message(Command("about"))
async def handle_about(message: types.Message):
    await message.answer(_("about.message"))

@dp.message(Command("settings"))
async def handle_settings(message: types.Message):
    await message.answer(_("settings.message"))

@dp.message(Command("language"))
async def handle_language(message: types.Message):
    # Create language selection keyboard
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en"),
            types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        ],
        [
            types.InlineKeyboardButton(text="🇪🇸 Español", callback_data="lang_es"),
        ]
    ])
    
    await message.answer(_("language.message"), reply_markup=keyboard)

@dp.callback_query(F.data.startswith("lang_"))
async def handle_language_change(callback: types.CallbackQuery):
    """Handle language change."""
    lang_code = callback.data.split("_")[1]
    
    # Update user's language
    await i18n.set_locale(callback.from_user.id, lang_code)
    
    # Get language name
    lang_names = {
        "en": "English",
        "ru": "Русский", 
        "es": "Español"
    }
    
    await callback.message.edit_text(
        _("language.changed", language=lang_names[lang_code])
    )
    
    # Update user's commands with new language
    manager = CommandScopeManager(bot, translator=translator)
    await manager.update_user_commands(
        user_id=callback.from_user.id,
        is_registered=True,
        has_vehicle=False,
        user_language=lang_code
    )

@dp.message()
async def handle_other_messages(message: types.Message):
    await message.answer(_("unknown.message"))

async def main():
    dp.startup.register(on_startup)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🚀 Step 5: Test Your Bot

1. **Start your bot**: `python bot.py`
2. **Test different languages**:
   - Send `/start` - Should show welcome in English
   - Send `/language` - Should show language selection
   - Select Russian - Commands should update to Russian
   - Send `/help` - Should show help in Russian

## 🔧 Step 6: Advanced i18n Features

### Custom Translator with Fallbacks

```python
class CustomTranslator:
    def __init__(self, i18n: I18n):
        self.i18n = i18n
        self.fallbacks = {
            "en": {
                "cmd.start.desc": "Start the bot",
                "cmd.help.desc": "Show help",
            },
            "ru": {
                "cmd.start.desc": "Запустить бота",
                "cmd.help.desc": "Показать справку",
            }
        }
    
    def __call__(self, key: str, *, locale: str) -> str:
        # Try aiogram i18n first
        try:
            translation = self.i18n.gettext(key, locale=locale)
            if translation and translation != key:
                return translation
        except Exception:
            pass
        
        # Fallback to hardcoded translations
        return self.fallbacks.get(locale, {}).get(key)

# Usage
custom_translator = CustomTranslator(i18n)
manager = CommandScopeManager(bot, translator=custom_translator)
```

### Dynamic Language Detection

```python
@dp.message(Command("start"))
async def handle_start(message: types.Message):
    # Detect user's language from Telegram
    user_lang = message.from_user.language_code or "en"
    
    # Set user's language
    await i18n.set_locale(message.from_user.id, user_lang)
    
    # Update commands with detected language
    manager = CommandScopeManager(bot, translator=translator)
    await manager.update_user_commands(
        user_id=message.from_user.id,
        is_registered=True,
        has_vehicle=False,
        user_language=user_lang
    )
    
    await message.answer(_("welcome.message"))
```

### Context-Aware Translations

```python
# In your translation files, add context
msgid "cmd.start.desc"
msgstr "Start the bot"

msgid "cmd.start.desc@admin"
msgstr "Start the bot (Admin)"

# In your code
def context_translator(key: str, *, locale: str, context: str = None) -> str:
    if context:
        context_key = f"{key}@{context}"
        translation = i18n.gettext(context_key, locale=locale)
        if translation and translation != context_key:
            return translation
    
    return i18n.gettext(key, locale=locale)

# Usage with context
admin_commands = {
    "start": CommandDef(i18n_key="start.desc"),  # Will use "start.desc@admin" for admins
}
```

## 🚨 Common Issues

### Translation Files Not Found
```bash
# Make sure files are compiled
msgfmt locales/en/LC_MESSAGES/messages.po -o locales/en/LC_MESSAGES/messages.mo

# Check file permissions
chmod 644 locales/*/LC_MESSAGES/messages.mo
```

### Commands Not Updating Language
```python
# Make sure to update user commands after language change
await manager.update_user_commands(
    user_id=user_id,
    is_registered=True,
    has_vehicle=False,
    user_language=new_language
)
```

### Missing Translations
```python
# Add fallback handling
def safe_translator(key: str, *, locale: str) -> str:
    translation = i18n.gettext(key, locale=locale)
    if translation and translation != key:
        return translation
    
    # Fallback to English
    if locale != "en":
        translation = i18n.gettext(key, locale="en")
        if translation and translation != key:
            return translation
    
    # Final fallback
    return key.replace("cmd.", "").replace(".desc", "").title()
```

## 🎉 Next Steps

Congratulations! You've successfully integrated i18n with aiogram-cmds. Here's what you can do next:

1. **[Advanced Profiles Tutorial](advanced-profiles.md)** - Create user-specific commands
2. **[Dynamic Commands Tutorial](dynamic-commands.md)** - Update commands at runtime
3. **[Examples](../examples/)** - See complete multi-language bots
4. **[API Reference](../api/translator.md)** - Explore advanced translator features

## 💡 Tips

- Use consistent translation key patterns
- Provide fallback translations for missing keys
- Test all languages thoroughly
- Use context-aware translations for different user types
- Compile translation files after changes
- Consider using translation management tools for large projects

---

**Ready for more?** Check out the [Advanced Profiles Tutorial](advanced-profiles.md) to create user-specific command sets!
