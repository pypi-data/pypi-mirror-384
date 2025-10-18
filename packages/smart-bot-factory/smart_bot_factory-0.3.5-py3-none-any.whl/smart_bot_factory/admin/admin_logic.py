# Исправленный admin_logic.py с правильной обработкой диалогов

import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

# Импортируем состояния
from ..core.states import UserStates, AdminStates

# Создаем роутер для админских обработчиков
admin_router = Router()

def setup_admin_handlers(dp):
    """Настройка админских обработчиков"""
    dp.include_router(admin_router)

@admin_router.message(Command(commands=["отмена", "cancel"]))
async def cancel_handler(message: Message, state: FSMContext):
    """Отмена текущего действия и очистка state"""
    from ..handlers.handlers import get_global_var
    admin_manager = get_global_var('admin_manager')
    
    # Получаем текущий state
    current_state = await state.get_state()
    
    # Очищаем временные файлы если это создание события
    if current_state and current_state.startswith('AdminStates:create_event'):
        from .admin_events import cleanup_temp_files
        await cleanup_temp_files(state)
    
    # Очищаем state
    await state.clear()
    
    if current_state:
        logger.info(f"State очищен для пользователя {message.from_user.id}: {current_state}")
        
        # Если это админ, возвращаем в админ режим
        if admin_manager.is_admin(message.from_user.id):
            await state.set_state(AdminStates.admin_mode)
            await message.answer(
                "✅ Текущее действие отменено\n"
                "Вы вернулись в админ режим\n\n"
                "Используйте /admin для просмотра доступных команд",
                parse_mode='Markdown'
            )
        else:
            await message.answer(
                "✅ Текущее действие отменено\n\n"
                "Используйте /start для начала работы",
                parse_mode='Markdown'
            )
    else:
        await message.answer(
            "ℹ️ Нет активных действий для отмены",
            parse_mode='Markdown'
        )

async def admin_start_handler(message: Message, state: FSMContext):
    """Обработчик /start для админов в режиме администратора"""
    from ..handlers.handlers import get_global_var
    admin_manager = get_global_var('admin_manager')
    
    await state.set_state(AdminStates.admin_mode)
    
    admin_status = admin_manager.get_admin_mode_text(message.from_user.id)
    
    # Основное меню админа
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="💬 Активные чаты", callback_data="admin_active_chats")],
        [InlineKeyboardButton(text="🔄 Режим польз.", callback_data="admin_toggle_mode")]
    ])
    
    welcome_text = f"""
{admin_status}

🎛️ **Панель администратора**

Доступные команды:
• `/стат` - статистика воронки
• `/история user_id` - история пользователя
• `/чат user_id` - начать диалог
• `/чаты` - активные диалоги
• `/стоп` - завершить диалог
• `/админ` - переключить режим
• `/отмена` - отменить текущее действие

📅 **Управление событиями:**
• `/создать_событие` - создать новое событие
• `/список_событий` - список активных событий
• `/удалить_событие название` - отменить событие
"""

    await message.answer(welcome_text, reply_markup=keyboard, parse_mode='Markdown')

@admin_router.message(Command(commands=["стат", "stats"]))
async def admin_stats_handler(message: Message, state: FSMContext):
    """Статистика воронки"""
    from ..handlers.handlers import get_global_var
    admin_manager = get_global_var('admin_manager')
    analytics_manager = get_global_var('analytics_manager')
    
    if not admin_manager.is_admin(message.from_user.id):
        return
    
    try:
        # Получаем статистику
        funnel_stats = await analytics_manager.get_funnel_stats(7)
        events_stats = await analytics_manager.get_events_stats(7)
        
        # Форматируем ответ
        funnel_text = analytics_manager.format_funnel_stats(funnel_stats)
        events_text = analytics_manager.format_events_stats(events_stats)
        
        full_text = f"{funnel_text}\n\n{events_text}"
        
        await message.answer(full_text)
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await message.answer("❌ Ошибка получения статистики")

@admin_router.message(Command(commands=["история", "history"]))
async def admin_history_handler(message: Message, state: FSMContext):
    """История пользователя"""
    from ..handlers.handlers import get_global_var
    admin_manager = get_global_var('admin_manager')
    analytics_manager = get_global_var('analytics_manager')
    
    if not admin_manager.is_admin(message.from_user.id):
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Укажите ID пользователя: /история 123456789")
            return
        
        user_id = int(parts[1])
        
        # Получаем историю (та же функция что использует кнопка)
        journey = await analytics_manager.get_user_journey(user_id)
        
        if not journey:
            await message.answer(f"❌ У пользователя {user_id} нет активной сессии")
            return
        
        # Используем ту же функцию форматирования что и кнопка
        history_text = analytics_manager.format_user_journey(user_id, journey)
        
        await message.answer(history_text)
        
    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя")
    except Exception as e:
        logger.error(f"Ошибка получения истории: {e}")
        await message.answer("❌ Ошибка получения истории")

@admin_router.message(Command(commands=["чат", "chat"]))
async def admin_chat_handler(message: Message, state: FSMContext):
    """Начать диалог с пользователем"""
    from ..handlers.handlers import get_global_var
    
    admin_manager = get_global_var('admin_manager') 
    supabase_client = get_global_var('supabase_client')
    conversation_manager = get_global_var('conversation_manager')
    
    if not admin_manager.is_admin(message.from_user.id):
        return
    
    try:
        # Парсим user_id из команды
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Укажите ID пользователя: /чат 123456789")
            return
        
        user_id = int(parts[1])
        admin_id = message.from_user.id
        
        logger.info(f"👑 Админ {admin_id} хочет начать диалог с пользователем {user_id}")
        
        # Проверяем, есть ли активная сессия у пользователя
        session_info = await supabase_client.get_active_session(user_id)
        if not session_info:
            await message.answer(f"❌ У пользователя {user_id} нет активной сессии")
            logger.warning(f"❌ У пользователя {user_id} нет активной сессии")
            return
        
        logger.info(f"✅ У пользователя {user_id} есть активная сессия: {session_info['id']}")
        
        # Начинаем диалог
        logger.info(f"🚀 Запускаем создание диалога...")
        success = await conversation_manager.start_admin_conversation(admin_id, user_id)
        
        if success:
            # ✅ ИСПРАВЛЕНИЕ: Правильно переключаем состояние админа
            await state.set_state(AdminStates.in_conversation)
            await state.update_data(conversation_user_id=user_id)
            
            await message.answer(f"✅ Диалог с пользователем {user_id} начат\n💬 Ваши сообщения будут переданы пользователю\n⏹️ Используйте /стоп для завершения")
            logger.info(f"✅ Диалог успешно создан, админ переключен в состояние in_conversation")
        else:
            await message.answer(f"❌ Не удалось начать диалог с пользователем {user_id}")
            logger.error(f"❌ Не удалось создать диалог")
            
    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя")
        logger.error(f"❌ Неверный формат ID пользователя: {message.text}")
    except Exception as e:
        logger.error(f"❌ Ошибка начала диалога: {e}")
        await message.answer("❌ Ошибка начала диалога")

@admin_router.message(Command(commands=["чаты", "chats"]))
async def admin_active_chats_command(message: Message, state: FSMContext):
    """Показать активные диалоги админов"""
    from ..handlers.handlers import get_global_var
    admin_manager = get_global_var('admin_manager')
    conversation_manager = get_global_var('conversation_manager')
    
    if not admin_manager.is_admin(message.from_user.id):
        return
    
    try:
        conversations = await conversation_manager.get_active_conversations()
        formatted_text = conversation_manager.format_active_conversations(conversations)
        
        # ✅ ИСПРАВЛЕНИЕ: Убираем parse_mode='Markdown' чтобы избежать ошибок парсинга
        await message.answer(formatted_text)
        
    except Exception as e:
        logger.error(f"Ошибка получения активных чатов: {e}")
        await message.answer("❌ Ошибка получения активных диалогов")

@admin_router.message(Command(commands=["стоп", "stop"]))
async def admin_stop_handler(message: Message, state: FSMContext):
    """Завершить диалог"""
    from ..handlers.handlers import get_global_var
    admin_manager = get_global_var('admin_manager')
    conversation_manager = get_global_var('conversation_manager')
    
    if not admin_manager.is_admin(message.from_user.id):
        return
    
    try:
        admin_id = message.from_user.id
        
        # Проверяем есть ли активный диалог
        conversation = await conversation_manager.get_admin_active_conversation(admin_id)
        
        if conversation:
            user_id = conversation['user_id']
            logger.info(f"🛑 Завершаем диалог админа {admin_id} с пользователем {user_id}")
            
            success = await conversation_manager.end_admin_conversation(admin_id)
            
            if success:
                # ✅ ИСПРАВЛЕНИЕ: Правильно переключаем состояние обратно
                await state.set_state(AdminStates.admin_mode)
                await state.update_data(conversation_user_id=None)
                
                await message.answer(f"✅ Диалог с пользователем {user_id} завершен")
                logger.info(f"✅ Диалог завершен, админ переключен в admin_mode")
            else:
                await message.answer("❌ Ошибка завершения диалога")
        else:
            await message.answer("❌ Нет активного диалога")
            logger.info(f"❌ У админа {admin_id} нет активного диалога")
            
    except Exception as e:
        logger.error(f"Ошибка завершения диалога: {e}")
        await message.answer("❌ Ошибка завершения диалога")

@admin_router.message(Command(commands=["админ", "admin"]))
async def admin_toggle_handler(message: Message, state: FSMContext):
    """Переключение режима админа"""
    from ..handlers.handlers import get_global_var
    admin_manager = get_global_var('admin_manager')
    from ..handlers.handlers import user_start_handler
    
    if not admin_manager.is_admin(message.from_user.id):
        return
    
    new_mode = admin_manager.toggle_admin_mode(message.from_user.id)
    
    if new_mode:
        # Переключились в режим админа
        await admin_start_handler(message, state)
    else:
        # Переключились в режим пользователя
        await state.clear()
        await message.answer("🔄 Переключен в режим пользователя\nНапишите /start для начала диалога")

@admin_router.message(Command("debug_chat"))
async def debug_chat_handler(message: Message, state: FSMContext):
    """Отладка диалогов админов"""
    from ..handlers.handlers import get_global_var
    admin_manager = get_global_var('admin_manager')
    conversation_manager = get_global_var('conversation_manager')
    supabase_client = get_global_var('supabase_client')
    
    if not admin_manager.is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /debug_chat USER_ID")
        return
    
    try:
        user_id = int(parts[1])
        
        # 1. Проверяем запись в БД
        conversation = await conversation_manager.is_user_in_admin_chat(user_id)
        
        debug_info = [
            f"🔍 ОТЛАДКА ДИАЛОГА С {user_id}",
            "",
            f"📊 Диалог в БД: {'✅' if conversation else '❌'}",
        ]
        
        if conversation:
            debug_info.extend([
                f"👑 Админ: {conversation['admin_id']}",
                f"🕐 Начат: {conversation['started_at']}",
            ])
        
        # 2. Проверяем активную сессию пользователя
        session_info = await supabase_client.get_active_session(user_id)
        debug_info.append(f"🎯 Активная сессия: {'✅' if session_info else '❌'}")
        
        if session_info:
            debug_info.append(f"📝 ID сессии: {session_info['id']}")
        
        # 3. Проверяем состояние пользователя (если он онлайн)
        debug_info.append(f"")
        debug_info.append(f"ℹ️ Для проверки состояния пользователь должен написать что-то")
        
        await message.answer("\n".join(debug_info))
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        logger.error(f"Ошибка отладки: {e}")

@admin_router.callback_query(F.data.startswith("admin_"))
async def admin_callback_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик callback кнопок админов"""
    from ..handlers.handlers import get_global_var
    admin_manager = get_global_var('admin_manager')
    analytics_manager = get_global_var('analytics_manager')
    conversation_manager = get_global_var('conversation_manager')
    
    if not admin_manager.is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    
    data = callback.data
    
    try:
        if data == "admin_stats":
            # Показываем статистику
            funnel_stats = await analytics_manager.get_funnel_stats(7)
            events_stats = await analytics_manager.get_events_stats(7)
            
            funnel_text = analytics_manager.format_funnel_stats(funnel_stats)
            events_text = analytics_manager.format_events_stats(events_stats)
            
            await callback.message.answer(f"{funnel_text}\n\n{events_text}")
            
        elif data == "admin_toggle_mode":
            # Переключаем режим
            new_mode = admin_manager.toggle_admin_mode(callback.from_user.id)
            mode_text = "администратор" if new_mode else "пользователь"
            await callback.answer(f"Режим переключен: {mode_text}")
            
            if not new_mode:
                await state.clear()
                await callback.message.answer("🔄 Теперь вы в режиме пользователя")

        elif data == "admin_active_chats":
            # Показываем активные диалоги
            conversations = await conversation_manager.get_active_conversations()
            formatted_text = conversation_manager.format_active_conversations(conversations)
            
            # ✅ ИСПРАВЛЕНИЕ: Убираем parse_mode='Markdown'
            await callback.message.answer(formatted_text)
                
        elif data.startswith("admin_history_"):
            user_id = int(data.split("_")[2])
            journey = await analytics_manager.get_user_journey(user_id)
            history_text = analytics_manager.format_user_journey(user_id, journey)
            await callback.message.answer(history_text)
            
        elif data.startswith("admin_end_"):
            user_id = int(data.split("_")[2])
            
            # Проверяем есть ли активный диалог
            conversation = await conversation_manager.get_admin_active_conversation(callback.from_user.id)
            
            if conversation and conversation['user_id'] == user_id:
                await conversation_manager.end_admin_conversation(callback.from_user.id)
                
                # ✅ ИСПРАВЛЕНИЕ: Правильно переключаем состояние
                await state.set_state(AdminStates.admin_mode)
                await state.update_data(conversation_user_id=None)
                
                await callback.answer("Диалог завершен")
                await callback.message.answer(f"✅ Диалог с пользователем {user_id} завершен")
                logger.info(f"✅ Диалог завершен через кнопку, админ переключен в admin_mode")
            else:
                await callback.answer("Диалог не найден")

        elif data.startswith("admin_chat_"):
            user_id = int(data.split("_")[2])
            admin_id = callback.from_user.id
            
            success = await conversation_manager.start_admin_conversation(admin_id, user_id)
            if success:
                # ✅ ИСПРАВЛЕНИЕ: Правильно переключаем состояние
                await state.set_state(AdminStates.in_conversation)
                await state.update_data(conversation_user_id=user_id)
                
                await callback.answer("Диалог начат")
                await callback.message.answer(f"✅ Диалог с пользователем {user_id} начат")
                logger.info(f"✅ Диалог начат через кнопку, админ переключен в in_conversation")
            else:
                await callback.answer("Не удалось начать диалог")         

        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка обработки callback {data}: {e}")
        await callback.answer("Ошибка")

@admin_router.message(StateFilter(AdminStates.admin_mode, AdminStates.in_conversation), F.text, lambda message: not message.text.startswith('/'))
async def admin_message_handler(message: Message, state: FSMContext):
    """Обработчик сообщений админов"""
    from ..handlers.handlers import get_global_var
    admin_manager = get_global_var('admin_manager')
    conversation_manager = get_global_var('conversation_manager')
    
    if not admin_manager.is_admin(message.from_user.id):
        return
    
    try:
        logger.info(f"👑 Получено сообщение от админа {message.from_user.id}: '{message.text}'")
        
        # Пытаемся обработать как админское сообщение
        handled = await conversation_manager.route_admin_message(message, state)
        
        if handled:
            logger.info(f"✅ Сообщение админа обработано и переслано пользователю")
        else:
            # Не админское сообщение - показываем справку
            logger.info(f"❌ Сообщение админа не обработано, показываем справку")
            await message.answer("""
👑 **Режим администратора**

Доступные команды:
• `/стат` - статистика воронки
• `/история user_id` - история пользователя  
• `/чат user_id` - начать диалог
• `/стоп` - завершить диалог
• `/админ` - переключить режим

💡 Если вы в диалоге с пользователем, просто напишите сообщение - оно будет переслано пользователю.
""", parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения админа: {e}")
        await message.answer("❌ Ошибка обработки команды")