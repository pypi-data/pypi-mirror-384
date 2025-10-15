"""
Dynamic command management for runtime profile changes.
"""

from aiogram import Bot
from aiogram.types import BotCommandScopeChat, BotCommandScopeChatMember

from .builders_configured import build_from_config
from .customize import CmdsConfig
from .registry import CommandRegistry
from .translator import Translator


async def set_user_profile(
    bot: Bot,
    cfg: CmdsConfig,
    *,
    translator: Translator | None,
    user_id: int,
    chat_id: int | None,
    profile: str,
    language: str,
) -> None:
    """
    Dynamically apply a profile to a user (optionally in a specific chat).
    """
    reg = CommandRegistry(cfg)
    names = list(reg.resolve_profile_commands(profile))
    cmds = build_from_config(
        reg, names, lang=language, translator=translator, key_prefix=cfg.i18n_key_prefix
    )

    scope = (
        BotCommandScopeChat(chat_id=user_id)
        if chat_id is None
        else BotCommandScopeChatMember(chat_id=chat_id, user_id=user_id)
    )

    await bot.set_my_commands(cmds, scope=scope, language_code=language)
