# aiogram-cmds

**Command management library for aiogram v3** - Manage Telegram bot commands with i18n support, user profiles, and dynamic scopes.

## 🚀 Quick Start

Get started with aiogram-cmds in under 5 minutes:

```python
from aiogram import Bot, Dispatcher
from aiogram_cmds.auto_setup import setup_commands_auto

async def on_startup():
    # Automatically set up commands with sensible defaults
    command_manager = await setup_commands_auto(bot)
    # Commands are ready to use!
```

## ✨ Key Features

### 🎯 **Three Usage Modes**
- **Auto-Setup**: Zero configuration, works out of the box
- **Simple Mode**: Settings-based configuration with policies  
- **Advanced Mode**: Full control with profiles, scopes, and custom resolvers

### 🌍 **i18n Integration**
- Built-in support for aiogram i18n
- Automatic fallback handling
- Multi-language command descriptions

### 👥 **User Profiles**
- Dynamic command sets based on user status
- Guest, registered, admin, and custom profiles
- Runtime profile switching

### 🎛️ **Multiple Scopes**
- All Telegram command scopes supported
- Private chats, groups, admins, specific users
- Hierarchical scope management

### 🔧 **Production Ready**
- Type-safe with full type hints
- Comprehensive testing suite
- CI/CD pipeline
- Extensive documentation

## 📖 Documentation

### Getting Started
- **[Quickstart Guide](quickstart.md)** - Get up and running in 5 minutes
- **[Installation](installation.md)** - Installation instructions and requirements
- **[Configuration](configuration.md)** - Complete configuration guide

### Tutorials
- **[Basic Setup](tutorials/basic-setup.md)** - Your first command management setup
- **[i18n Integration](tutorials/i18n-integration.md)** - Adding multiple languages
- **[Advanced Profiles](tutorials/advanced-profiles.md)** - Complex user profiles
- **[Dynamic Commands](tutorials/dynamic-commands.md)** - Runtime command updates

### API Reference
- **[Core API](api/core.md)** - Manager, builder, and policy classes
- **[Configuration](api/configuration.md)** - Configuration models and options
- **[Translator](api/translator.md)** - Translation system and i18n integration

### Architecture & Performance
- **[Architecture](ARCHITECTURE.md)** - Technical overview and design decisions
- **[Performance](performance.md)** - Benchmarks and optimization tips
- **[Testing](TESTING.md)** - Testing guide and best practices

## 🎯 Common Use Cases

### E-commerce Bot
```python
profiles = {
    "visitor": ProfileDef(include=["start", "catalog", "help"]),
    "customer": ProfileDef(include=["start", "catalog", "cart", "orders", "help"]),
    "vip": ProfileDef(include=["start", "catalog", "cart", "orders", "vip_offers", "help"]),
}
```

### Admin Bot
```python
scopes = [
    ScopeDef(scope="all_private_chats", profile="user"),
    ScopeDef(scope="chat_member", chat_id=12345, user_id=67890, profile="admin"),
]
```

### Multi-Language Bot
```python
config = CmdsConfig(
    languages=["en", "ru", "es", "fr"],
    commands={
        "start": CommandDef(i18n_key="commands.start"),
        "help": CommandDef(i18n_key="commands.help"),
    }
)
```

## 🏗️ Architecture Overview

aiogram-cmds provides a layered architecture that scales from simple to complex:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Auto-Setup    │    │   Simple Mode    │    │  Advanced Mode  │
│                 │    │                  │    │                 │
│ setup_commands_ │    │ CmdsSettings +   │    │ CmdsConfig +    │
│ auto()          │    │ CommandPolicy    │    │ ProfileResolver │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌──────────────────┐
                    │ CommandScopeMgr  │
                    │                  │
                    │ • setup_all()    │
                    │ • update_user()  │
                    │ • clear_user()   │
                    └──────────────────┘
                                 │
                    ┌──────────────────┐
                    │   Telegram API   │
                    │                  │
                    │ • set_commands   │
                    │ • delete_commands│
                    │ • menu_button    │
                    └──────────────────┘
```

## 🚀 Installation

```bash
# Basic installation
pip install aiogram-cmds

# With Redis support (for multi-worker deployments)
pip install aiogram-cmds[redis]
```

## 🤝 Community

- 💬 **[Discussions](https://github.com/ArmanAvanesyan/aiogram-cmds/discussions)** - Questions, ideas, and community chat
- 🐛 **[Issues](https://github.com/ArmanAvanesyan/aiogram-cmds/issues)** - Bug reports and feature requests
- 📖 **[Documentation](https://aiogram-cmds.dev)** - Complete guides and API reference

## 📊 Project Status

- ✅ **Core Features**: Command management, i18n, profiles, scopes
- ✅ **Documentation**: Comprehensive guides and API reference  
- ✅ **Testing**: Unit, integration, and performance tests
- ✅ **CI/CD**: Automated testing and deployment
- 🚧 **Examples**: Working bot examples (in progress)
- 🔮 **Future**: Rate limiting, caching, advanced analytics

---

**Ready to get started?** Check out our [Quickstart Guide](quickstart.md) or browse the [Examples](../examples/)!
