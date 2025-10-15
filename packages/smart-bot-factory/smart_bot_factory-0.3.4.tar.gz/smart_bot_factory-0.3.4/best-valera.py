"""
Best Valera Bot - Пример умного Telegram бота на Smart Bot Factory

Демонстрирует:
- Обработку событий (event_handler)
- Планирование задач (schedule_task)
- Глобальные уведомления (global_handler)
- Кастомные Telegram команды (aiogram.Router)
- Кастомное получение времени событий (event_type=функция)
"""

import asyncio
import logging
from datetime import datetime, timedelta

# Smart Bot Factory
from smart_bot_factory.router import EventRouter
from smart_bot_factory.message import send_message_by_human, send_message_to_users_by_stage
from smart_bot_factory.supabase import SupabaseClient
from smart_bot_factory.creation import BotBuilder

# Aiogram для Telegram команд
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

# =============================================================================
# ИНИЦИАЛИЗАЦИЯ
# =============================================================================

# Роутеры
event_router = EventRouter("best-valera")  # Бизнес-логика (события, задачи)
telegram_router = Router(name="commands")  # Telegram команды

# Клиенты
supabase_client = SupabaseClient("best-valera")

# Bot Builder
bot_builder = BotBuilder("best-valera")

# =============================================================================
# ОБРАБОТЧИКИ СОБЫТИЙ (немедленное выполнение)
# =============================================================================

@event_router.event_handler("collect_phone", notify=True, once_only=True)
async def handle_phone_collection(user_id: int, phone_number: str):
    """
    Обрабатывает получение номера телефона от клиента
    
    ИИ создает: {"тип": "collect_phone", "инфо": "+79001234567"}
    Выполняется: немедленно
    once_only=True: только 1 раз для пользователя
    """
    logger.info(f"📱 Получен телефон от пользователя {user_id}: {phone_number}")
    
    # Сохраняем телефон в метаданные сессии
    session = await supabase_client.get_active_session(user_id)
    if session:
        metadata = session.get('metadata', {})
        metadata['phone'] = phone_number
        await supabase_client.update_session_metadata(session['id'], metadata)
    
    await send_message_by_human(
        user_id=user_id,
        message_text=f"✅ Спасибо! Ваш номер {phone_number} сохранен"
    )
    
    return {"status": "success", "phone": phone_number}

@event_router.event_handler("collect_name", once_only=True)
async def handle_name_collection(user_id: int, client_name: str):
    """
    Обрабатывает получение имени клиента
    
    ИИ создает: {"тип": "collect_name", "инфо": "Михаил"}
    """
    logger.info(f"👤 Получено имя от пользователя {user_id}: {client_name}")
    
    session = await supabase_client.get_active_session(user_id)
    if session:
        metadata = session.get('metadata', {})
        metadata['confirmed_name'] = client_name
        await supabase_client.update_session_metadata(session['id'], metadata)
    
    return {"status": "success", "name": client_name}

# =============================================================================
# ЗАПЛАНИРОВАННЫЕ ЗАДАЧИ (выполняются через время)
# =============================================================================

@event_router.schedule_task("follow_up", delay="24h", smart_check=True, once_only=True)
async def send_follow_up(user_id: int, reminder_text: str):
    """
    Напоминание через 24 часа после последнего сообщения
    
    ИИ создает: {"тип": "follow_up", "инфо": "Не забудьте про запись"}
    smart_check=True: отменится если пользователь был активен
    """
    await send_message_by_human(
        user_id=user_id,
        message_text=f"👋 {reminder_text or 'Добрый день! Как дела с записью?'}"
    )
    
    return {"status": "sent", "type": "follow_up"}

# =============================================================================
# НАПОМИНАНИЯ С КАСТОМНЫМ ПОЛУЧЕНИЕМ ВРЕМЕНИ
# =============================================================================

async def get_booking_datetime(user_id: int, user_data: str) -> datetime:
    """
    Получает время записи из внешнего API (например YClients)
    
    Это кастомная логика - можете обращаться к любому API
    
    Returns:
        datetime: Когда запланирована запись
    """
    # Реальный пример:
    # from yclients_api import get_user_next_booking
    # booking = await get_user_next_booking(user_id)
    # return booking['datetime']
    
    # Демо: возвращаем "завтра в 19:00"
    tomorrow = datetime.now() + timedelta(days=1)
    appointment_time = tomorrow.replace(hour=19, minute=0, second=0, microsecond=0)
    
    logger.info(f"📅 Запись для user {user_id}: {appointment_time.strftime('%d.%m.%Y %H:%M')}")
    return appointment_time

@event_router.schedule_task(
    "appointment_reminder",
    delay="1h",  # За 1 час до записи
    event_type=get_booking_datetime,  # Функция для получения времени
    smart_check=False  # Отправить в любом случае
)
async def send_appointment_reminder(user_id: int, user_data: str):
    """
    Напоминание за 1 час до записи
    
    Работает так:
    1. ИИ: {"тип": "appointment_reminder", "инфо": ""}
    2. Вызывается get_booking_datetime(user_id, "") → возвращает datetime
    3. Вычисляется: reminder_time = booking_datetime - 1h
    4. Напоминание отправляется в вычисленное время
    """
    await send_message_by_human(
        user_id=user_id,
        message_text="⏰ Напоминаю о вашей записи через час!"
    )
    
    return {"status": "sent", "type": "appointment_reminder"}

# =============================================================================
# ГЛОБАЛЬНЫЕ ОБРАБОТЧИКИ (для всех пользователей)
# =============================================================================

@event_router.global_handler("promo_announcement", delay="2h", notify=True)
async def send_promo_to_all(announcement_text: str):
    """
    Отправляет рекламу всем пользователям через 2 часа
    
    ИИ создает: {"тип": "promo_announcement", "инфо": "Скидка 20% до конца недели!"}
    Выполняется: через 2 часа
    notify=True: админы получат уведомление
    """
    logger.info(f"📢 Отправляем промо всем пользователям: {announcement_text}")
    
    await send_message_to_users_by_stage(
        stage="all",
        message_text=f"🎉 {announcement_text}",
        bot_id="best-valera"
    )
    
    return {"status": "sent", "recipients": "all"}

# =============================================================================
# КАСТОМНЫЕ TELEGRAM КОМАНДЫ (aiogram.Router - без обертки)
# =============================================================================

@telegram_router.message(Command("price", "цена"))
async def price_command(message: Message):
    """Команда /price - показывает прайс-лист"""
    await message.answer(
        "💰 **Наши цены:**\n\n"
        "• Стрижка мужская — 1500₽\n"
        "• Стрижка женская — 2000₽\n"
        "• Окрашивание — от 3000₽\n"
        "• Укладка — 1000₽\n\n"
        "Для записи напишите боту!",
        parse_mode="Markdown"
    )

@telegram_router.message(Command("catalog", "каталог"))
async def catalog_command(message: Message):
    """Команда /catalog - показывает каталог с кнопками"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Акции", callback_data="promo")],
        [InlineKeyboardButton(text="💇 Стрижки", callback_data="haircut")],
        [InlineKeyboardButton(text="💅 Маникюр", callback_data="manicure")],
        [InlineKeyboardButton(text="📅 Записаться", callback_data="book")]
    ])
    
    await message.answer(
        "📁 Выберите категорию:",
        reply_markup=keyboard
    )

@telegram_router.callback_query(F.data == "book")
async def handle_booking_button(callback):
    """Обработка кнопки "Записаться" """
    await callback.answer("Переключаю на бота для записи...")
    await callback.message.answer(
        "📝 Напишите боту желаемую дату и время для записи"
    )

@telegram_router.message(F.text.lower().contains("помощь"))
async def help_message(message: Message):
    """Реагирует на слово "помощь" в сообщении"""
    await message.answer(
        "💁 Я могу помочь с:\n"
        "• Записью на услуги\n"
        "• Информацией о ценах\n"
        "• Консультацией\n\n"
        "Просто напишите что вас интересует!"
    )

# =============================================================================
# ОСНОВНАЯ ФУНКЦИЯ
# =============================================================================

async def main():
    """Основная функция запуска бота"""
    try:
        # Регистрируем роутеры
        bot_builder.register_routers(event_router)  # События и задачи
        bot_builder.register_telegram_router(telegram_router)  # Telegram команды
        
        # Собираем и запускаем
        await bot_builder.build()
        await bot_builder.start()
        
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        logger.exception("Детали ошибки:")
        raise

if __name__ == "__main__":
    asyncio.run(main())
