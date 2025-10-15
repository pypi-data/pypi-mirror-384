# Architecture

This document provides a technical overview of aiogram-cmds architecture, design decisions, and internal structure.

## 🏗️ High-Level Architecture

aiogram-cmds follows a layered architecture that provides three levels of complexity:

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
├─────────────────┬───────────────────┬───────────────────────────┤
│   Auto-Setup    │   Simple Mode     │      Advanced Mode        │
│                 │                   │                           │
│ setup_commands_ │ CmdsSettings +    │ CmdsConfig +             │
│ auto()          │ CommandPolicy     │ ProfileResolver           │
└─────────────────┴───────────────────┴───────────────────────────┘
                                │
                    ┌──────────────────┐
                    │ CommandScopeMgr  │
                    │                  │
                    │ • setup_all()    │
                    │ • update_user()  │
                    │ • clear_user()   │
                    └──────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Builder     │    │    Registry      │    │   Translator    │
│               │    │                  │    │                 │
│ • build_cmds  │    │ • resolve_profile│    │ • i18n adapter  │
│ • validate    │    │ • get_command    │    │ • fallback      │
└───────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                    ┌──────────────────┐
                    │   Telegram API   │
                    │                  │
                    │ • set_commands   │
                    │ • delete_commands│
                    │ • menu_button    │
                    └──────────────────┘
```

## 🎯 Design Principles

### 1. **Progressive Complexity**
- Start simple with auto-setup
- Scale to advanced configurations as needed
- No forced complexity for simple use cases

### 2. **Type Safety**
- Full type hints throughout the codebase
- Strict type checking with Pyright
- Runtime validation with Pydantic

### 3. **i18n First**
- Built-in support for multiple languages
- Graceful fallback handling
- Extensible translation system

### 4. **Telegram API Compliance**
- Respects all Telegram command constraints
- Proper scope hierarchy handling
- Menu button integration

## 📦 Core Components

### CommandScopeManager
The central orchestrator that coordinates all command management operations.

```python
class CommandScopeManager:
    def __init__(self, bot: Bot, *, settings=None, config=None, ...):
        # Supports both simple and advanced modes
    
    async def setup_all(self) -> None:
        # Apply all configured scopes and menu button
    
    async def update_user_commands(self, user_id: int, **flags) -> None:
        # Dynamically update user commands based on flags
    
    async def clear_user_commands(self, user_id: int) -> None:
        # Remove user-specific command overrides
```

**Key Features:**
- Dual-mode operation (simple + advanced)
- Automatic scope ordering by specificity
- Profile-based command resolution
- i18n integration

### Builder System
Converts command names and configurations into Telegram BotCommand objects.

```python
def build_bot_commands(
    command_names: List[str],
    *,
    lang: str,
    translator: Optional[Translator] = None,
    key_prefix: str = "cmd",
) -> List[BotCommand]:
    # Build BotCommand objects with i18n descriptions
```

**Key Features:**
- Command name validation and sanitization
- i18n description resolution
- Fallback handling for missing translations
- Telegram API compliance (length limits, character restrictions)

### Registry System
Manages command profiles and resolves which commands belong to which profiles.

```python
class CommandRegistry:
    def __init__(self, cfg: CmdsConfig):
        # Initialize with configuration
    
    def resolve_profile_commands(self, profile: str) -> List[str]:
        # Get command list for a profile (include - exclude)
    
    def get_command(self, name: str) -> Optional[CommandDef]:
        # Get command definition by name
```

**Key Features:**
- Profile-based command grouping
- Include/exclude logic
- Command definition lookup
- Configuration validation

### Translator System
Provides a unified interface for i18n integration.

```python
class Translator(Protocol):
    def __call__(self, key: str, *, locale: str) -> Optional[str]: ...

def build_translator_from_i18n(i18n_obj) -> Translator:
    # Create translator adapter from aiogram i18n instance
```

**Key Features:**
- Protocol-based design for extensibility
- aiogram i18n integration
- Graceful fallback handling
- No-op translator for testing

## 🔄 Data Flow

### 1. Initialization Flow
```
User Code → CommandScopeManager → Configuration → Registry → Builder
```

### 2. Setup Flow
```
setup_all() → Apply Config → Resolve Scopes → Build Commands → Telegram API
```

### 3. Dynamic Update Flow
```
update_user_commands() → Profile Resolver → Registry → Builder → Telegram API
```

## 🎛️ Configuration System

### Simple Mode Configuration
```python
@dataclass
class CmdsSettings:
    languages: List[str] = ["en"]
    fallback_language: str = "en"
    i18n_key_prefix: str = "cmd"
    profile: str = "default"
    menu_button: str = "commands"
```

### Advanced Mode Configuration
```python
class CmdsConfig(BaseModel):
    languages: List[str] = ["en"]
    fallback_language: str = "en"
    i18n_key_prefix: str = "cmd"
    commands: Dict[str, CommandDef] = Field(default_factory=dict)
    profiles: Dict[str, ProfileDef] = Field(default_factory=dict)
    scopes: List[ScopeDef] = Field(default_factory=list)
    menu_button: MenuButtonDef = Field(default_factory=MenuButtonDef)
```

## 🔧 Policy System

### Command Policy (Simple Mode)
```python
class CommandPolicy(Protocol):
    def __call__(self, flags: Flags) -> List[str]: ...

def default_policy(flags: Flags) -> List[str]:
    # Convert user flags to command list
```

### Profile Resolver (Advanced Mode)
```python
class ProfileResolver(Protocol):
    def __call__(self, flags: Flags) -> str: ...

def my_profile_resolver(flags: Flags) -> str:
    # Convert user flags to profile name
```

## 🌍 i18n Integration

### Translation Key Pattern
```
{prefix}.{command}.desc
```

Example:
- `cmd.start.desc` → "Start the bot"
- `cmd.help.desc` → "Show help information"

### Fallback Strategy
1. Try i18n key with user's language
2. Try i18n key with fallback language
3. Use Title Case of command name
4. Use "Command" as final fallback

## 🎯 Scope Management

### Scope Hierarchy (Most Specific First)
1. `chat_member` - Specific user in specific chat
2. `chat_admins` - All admins in specific chat
3. `chat` - All users in specific chat
4. `all_chat_admins` - All chat administrators globally
5. `all_group_chats` - All group chats
6. `all_private_chats` - All private chats
7. `default` - Global fallback

### Scope Application Order
Commands are applied in order of specificity, with more specific scopes overriding broader ones.

## 🔄 Dynamic Updates

### User Command Updates
```python
await manager.update_user_commands(
    user_id=12345,
    is_registered=True,
    has_vehicle=False,
    user_language="en"
)
```

**Process:**
1. Create Flags object from parameters
2. Resolve profile (policy or resolver)
3. Get command list from registry
4. Build BotCommand objects with i18n
5. Apply to user's private chat scope

### Command Clearing
```python
await manager.clear_user_commands(user_id)
```

**Process:**
1. Delete user-specific command overrides
2. User falls back to broader scope commands
3. Log the operation for debugging

## 🧪 Testing Architecture

### Unit Tests
- Test individual components in isolation
- Mock external dependencies (Telegram API, i18n)
- Validate configuration models
- Test edge cases and error conditions

### Integration Tests
- Test full command setup workflows
- Verify Telegram API interactions
- Test i18n integration
- Validate scope hierarchy

### Performance Tests
- Benchmark command building performance
- Test with large command sets
- Measure memory usage
- Validate scalability

## 🔒 Security Considerations

### Input Validation
- Command names are validated against Telegram constraints
- User IDs are validated as positive integers
- Configuration is validated with Pydantic
- i18n keys are sanitized

### Error Handling
- Graceful degradation on i18n failures
- Fallback to default commands on errors
- Comprehensive logging for debugging
- No sensitive data in logs

## 🚀 Performance Optimizations

### Caching
- Command definitions are cached in registry
- Translation results can be cached (future enhancement)
- Profile resolution results can be memoized

### Batch Operations
- Multiple scopes are applied in single operations
- Command building is optimized for bulk operations
- Minimal API calls to Telegram

### Memory Efficiency
- Lazy loading of configurations
- Efficient data structures
- Minimal object creation in hot paths

## 🔮 Future Enhancements

### Planned Features
- **Rate Limiting**: Built-in rate limiting for command updates
- **Caching**: Redis-based caching for multi-worker deployments
- **Analytics**: Command usage analytics and insights
- **Webhooks**: Webhook-based command management
- **Admin Panel**: Web interface for command management

### Architecture Evolution
- Plugin system for custom command types
- Event-driven architecture for real-time updates
- Microservices support for large-scale deployments
- GraphQL API for advanced integrations

---

This architecture provides a solid foundation for command management while remaining flexible and extensible for future needs.
