# Examples

This directory contains working example bots that demonstrate various features of aiogram-cmds.

## 📋 Available Examples

### 1. Basic Bot (`basic_bot.py`)
A simple bot demonstrating basic command management with auto-setup.

**Features:**
- Auto-setup with default commands
- Basic message handlers
- Simple user interaction

**Run:**
```bash
python examples/basic_bot.py
```

### 2. i18n Bot (`i18n_bot.py`)
A multi-language bot with i18n integration.

**Features:**
- Multiple languages (English, Russian, Spanish)
- aiogram i18n integration
- Dynamic language switching
- Localized command descriptions

**Run:**
```bash
python examples/i18n_bot.py
```

### 3. Profile-Based Bot (`profile_based_bot.py`)
An advanced bot with user profiles and dynamic command sets.

**Features:**
- Multiple user profiles (guest, user, premium, admin)
- Dynamic command updates
- Profile-based access control
- User registration system

**Run:**
```bash
python examples/profile_based_bot.py
```

### 4. Dynamic Bot (`dynamic_bot.py`)
A bot that updates commands dynamically based on user actions.

**Features:**
- Event-driven command updates
- Real-time command changes
- User state management
- Scheduled updates

**Run:**
```bash
python examples/dynamic_bot.py
```

### 5. E-commerce Bot (`ecommerce_bot.py`)
A complete e-commerce bot with product management and user tiers.

**Features:**
- Product catalog
- Shopping cart
- User tiers (visitor, customer, VIP)
- Order management
- Premium features

**Run:**
```bash
python examples/ecommerce_bot.py
```

### 6. Admin Bot (`admin_bot.py`)
An admin bot with user management and moderation features.

**Features:**
- User management
- Ban/unban functionality
- Admin commands
- Chat moderation
- Statistics and analytics

**Run:**
```bash
python examples/admin_bot.py
```

## 🚀 Getting Started

### Prerequisites

1. **Install aiogram-cmds:**
   ```bash
   pip install aiogram-cmds
   ```

2. **Get a bot token:**
   - Create a bot with [@BotFather](https://t.me/botfather)
   - Get your bot token

3. **Set up environment:**
   ```bash
   export BOT_TOKEN="your_bot_token_here"
   ```

### Running Examples

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ArmanAvanesyan/aiogram-cmds.git
   cd aiogram-cmds
   ```

2. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Run an example:**
   ```bash
   python examples/basic_bot.py
   ```

### Configuration

Each example can be configured by:

1. **Environment variables:**
   ```bash
   export BOT_TOKEN="your_bot_token"
   export BOT_LANGUAGES="en,ru,es"
   export BOT_FALLBACK_LANGUAGE="en"
   ```

2. **Configuration files:**
   - Create `pyproject.toml` in the examples directory
   - Add configuration under `[tool.aiogram_cmds]`

3. **Code modification:**
   - Edit the example files directly
   - Modify configuration objects

## 📁 Example Structure

```
examples/
├── README.md                 # This file
├── basic_bot.py             # Basic bot example
├── i18n_bot.py              # i18n bot example
├── profile_based_bot.py      # Profile-based bot example
├── dynamic_bot.py           # Dynamic bot example
├── ecommerce_bot.py         # E-commerce bot example
├── admin_bot.py             # Admin bot example
├── locales/                 # Translation files
│   ├── en/
│   │   └── LC_MESSAGES/
│   │       └── messages.po
│   ├── ru/
│   │   └── LC_MESSAGES/
│   │       └── messages.po
│   └── es/
│       └── LC_MESSAGES/
│           └── messages.po
├── data/                    # Example data files
│   ├── products.json
│   ├── users.json
│   └── config.json
└── utils/                   # Utility functions
    ├── database.py
    ├── helpers.py
    └── validators.py
```

## 🎯 Learning Path

### Beginner
1. Start with `basic_bot.py` to understand the basics
2. Move to `i18n_bot.py` to learn about translations
3. Try `profile_based_bot.py` for user management

### Intermediate
1. Study `dynamic_bot.py` for real-time updates
2. Explore `ecommerce_bot.py` for complex business logic
3. Examine `admin_bot.py` for moderation features

### Advanced
1. Combine features from multiple examples
2. Add your own custom logic
3. Implement production-ready features

## 🔧 Customization

### Adding New Commands

```python
# In any example, add new commands to the configuration
config = CmdsConfig(
    commands={
        "start": CommandDef(i18n_key="start.desc"),
        "help": CommandDef(i18n_key="help.desc"),
        "new_command": CommandDef(i18n_key="new_command.desc"),  # Add this
    },
    profiles={
        "user": ProfileDef(include=["start", "help", "new_command"]),  # Add to profile
    },
)

# Add the handler
@dp.message(Command("new_command"))
async def handle_new_command(message: Message):
    await message.answer("New command executed!")
```

### Adding New Languages

1. **Create translation files:**
   ```bash
   mkdir -p examples/locales/fr/LC_MESSAGES
   ```

2. **Add translations:**
   ```po
   # examples/locales/fr/LC_MESSAGES/messages.po
   msgid "cmd.start.desc"
   msgstr "Démarrer le bot"
   
   msgid "cmd.help.desc"
   msgstr "Afficher l'aide"
   ```

3. **Compile translations:**
   ```bash
   msgfmt examples/locales/fr/LC_MESSAGES/messages.po -o examples/locales/fr/LC_MESSAGES/messages.mo
   ```

4. **Update configuration:**
   ```python
   config = CmdsConfig(
       languages=["en", "ru", "es", "fr"],  # Add French
       # ... rest of configuration
   )
   ```

### Adding New Profiles

```python
# Add new profile to configuration
profiles = {
    "guest": ProfileDef(include=["start", "help"]),
    "user": ProfileDef(include=["start", "help", "profile"]),
    "premium": ProfileDef(include=["start", "help", "profile", "premium"]),
    "moderator": ProfileDef(include=["start", "help", "profile", "moderate"]),  # Add this
}

# Update profile resolver
def profile_resolver(flags: Flags) -> str:
    if flags.is_moderator:  # Add this condition
        return "moderator"
    elif flags.is_premium:
        return "premium"
    elif flags.is_registered:
        return "user"
    return "guest"
```

## 🚨 Troubleshooting

### Common Issues

1. **Bot not responding:**
   - Check your bot token
   - Make sure the bot is running
   - Check logs for errors

2. **Commands not appearing:**
   - Make sure `setup_all()` is called
   - Check command names are valid
   - Verify configuration is correct

3. **Translations not working:**
   - Check translation files exist
   - Make sure files are compiled
   - Verify i18n configuration

4. **Profile resolver not working:**
   - Check profile names are valid
   - Verify profiles are defined
   - Test resolver function

### Debug Mode

Enable debug logging in any example:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Getting Help

- Check the [Troubleshooting Guide](../docs/troubleshooting.md)
- Review the [FAQ](../docs/faq.md)
- Ask questions in [GitHub Discussions](https://github.com/ArmanAvanesyan/aiogram-cmds/discussions)

## 🤝 Contributing

### Adding New Examples

1. **Create a new file:**
   ```bash
   touch examples/my_bot.py
   ```

2. **Follow the structure:**
   ```python
   import asyncio
   import logging
   from aiogram import Bot, Dispatcher
   from aiogram_cmds import CommandScopeManager
   
   # Configuration
   BOT_TOKEN = "YOUR_BOT_TOKEN"
   
   # Bot setup
   bot = Bot(token=BOT_TOKEN)
   dp = Dispatcher()
   
   async def on_startup():
       # Your setup code here
       pass
   
   # Message handlers
   @dp.message(Command("start"))
   async def handle_start(message: Message):
       await message.answer("Hello!")
   
   async def main():
       dp.startup.register(on_startup)
       await dp.start_polling(bot)
   
   if __name__ == "__main__":
       asyncio.run(main())
   ```

3. **Add to README:**
   - Update this file with your new example
   - Add description and features
   - Include run instructions

4. **Submit a pull request:**
   - Fork the repository
   - Create a feature branch
   - Submit a pull request

### Example Guidelines

- **Keep it simple:** Focus on one main feature
- **Add comments:** Explain complex logic
- **Include error handling:** Show best practices
- **Use realistic data:** Make examples practical
- **Test thoroughly:** Ensure examples work

---

**Ready to explore?** Start with the [Basic Bot](basic_bot.py) and work your way up!
