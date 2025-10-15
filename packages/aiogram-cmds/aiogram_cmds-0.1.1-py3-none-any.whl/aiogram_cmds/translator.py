"""
Translator protocol and adapters for i18n integration.
"""

from contextlib import nullcontext
from typing import Protocol


class Translator(Protocol):
    """Protocol for translation functions.

    Contract:
    - Returns None when translation is missing (allows callers to fallback)
    - Supports optional explicit locale switching via keyword-only ``locale``
    - Supports optional pluralization via ``plural`` and ``count``
    """

    def __call__(
        self,
        key: str,
        *,
        locale: str | None = None,
        plural: str | None = None,
        count: int | None = None,
    ) -> str | None: ...


def build_translator_from_i18n(i18n_obj) -> Translator:
    """
    Build translator adapter from an aiogram ``I18n`` instance.

    Implementation details:
    - aiogram resolves locale from context/middleware; this adapter optionally accepts
      an explicit ``locale`` and uses ``I18n.with_locale(locale)`` when provided.
    - Pluralization is supported via ``plural`` and ``count`` mapped to ``ngettext``.
    - Missing translations return None so callers can apply sensible fallbacks.
    """

    def _translate(
        key: str, *, locale: str | None = None, plural: str | None = None, count: int | None = None
    ) -> str | None:
        try:
            # Enter locale context if explicitly provided; otherwise rely on ambient context
            ctx = i18n_obj.with_locale(locale) if locale else nullcontext()
            with ctx:
                if plural is not None and count is not None:
                    value = i18n_obj.ngettext(key, plural, count)
                else:
                    value = i18n_obj.gettext(key)
            if not value or value == key:
                return None
            return value
        except Exception:
            return None

    return _translate


def noop_translator(
    key: str, *, locale: str | None = None, plural: str | None = None, count: int | None = None
) -> str | None:
    """No-op translator that always returns None."""
    return None
