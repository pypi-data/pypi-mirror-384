"""
Message модули smart_bot_factory
"""


from ..core.message_sender import (
    send_message_by_human, 
    send_message_by_ai,
    send_message_to_users_by_stage,
    send_message,
)


def get_bot():
    """
    Получает aiogram Bot из глобального контекста
    
    Доступен после вызова bot_builder.start()
    
    Returns:
        Bot: aiogram Bot объект
        
    Raises:
        RuntimeError: Если bot еще не инициализирован
        
    Example:
        from smart_bot_factory.message import get_bot
        
        @event_router.event_handler("booking")
        async def handle_booking(user_id: int, event_data: str):
            bot = get_bot()
            
            # Получаем информацию о пользователе из Telegram
            telegram_user = await bot.get_chat(user_id)
            name = telegram_user.first_name or 'Клиент'
            
            # Используем любые методы aiogram Bot
            await bot.send_message(user_id, f"Привет, {name}!")
            await bot.send_photo(user_id, photo=...)
    """
    from ..handlers.handlers import get_global_var
    
    bot = get_global_var('bot')
    if not bot:
        raise RuntimeError(
            "Bot еще не инициализирован. "
            "Убедитесь что bot_builder.start() уже вызван. "
            "Функция get_bot() доступна только внутри обработчиков событий, "
            "которые выполняются во время работы бота."
        )
    return bot


__all__ = [
    'send_message_by_human',
    'send_message_by_ai',
    'send_message_to_users_by_stage',
    'send_message',  # Чистая отправка с файлами и кнопками
    'get_bot',  # Доступ к aiogram Bot
]