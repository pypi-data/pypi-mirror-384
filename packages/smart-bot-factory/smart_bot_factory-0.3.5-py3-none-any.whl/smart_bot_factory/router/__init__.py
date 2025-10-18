"""
Router модули smart_bot_factory
"""

from ..core.router import EventRouter

__all__ = [
    'EventRouter',  # Роутер для событий (бизнес-логика)
    # Для Telegram используйте aiogram.Router напрямую
]