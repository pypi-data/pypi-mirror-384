# Исправленный handlers.py с отладкой маршрутизации

import logging
import time
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from ..core.bot_utils import send_message, parse_ai_response, process_events, send_welcome_file
from ..core.states import UserStates, AdminStates

logger = logging.getLogger(__name__)

# Создаем роутер для обработчиков
router = Router()

def setup_handlers(dp):
    """Настройка основных обработчиков"""
    # Подключаем middleware
    router.message.middleware()(admin_middleware)
    
    # Регистрируем роутер
    dp.include_router(router)

# Функция для получения глобальных переменных
def get_global_var(var_name):
    """Получает глобальную переменную из модуля handlers"""
    import sys
    current_module = sys.modules[__name__]
    return getattr(current_module, var_name, None)

# Middleware для проверки админов
async def admin_middleware(handler, event: Message, data: dict):
    """Middleware для обновления информации об админах"""
    admin_manager = get_global_var('admin_manager')
    
    if admin_manager and admin_manager.is_admin(event.from_user.id):
        await admin_manager.update_admin_info(event.from_user)
    
    return await handler(event, data)

@router.message(Command(commands=["start", "старт", "ст"]))
async def start_handler(message: Message, state: FSMContext):
    """Обработчик команды /start - сброс сессии и начало заново"""
    admin_manager = get_global_var('admin_manager')
    from ..admin.admin_logic import admin_start_handler
    from ..utils.debug_routing import debug_user_state
    
    try:
        await debug_user_state(message, state, "START_COMMAND")
        
        # Проверяем, админ ли это и в каком режиме
        if admin_manager.is_admin(message.from_user.id):
            if admin_manager.is_in_admin_mode(message.from_user.id):
                # Админ в режиме администратора - работаем как админ
                await admin_start_handler(message, state)
                return
            # Админ в режиме пользователя - работаем как обычный пользователь
        
        await user_start_handler(message, state)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке /start: {e}")
        await send_message(message, "Произошла ошибка при инициализации. Попробуйте позже.")

@router.message(Command(commands=["timeup", "вперед"]))
async def timeup_handler(message: Message, state: FSMContext):
    """Обработчик команды /timeup (или /вперед) - тестирование запланированных событий"""
    from ..core.decorators import process_scheduled_event, update_event_result
    from datetime import datetime
    
    supabase_client = get_global_var('supabase_client')
    
    try:
        await message.answer("🔄 Запускаю тестирование запланированных событий...")
        
        # Получаем события для этого пользователя И глобальные события (user_id = null)
        # 1. События пользователя
        user_events = supabase_client.client.table('scheduled_events').select(
            '*'
        ).eq('user_id', message.from_user.id).in_('status', ['pending', 'immediate']).execute()
        
        # 2. Глобальные события (без user_id)
        global_events = supabase_client.client.table('scheduled_events').select(
            '*'
        ).is_('user_id', 'null').in_('status', ['pending', 'immediate']).execute()
        
        # Объединяем события
        all_events = (user_events.data or []) + (global_events.data or [])
        
        if not all_events:
            await message.answer("📭 Нет запланированных событий для тестирования")
            return
        
        total_events = len(all_events)
        user_count = len(user_events.data or [])
        global_count = len(global_events.data or [])
        
        status_msg = f"📋 Найдено {total_events} событий:"
        if user_count > 0:
            status_msg += f"\n   👤 Ваших: {user_count}"
        if global_count > 0:
            status_msg += f"\n   🌍 Глобальных: {global_count}"
        status_msg += "\n\nВыполняю их немедленно..."
        
        await message.answer(status_msg)
        
        # Выполняем каждое событие
        success_count = 0
        failed_count = 0
        results = []
        
        for event in all_events:
            event_id = event['id']
            event_type = event['event_type']
            event_category = event['event_category']
            is_global = event.get('user_id') is None
            
            try:
                event_label = f"🌍 {event_type}" if is_global else f"👤 {event_type}"
                logger.info(f"🧪 Тестируем событие {event_id}: {event_category}/{event_type} ({'глобальное' if is_global else f'пользователя {message.from_user.id}'})")
                
                # Выполняем событие
                await process_scheduled_event(event)
                
                # Помечаем как выполненное
                await update_event_result(event_id, 'completed', {
                    "executed": True,
                    "test_mode": True,
                    "tested_by_user": message.from_user.id,
                    "tested_at": datetime.now().isoformat()
                })
                
                success_count += 1
                results.append(f"✅ {event_label}")
                logger.info(f"✅ Событие {event_id} успешно выполнено")
                
            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                event_label = f"🌍 {event_type}" if is_global else f"👤 {event_type}"
                results.append(f"❌ {event_label}: {error_msg[:50]}")
                logger.error(f"❌ Ошибка выполнения события {event_id}: {error_msg}")
                
                # Помечаем как failed
                await update_event_result(event_id, 'failed', None, error_msg)
        
        # Отправляем итоговую статистику
        result_text = [
            "📊 **Результаты тестирования:**",
            "",
            f"✅ Успешно: {success_count}",
            f"❌ Ошибок: {failed_count}",
            f"📋 Всего: {total_events}",
            "",
            "**События:**",
            f"👤 - ваши события",
            f"🌍 - глобальные события",
            ""
        ]
        
        # Добавляем результаты (максимум 10 событий)
        for result in results[:10]:
            result_text.append(result)
        
        if len(results) > 10:
            result_text.append(f"... и еще {len(results) - 10} событий")
        
        await message.answer("\n".join(result_text))
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в timeup_handler: {e}")
        await message.answer(f"❌ Ошибка тестирования: {str(e)}")
        
@router.message(F.voice | F.audio)
async def voice_handler(message: Message, state: FSMContext):
    """Обработчик голосовых и аудио сообщений"""
    openai_client = get_global_var('openai_client')
    bot = get_global_var('bot')
    admin_manager = get_global_var('admin_manager')
    
    import os
    from pathlib import Path
    from datetime import datetime
    
    processing_msg = None
    
    try:
        # Проверяем что это не админ в режиме администратора
        if admin_manager.is_admin(message.from_user.id):
            if admin_manager.is_in_admin_mode(message.from_user.id):
                return  # Админы работают с текстом
        
        logger.info(f"🎤 Получено голосовое сообщение от {message.from_user.id}")
        
        # Получаем файл
        if message.voice:
            file_id = message.voice.file_id
            duration = message.voice.duration
        else:
            file_id = message.audio.file_id
            duration = message.audio.duration
        
        # Показываем что обрабатываем
        processing_msg = await message.answer("🎤 Распознаю голос...")
        
        try:
            # Скачиваем файл
            file = await bot.get_file(file_id)
            
            # Путь для сохранения
            temp_dir = Path("temp_audio")
            temp_dir.mkdir(exist_ok=True)
            
            file_path = temp_dir / f"{message.from_user.id}_{int(datetime.now().timestamp())}.ogg"
            
            # Скачиваем
            await bot.download_file(file.file_path, file_path)
            logger.info(f"📥 Файл скачан: {file_path} ({duration} сек)")
            
            # Распознаем через Whisper
            recognized_text = await openai_client.transcribe_audio(str(file_path))
            
            # Удаляем временный файл и папку
            try:
                os.remove(file_path)
                logger.info(f"🗑️ Временный файл удален: {file_path}")
                
                # Проверяем, пуста ли папка
                if not any(temp_dir.iterdir()):
                    temp_dir.rmdir()
                    logger.info(f"🗑️ Временная папка удалена: {temp_dir}")
                
            except Exception as e:
                logger.warning(f"⚠️ Не удалось удалить временные файлы: {e}")
            
            if not recognized_text:
                await processing_msg.edit_text("❌ Не удалось распознать голос. Попробуйте еще раз.")
                return
            
            logger.info(f"✅ Текст распознан успешно: '{recognized_text[:100]}...'")
            
            # Получаем данные сессии
            current_state = await state.get_state()
            data = await state.get_data()
            
            logger.info(f"🔍 Текущее состояние: {current_state}")
            logger.info(f"🔍 Данные в state: {data}")
            
            session_id = data.get('session_id')
            system_prompt = data.get('system_prompt')
            
            logger.info(f"📝 session_id из state: {session_id}")
            
            # Если session_id нет в state, пытаемся получить из БД
            if not session_id:
                logger.warning(f"⚠️ session_id не найден в state, ищем активную сессию в БД...")
                supabase_client = get_global_var('supabase_client')
                
                session_info = await supabase_client.get_active_session(message.from_user.id)
                if session_info:
                    session_id = session_info['id']
                    system_prompt = session_info['system_prompt']
                    
                    # Сохраняем в state для следующих сообщений
                    await state.update_data(session_id=session_id, system_prompt=system_prompt)
                    await state.set_state(UserStates.waiting_for_message)
                    
                    logger.info(f"✅ Сессия восстановлена из БД: {session_id}")
                else:
                    logger.error(f"❌ Активная сессия не найдена в БД")
            
            if session_id:
                # Сохраняем распознанный текст в state
                await state.update_data(voice_recognized_text=recognized_text)
                await state.set_state(UserStates.voice_confirmation)
                
                # Показываем распознанный текст с кнопками выбора
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Отправить", callback_data="voice_send")],
                    [InlineKeyboardButton(text="✏️ Изменить текст", callback_data="voice_edit")],
                    [InlineKeyboardButton(text="🎤 Надиктовать заново", callback_data="voice_retry")]
                ])
                
                # Удаляем сообщение "Обрабатываю"
                try:
                    await processing_msg.delete()
                except:
                    pass
                
                # Показываем результат с кнопками
                await message.answer(
                    f"✅ Распознано:\n\n<i>{recognized_text}</i>\n\n"
                    f"Выберите действие:",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                
                logger.info(f"✅ Показаны кнопки подтверждения голосового сообщения")
            else:
                logger.warning(f"❌ Нет session_id в состоянии")
                await processing_msg.edit_text(
                    f"✅ Распознано:\n\n{recognized_text}\n\n"
                    f"Сессия не найдена. Напишите /start"
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка в процессе обработки голоса: {e}")
            logger.exception("Полный стек ошибки:")
            if processing_msg:
                await processing_msg.edit_text("❌ Ошибка обработки. Попробуйте написать текстом.")
            else:
                await message.answer("❌ Ошибка обработки. Попробуйте написать текстом.")
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ошибка обработки голоса: {e}")
        logger.exception("Полный стек критической ошибки:")
        try:
            if processing_msg:
                await processing_msg.edit_text("❌ Ошибка распознавания. Попробуйте написать текстом.")
            else:
                await message.answer("❌ Ошибка распознавания. Попробуйте написать текстом.")
        except:
            pass

async def user_start_handler(message: Message, state: FSMContext):
    """Обработчик /start для обычных пользователей"""
    supabase_client = get_global_var('supabase_client')
    prompt_loader = get_global_var('prompt_loader')
    from ..core.bot_utils import parse_utm_from_start_param
    
    try:
        # 0. ПОЛУЧАЕМ UTM ДАННЫЕ
        start_param = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else None
        
        # Логируем входящий start параметр
        # Пример поддерживаемого формата: @https://t.me/bot?start=utmSource-vk_utmCampaign-summer2025 не более 64 символов после strat=
        
        logger.info(f"📥 Получен start параметр: '{start_param}'")
    
        utm_data = {}
        if start_param:
            # Парсим UTM данные
            utm_data = parse_utm_from_start_param(start_param)
            
            # Подробное логирование UTM
            logger.info(f"📊 UTM данные для пользователя {message.from_user.id}:")
            if utm_data:
                for key, value in utm_data.items():
                    logger.info(f"   • {key}: {value}")
                logger.info(f"✅ UTM данные успешно распознаны")
            else:
                logger.warning(f"⚠️ UTM данные не найдены в параметре: '{start_param}'")
        else:
            logger.info("ℹ️ Start параметр отсутствует (обычный /start)")
        
        # 1. ЯВНО ОЧИЩАЕМ СОСТОЯНИЕ FSM
        await state.clear()
        logger.info(f"🔄 Состояние FSM очищено для пользователя {message.from_user.id}")
        
        # 2. ЗАГРУЖАЕМ ПРОМПТЫ
        logger.info(f"Загрузка промптов для пользователя {message.from_user.id}")
        system_prompt = await prompt_loader.load_system_prompt()
        
        # Загружаем приветственное сообщение
        welcome_message = await prompt_loader.load_welcome_message()
        
        # 3. ПОЛУЧАЕМ ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
        user_data = {
            'telegram_id': message.from_user.id,
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
            'language_code': message.from_user.language_code,
            'source': utm_data.get('utm_source'),
            'medium': utm_data.get('utm_medium'),
            'campaign': utm_data.get('utm_campaign'),
            'content': utm_data.get('utm_content'),
            'term': utm_data.get('utm_term'),
            'segment': utm_data.get('segment')
        }
        
        # 4. СОЗДАЕМ НОВУЮ СЕССИЮ (автоматически закроет активные)
        # Добавляем UTM данные в метаданные пользователя
        if utm_data:
            user_data['metadata'] = {'utm_data': utm_data}
            logger.info(f"📈 UTM данные добавлены в метаданные пользователя")
            
        session_id = await supabase_client.create_chat_session(user_data, system_prompt)
        logger.info(f"✅ Создана новая сессия {session_id} для пользователя {message.from_user.id}")
        
        # 5. УСТАНАВЛИВАЕМ НОВОЕ СОСТОЯНИЕ
        await state.update_data(session_id=session_id, system_prompt=system_prompt)
        await state.set_state(UserStates.waiting_for_message)
        
        # 6. ОТПРАВЛЯЕМ ПРИВЕТСТВЕННОЕ СООБЩЕНИЕ
        try:
            await send_message(message, welcome_message)
            logger.info(f"Приветственное сообщение отправлено пользователю {message.from_user.id}")
        except Exception as e:
            if "Forbidden: bot was blocked by the user" in str(e):
                logger.warning(f"🚫 Бот заблокирован пользователем {message.from_user.id}")
                return
            else:
                logger.error(f"❌ Ошибка отправки приветственного сообщения: {e}")
                raise
        
        # 7. ЕСЛИ ЕСТЬ ФАЙЛ ОТПРАВЛЯЕМ ВМЕСТЕ С ПОДПИСЬЮ
        logging.info(f"📎 Попытка отправки приветственного файла для сессии {session_id}")
        caption = await send_welcome_file(message)
        
        # 8. СОХРАНЯЕМ ПРИВЕТСТВЕННОЕ СООБЩЕНИЕ В БД
        if caption:
            logging.info(f"📄 Добавление подписи к файлу в приветственное сообщение для сессии {session_id}")
            welcome_message = f"{welcome_message}\n\nПодпись к файлу:\n\n{caption}"
        else:
            logging.info(f"📄 Приветственный файл отправлен без подписи для сессии {session_id}")
            
        logging.info(f"💾 Сохранение приветственного сообщения в БД для сессии {session_id}")
        
        await supabase_client.add_message(
            session_id=session_id,
            role='assistant',
            content=welcome_message,
            message_type='text'
        )
        
        logging.info(f"✅ Приветственное сообщение успешно сохранено в БД для сессии {session_id}")
        
        # ВЫЗЫВАЕМ ПОЛЬЗОВАТЕЛЬСКИЕ ОБРАБОТЧИКИ on_start
        start_handlers = get_global_var('start_handlers')
        if start_handlers:
            logger.info(f"🔔 Вызов {len(start_handlers)} пользовательских обработчиков on_start")
            for handler in start_handlers:
                try:
                    await handler(
                        user_id=message.from_user.id,
                        session_id=session_id,
                        message=message,
                        state=state
                    )
                    logger.info(f"✅ Обработчик on_start '{handler.__name__}' выполнен успешно")
                except Exception as handler_error:
                    logger.error(f"❌ Ошибка в обработчике on_start '{handler.__name__}': {handler_error}")
                    # Продолжаем выполнение остальных обработчиков
        
    except Exception as e:
        logger.error(f"Ошибка при обработке user /start: {e}")
        await send_message(message, "Произошла ошибка при инициализации. Попробуйте позже.")

@router.message(StateFilter(None))
async def message_without_state_handler(message: Message, state: FSMContext):
    """Обработчик сообщений без состояния (после перезапуска бота)"""
    admin_manager = get_global_var('admin_manager')
    supabase_client = get_global_var('supabase_client')
    conversation_manager = get_global_var('conversation_manager')
    from ..admin.admin_logic import AdminStates
    from ..utils.debug_routing import debug_user_state
    
    try:
        await debug_user_state(message, state, "NO_STATE")
        
        # СНАЧАЛА проверяем диалог с админом
        conversation = await conversation_manager.is_user_in_admin_chat(message.from_user.id)
        
        if conversation:
            logger.info(f"✅ Найден диалог с админом {conversation['admin_id']}, устанавливаем состояние admin_chat")
            
            # Устанавливаем состояние admin_chat
            await state.set_state(UserStates.admin_chat)
            await state.update_data(admin_conversation=conversation)
            
            # Сразу пересылаем сообщение админу
            await conversation_manager.forward_message_to_admin(message, conversation)
            
            # Сохраняем сообщение в БД
            session_info = await supabase_client.get_active_session(message.from_user.id)
            if session_info:
                await supabase_client.add_message(
                    session_id=session_info['id'],
                    role='user',
                    content=message.text,
                    message_type='text',
                    metadata={'in_admin_chat': True, 'admin_id': conversation['admin_id']}
                )
            
            return
        
        # Проверяем, админ ли это
        if admin_manager.is_admin(message.from_user.id):
            logger.info(f"👑 Админ в режиме администратора без состояния")
            await state.set_state(AdminStates.admin_mode)
            await message.answer("👑 Режим администратора\nИспользуйте /start для панели управления")
            return
        
        logger.info(f"👤 Обычный пользователь без состояния, ищем активную сессию")
        
        # Ищем активную сессию в БД
        session_info = await supabase_client.get_active_session(message.from_user.id)
        
        if session_info:
            logger.info(f"📝 Восстанавливаем сессию {session_info['id']}")
            # Восстанавливаем сессию из БД
            session_id = session_info['id']
            system_prompt = session_info['system_prompt']
            
            # Сохраняем в состояние
            await state.update_data(session_id=session_id, system_prompt=system_prompt)
            await state.set_state(UserStates.waiting_for_message)
            
            logger.info(f"✅ Сессия восстановлена, обрабатываем сообщение")
            
            # Теперь обрабатываем сообщение как обычно
            await process_user_message(message, state, session_id, system_prompt)
        else:
            logger.info(f"❌ Нет активной сессии, просим написать /start")
            await send_message(message, "Привет! Напишите /start для начала диалога.")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке сообщения без состояния: {e}")
        await send_message(message, "Произошла ошибка. Попробуйте написать /start для начала диалога.")

# ✅ ИСПРАВЛЕНИЕ: Обработчик admin_chat должен быть ПЕРВЫМ и более приоритетным
@router.message(StateFilter(UserStates.admin_chat))
async def user_in_admin_chat_handler(message: Message, state: FSMContext):
    """ПРИОРИТЕТНЫЙ обработчик сообщений пользователей в диалоге с админом"""
    conversation_manager = get_global_var('conversation_manager')
    supabase_client = get_global_var('supabase_client')
    from ..utils.debug_routing import debug_user_state
    
    await debug_user_state(message, state, "ADMIN_CHAT_HANDLER")
    
    user_id = message.from_user.id
    logger.info(f"🎯 ADMIN_CHAT HANDLER: сообщение от {user_id}: '{message.text}'")
    
    # Проверяем, есть ли еще активный диалог
    conversation = await conversation_manager.is_user_in_admin_chat(user_id)
    
    if conversation:
        logger.info(f"✅ Диалог активен, пересылаем админу {conversation['admin_id']}")
        
        try:
            # Сохраняем сообщение в БД
            session_info = await supabase_client.get_active_session(user_id)
            if session_info:
                await supabase_client.add_message(
                    session_id=session_info['id'],
                    role='user',
                    content=message.text,
                    message_type='text',
                    metadata={'in_admin_chat': True, 'admin_id': conversation['admin_id']}
                )
                logger.info(f"💾 Сообщение сохранено в БД")
            
            # Пересылаем админу
            await conversation_manager.forward_message_to_admin(message, conversation)
            logger.info(f"📤 Сообщение переслано админу")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки admin_chat: {e}")
            await message.answer("Произошла ошибка. Попробуйте позже.")
    else:
        logger.info(f"💬 Диалог завершен, возвращаем к обычному режиму")
        # Диалог завершен, возвращаем к обычному режиму
        await state.set_state(UserStates.waiting_for_message)
        
        # Обрабатываем как обычное сообщение
        data = await state.get_data()
        session_id = data.get('session_id')
        system_prompt = data.get('system_prompt')
        
        if session_id:
            await process_user_message(message, state, session_id, system_prompt)
        else:
            await send_message(message, "Сессия не найдена. Пожалуйста, напишите /start")

# Обработчик для обычных сообщений (НЕ в admin_chat)
@router.message(StateFilter(UserStates.waiting_for_message), ~F.text.startswith('/'))
async def user_message_handler(message: Message, state: FSMContext):
    """Обработчик сообщений пользователей (исключая admin_chat)"""
    conversation_manager = get_global_var('conversation_manager')
    from ..utils.debug_routing import debug_user_state
    
    try:
        await debug_user_state(message, state, "USER_MESSAGE_HANDLER")
        
        # ✅ ВАЖНО: Сначала проверяем диалог с админом
        conversation = await conversation_manager.is_user_in_admin_chat(message.from_user.id)
        
        if conversation:
            logger.info(f"⚠️ НЕОЖИДАННО: пользователь в waiting_for_message, но есть диалог с админом!")
            logger.info(f"🔄 Принудительно переключаем в admin_chat состояние")
            
            # Принудительно переключаем состояние
            await state.set_state(UserStates.admin_chat)
            await state.update_data(admin_conversation=conversation)
            
            # Обрабатываем сообщение как admin_chat
            await user_in_admin_chat_handler(message, state)
            return
        
        logger.info(f"🤖 Обычный диалог с ботом")
        data = await state.get_data()
        session_id = data.get('session_id')
        system_prompt = data.get('system_prompt')
        
        if not session_id:
            logger.warning(f"❌ Нет session_id в состоянии")
            await send_message(message, "Сессия не найдена. Пожалуйста, напишите /start")
            return
        
        logger.info(f"📝 Обрабатываем сообщение с session_id: {session_id}")
        await process_user_message(message, state, session_id, system_prompt)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке сообщения пользователя: {e}")
        await send_message(message, "Произошла ошибка. Попробуйте еще раз или напишите /start для перезапуска.")
        
@router.callback_query(F.data == "voice_send")
async def voice_send_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Отправить' для голосового сообщения"""
    try:
        data = await state.get_data()
        recognized_text = data.get('voice_recognized_text')
        session_id = data.get('session_id')
        system_prompt = data.get('system_prompt')
        
        if not recognized_text or not session_id:
            await callback.answer("❌ Ошибка: текст не найден", show_alert=True)
            return
        
        # Удаляем сообщение с кнопками
        await callback.message.delete()
        
        # Обрабатываем текст сразу без промежуточного сообщения
        await process_voice_message(callback.message, state, session_id, system_prompt, recognized_text)
        
        # Возвращаем в обычное состояние
        await state.set_state(UserStates.waiting_for_message)
        await state.update_data(voice_recognized_text=None)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки голосового: {e}")
        await callback.answer("❌ Ошибка обработки", show_alert=True)

@router.callback_query(F.data == "voice_edit")
async def voice_edit_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Изменить текст' для голосового сообщения"""
    try:
        data = await state.get_data()
        recognized_text = data.get('voice_recognized_text')
        
        if not recognized_text:
            await callback.answer("❌ Ошибка: текст не найден", show_alert=True)
            return
        
        # Переводим в режим редактирования
        await state.set_state(UserStates.voice_editing)
        
        # Показываем текст для редактирования (обычный формат)
        await callback.message.edit_text(
            f"✏️ Отредактируйте распознанный текст:\n\n"
            f"{recognized_text}\n\n"
            f"Напишите исправленный текст:"
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка редактирования: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

@router.callback_query(F.data == "voice_retry")
async def voice_retry_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Надиктовать заново' для голосового сообщения"""
    try:
        # Удаляем сообщение с кнопками
        await callback.message.delete()
        
        # Возвращаем в обычное состояние
        await state.set_state(UserStates.waiting_for_message)
        await state.update_data(voice_recognized_text=None)
        
        # Просим отправить заново
        await callback.message.answer("🎤 Отправьте голосовое сообщение заново")
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"❌ Ошибка повтора: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

@router.message(StateFilter(UserStates.voice_editing))
async def voice_edit_text_handler(message: Message, state: FSMContext):
    """Обработчик получения отредактированного текста"""
    try:
        edited_text = message.text.strip()
        
        if not edited_text:
            await message.answer("⚠️ Текст не может быть пустым. Напишите текст:")
            return
        
        # Получаем данные сессии
        data = await state.get_data()
        session_id = data.get('session_id')
        system_prompt = data.get('system_prompt')
        
        if not session_id:
            await message.answer("❌ Сессия не найдена. Напишите /start")
            return
        
        # Обрабатываем отредактированный текст сразу
        await process_voice_message(message, state, session_id, system_prompt, edited_text)
        
        # Возвращаем в обычное состояние
        await state.set_state(UserStates.waiting_for_message)
        await state.update_data(voice_recognized_text=None)
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки отредактированного текста: {e}")
        await message.answer("❌ Ошибка обработки. Попробуйте еще раз или напишите /start")

@router.message()
async def catch_all_handler(message: Message, state: FSMContext):
    """Перехватчик всех необработанных сообщений"""
    admin_manager = get_global_var('admin_manager')
    from ..utils.debug_routing import debug_user_state
    
    await debug_user_state(message, state, "CATCH_ALL")
    
    current_state = await state.get_state()
    logger.warning(f"⚠️ НЕОБРАБОТАННОЕ СООБЩЕНИЕ от {message.from_user.id}: '{message.text}', состояние: {current_state}")
    
    # Проверяем, админ ли это
    if admin_manager.is_admin(message.from_user.id):
        logger.info(f"👑 Необработанное сообщение админа")
        await message.answer("Команда не распознана. Используйте /help для справки.")
    else:
        logger.info(f"👤 Необработанное сообщение пользователя")
        await message.answer("Не понимаю. Напишите /start для начала диалога.")

async def process_user_message(message: Message, state: FSMContext, session_id: str, system_prompt: str):
    """Общая функция для обработки сообщений пользователя"""
    supabase_client = get_global_var('supabase_client')
    openai_client = get_global_var('openai_client')
    config = get_global_var('config')
    bot = get_global_var('bot')
    prompt_loader = get_global_var('prompt_loader')
    message_hooks = get_global_var('message_hooks') or {}
    from datetime import datetime
    import pytz  # Добавляем импорт для работы с временными зонами
    
    try:
        # ============ ХУК 1: ВАЛИДАЦИЯ СООБЩЕНИЯ ============
        validators = message_hooks.get('validators', [])
        for validator in validators:
            try:
                user_message = message.text
                message_obj = message
                
                should_continue = await validator(user_message, message_obj)
                if not should_continue:
                    logger.info(f"⛔ Валидатор '{validator.__name__}' прервал обработку")
                    return  # Прерываем обработку
            except Exception as e:
                logger.error(f"❌ Ошибка в валидаторе '{validator.__name__}': {e}")
        
        # Сохраняем сообщение пользователя
        await supabase_client.add_message(
            session_id=session_id,
            role='user',
            content=message.text,
            message_type='text'
        )
        logger.info(f"✅ Сообщение пользователя сохранено в БД")
        
        # Получаем историю сообщений
        chat_history = await supabase_client.get_chat_history(session_id, limit=config.MAX_CONTEXT_MESSAGES)
        logger.info(f"📚 Загружена история: {len(chat_history)} сообщений")
        
        # ДОБАВЛЯЕМ ПОЛУЧЕНИЕ ТЕКУЩЕГО ВРЕМЕНИ
        moscow_tz = pytz.timezone('Europe/Moscow')
        current_time = datetime.now(moscow_tz)
        time_info = current_time.strftime('%H:%M, %d.%m.%Y, %A')
        
        # Базовый системный промпт с временем
        system_prompt_with_time = f"""
{system_prompt}

ТЕКУЩЕЕ ВРЕМЯ: {time_info} (московское время)
"""
        
        # ============ ХУК 2: ОБОГАЩЕНИЕ ПРОМПТА ============
        prompt_enrichers = message_hooks.get('prompt_enrichers', [])
        for enricher in prompt_enrichers:
            try:
                system_prompt_with_time = await enricher(
                    system_prompt_with_time,
                    message.from_user.id
                )
                logger.info(f"✅ Промпт обогащен '{enricher.__name__}'")
            except Exception as e:
                logger.error(f"❌ Ошибка в обогатителе промпта '{enricher.__name__}': {e}")
        
        # Формируем контекст для OpenAI с обновленным системным промптом
        messages = [{"role": "system", "content": system_prompt_with_time}]
        
        for msg in chat_history[-config.MAX_CONTEXT_MESSAGES:]:  # Ограничиваем контекст
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # Добавляем финальные инструкции в конец контекста
        final_instructions = await prompt_loader.load_final_instructions()
        if final_instructions:
            messages.append({"role": "system", "content": final_instructions})
            logger.info(f"🎯 Добавлены финальные инструкции ({len(final_instructions)} символов)")
        
        # ============ ХУК 3: ОБОГАЩЕНИЕ КОНТЕКСТА ============
        context_enrichers = message_hooks.get('context_enrichers', [])
        for enricher in context_enrichers:
            try:
                messages = await enricher(
                    messages
                )
                logger.info(f"✅ Контекст обогащен '{enricher.__name__}'")
            except Exception as e:
                logger.error(f"❌ Ошибка в обогатителе контекста '{enricher.__name__}': {e}")
        
        logger.info(f"📝 Контекст сформирован: {len(messages)} сообщений (включая время: {time_info})")
        
        await bot.send_chat_action(message.chat.id, "typing")
        
        start_time = time.time()
        ai_response = await openai_client.get_completion(messages)
        processing_time = int((time.time() - start_time) * 1000)

        logger.info(f"🤖 OpenAI ответил за {processing_time}мс, длина ответа: {len(ai_response) if ai_response else 0}")
        
        # ИСПРАВЛЕННАЯ ЛОГИКА: инициализируем все переменные заранее
        tokens_used = 0
        ai_metadata = {}
        response_text = ""

        # Проверяем ответ
        if not ai_response or not ai_response.strip():
            logger.warning(f"❌ OpenAI вернул пустой/пробельный ответ!")
            
            # Проверяем, были ли использованы токены при пустом ответе
            if hasattr(openai_client, 'last_completion_tokens'):
                logger.warning(f"⚠️ Токены использованы ({openai_client.last_completion_tokens}), но ответ пустой")
            
            # Устанавливаем fallback ответ
            fallback_message = "Извините, произошла техническая ошибка. Попробуйте переформулировать вопрос или напишите /start для перезапуска."
            ai_response = fallback_message
            response_text = fallback_message
            tokens_used = 0
            ai_metadata = {}
            
        else:
            logger.info(f"📤 Сырой ответ OpenAI получен, обрабатываем...")
            
            tokens_used = openai_client.estimate_tokens(ai_response)
            
            # Парсим JSON метаданные
            response_text, ai_metadata = parse_ai_response(ai_response)

            logger.info(f"🔍 После парсинга JSON:")
            logger.info(f"   📝 Текст ответа: {len(response_text)} символов: '{response_text[:100]}...'")
            logger.info(f"   📊 Метаданные: {ai_metadata}")

            # Более надежная проверка
            if not ai_metadata:
                logger.info("ℹ️ JSON не найден, используем исходный ответ")
                response_text = ai_response
                ai_metadata = {}
            elif not response_text.strip():
                logger.warning("⚠️ JSON найден, но текст ответа пустой! Используем исходный ответ.")
                response_text = ai_response

            logger.info(f"✅ Финальный текст для отправки: {len(response_text)} символов")
        
        # ============ ХУК 4: ОБРАБОТКА ОТВЕТА ============
        response_processors = message_hooks.get('response_processors', [])
        for processor in response_processors:
            try:
                response_text, ai_metadata = await processor(
                    response_text,
                    ai_metadata,
                    message.from_user.id
                )
                logger.info(f"✅ Ответ обработан '{processor.__name__}'")
            except Exception as e:
                logger.error(f"❌ Ошибка в обработчике ответа '{processor.__name__}': {e}")
        
        # Обновляем этап сессии и качество лида
        if ai_metadata:
            logger.info("🔍 Анализ метаданных от ИИ:")
            
            # Вывод информации об этапе
            stage = ai_metadata.get('этап')
            if stage:
                logger.info(f"   📈 Этап диалога: {stage}")
            
            # Вывод информации о качестве лида
            quality = ai_metadata.get('качество')
            if quality is not None:
                quality_emoji = "⭐" * min(quality, 5)  # Максимум 5 звезд
                logger.info(f"   {quality_emoji} Качество лида: {quality}/10")
            
            # Обновляем в базе данных
            if stage or quality is not None:
                await supabase_client.update_session_stage(session_id, stage, quality)
                logger.info(f"   ✅ Этап и качество обновлены в БД")
            
            # Обрабатываем события
            events = ai_metadata.get('события', [])
            if events:
                logger.info(f"\n🔔 События в диалоге ({len(events)}):")
                for idx, event in enumerate(events, 1):
                    event_type = event.get('тип', 'неизвестно')
                    event_info = event.get('инфо', 'нет информации')

                    # Подбираем эмодзи для разных типов событий
                    event_emoji = {
                        'телефон': '📱',
                        'email': '📧',
                        'встреча': '📅',
                        'заказ': '🛍️',
                        'вопрос': '❓',
                        'консультация': '💬',
                        'жалоба': '⚠️',
                        'отзыв': '💭'
                    }.get(event_type.lower(), '📌')

                    logger.info(f"   {idx}. {event_emoji} {event_type}: {event_info}")

                # Обрабатываем события в системе
                await process_events(session_id, events, message.from_user.id)
                logger.info("   ✅ События обработаны")
        
        # Обрабатываем файлы и каталоги
        files_list = ai_metadata.get('файлы', [])
        directories_list = ai_metadata.get('каталоги', [])
        
        # Форматируем информацию о файлах
        if files_list:
            logger.info("📎 Найденные файлы:")
            for idx, file in enumerate(files_list, 1):
                logger.info(f"   {idx}. 📄 {file}")
        
        # Форматируем информацию о каталогах
        if directories_list:
            logger.info("📂 Найденные каталоги:")
            for idx, directory in enumerate(directories_list, 1):
                logger.info(f"   {idx}. 📁 {directory}")
        
        # Добавляем информацию в текст ответа
        if files_list or directories_list:
            files_info = []
            if files_list:
                files_str = "\n".join(f"• {file}" for file in files_list)
                files_info.append(f"\n\n📎 Доступные файлы:\n{files_str}")
            
            if directories_list:
                dirs_str = "\n".join(f"• {directory}" for directory in directories_list)
                files_info.append(f"\n\n📂 Доступные каталоги:\n{dirs_str}")
            
        else:
            logger.info("📎 Файлы и каталоги не указаны")

        # Сохраняем ответ ассистента с метаданными
        try:
            await supabase_client.add_message(
                session_id=session_id,
                role='assistant',
                content=response_text,
                message_type='text',
                tokens_used=tokens_used,
                processing_time_ms=processing_time,
                ai_metadata=ai_metadata
            )
            logger.info(f"✅ Ответ ассистента сохранен в БД")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения ответа в БД: {e}")

        # Определяем финальный ответ для пользователя
        if config.DEBUG_MODE:
            # В режиме отладки показываем полный ответ с JSON
            final_response = ai_response
            logger.info(f"🐛 Режим отладки: отправляем полный ответ с JSON")
        else:
            # В обычном режиме показываем только текст без JSON
            final_response = response_text
            logger.info(f"👤 Обычный режим: отправляем очищенный текст")

        # Проверяем, что есть что отправлять
        if not final_response or not final_response.strip():
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Финальный ответ пуст!")
            final_response = "Извините, произошла ошибка при формировании ответа. Попробуйте еще раз."

        logger.info(f"📱 Отправляем пользователю: {len(final_response)} символов")
        
        # ============ ХУК 5: ФИЛЬТРЫ ОТПРАВКИ ============
        send_filters = message_hooks.get('send_filters', [])
        for filter_func in send_filters:
            try:
                should_send = await filter_func(message.from_user.id)
                if should_send:
                    # True = блокируем (для совместимости с should_block_ai_response)
                    logger.info(f"⛔ Фильтр '{filter_func.__name__}' заблокировал отправку (вернул True)")
                    return  # Не отправляем
            except Exception as e:
                logger.error(f"❌ Ошибка в фильтре отправки '{filter_func.__name__}': {e}")
        
        # Отправляем ответ пользователю
        try:
            await send_message(message, final_response, files_list=files_list, directories_list=directories_list)
            logger.info(f"✅ Ответ успешно отправлен пользователю {message.from_user.id}")
        except Exception as e:
            logger.error(f"❌ ОШИБКА ОТПРАВКИ СООБЩЕНИЯ: {e}")
            # Пытаемся отправить простое сообщение об ошибке
            try:
                await message.answer("Произошла ошибка при отправке ответа. Попробуйте еще раз.")
            except Exception as e2:
                logger.error(f"❌ Не удалось отправить даже сообщение об ошибке: {e2}")
                
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА в process_user_message: {e}")
        logger.exception("Полный стек ошибки:")
        try:
            await message.answer("Произошла критическая ошибка. Попробуйте написать /start для перезапуска.")
        except:
            logger.error(f"❌ Не удалось отправить сообщение об критической ошибке")
            
async def process_voice_message(message: Message, state: FSMContext, session_id: str, system_prompt: str, recognized_text: str):
    """Обработка распознанного голосового сообщения"""
    supabase_client = get_global_var('supabase_client')
    openai_client = get_global_var('openai_client')
    config = get_global_var('config')
    bot = get_global_var('bot')
    prompt_loader = get_global_var('prompt_loader')
    
    from datetime import datetime
    import pytz
    
    try:
        # Сохраняем распознанное сообщение как текст пользователя
        await supabase_client.add_message(
            session_id=session_id,
            role='user',
            content=recognized_text,
            message_type='text',  # БД разрешает только 'text'
            metadata={'original_type': 'voice', 'duration': message.voice.duration if message.voice else 0}
        )
        logger.info(f"✅ Распознанное сообщение сохранено в БД")
        
        # Получаем историю сообщений
        chat_history = await supabase_client.get_chat_history(session_id, limit=config.MAX_CONTEXT_MESSAGES)
        logger.info(f"📚 Загружена история: {len(chat_history)} сообщений")
        
        # Добавляем текущее время
        moscow_tz = pytz.timezone('Europe/Moscow')
        current_time = datetime.now(moscow_tz)
        time_info = current_time.strftime('%H:%M, %d.%m.%Y, %A')
        
        system_prompt_with_time = f"""
{system_prompt}

ТЕКУЩЕЕ ВРЕМЯ: {time_info} (московское время)
"""
        
        # Формируем контекст для OpenAI
        messages = [{"role": "system", "content": system_prompt_with_time}]
        
        for msg in chat_history[-config.MAX_CONTEXT_MESSAGES:]:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # Добавляем финальные инструкции
        final_instructions = await prompt_loader.load_final_instructions()
        if final_instructions:
            messages.append({"role": "system", "content": final_instructions})
            logger.info(f"🎯 Добавлены финальные инструкции")
        
        logger.info(f"📝 Контекст сформирован: {len(messages)} сообщений")
        
        await bot.send_chat_action(message.chat.id, "typing")
        
        import time
        start_time = time.time()
        ai_response = await openai_client.get_completion(messages)
        processing_time = int((time.time() - start_time) * 1000)

        logger.info(f"🤖 OpenAI ответил за {processing_time}мс")
        
        tokens_used = 0
        ai_metadata = {}
        response_text = ""

        if not ai_response or not ai_response.strip():
            logger.warning(f"❌ OpenAI вернул пустой ответ!")
            fallback_message = "Извините, произошла техническая ошибка. Попробуйте еще раз."
            ai_response = fallback_message
            response_text = fallback_message
            tokens_used = 0
            ai_metadata = {}
        else:
            tokens_used = openai_client.estimate_tokens(ai_response)
            response_text, ai_metadata = parse_ai_response(ai_response)

            if not ai_metadata:
                response_text = ai_response
                ai_metadata = {}
            elif not response_text.strip():
                logger.warning("⚠️ JSON найден, но текст пустой! Используем исходный ответ.")
                response_text = ai_response

            # Обновляем этап и качество
            if ai_metadata:
                stage = ai_metadata.get('этап')
                quality = ai_metadata.get('качество')
                
                if stage or quality is not None:
                    await supabase_client.update_session_stage(session_id, stage, quality)
                
                # Обрабатываем события
                events = ai_metadata.get('события', [])
                if events:
                    await process_events(session_id, events, message.from_user.id)

        # Сохраняем ответ ассистента
        await supabase_client.add_message(
            session_id=session_id,
            role='assistant',
            content=response_text,
            message_type='text',
            tokens_used=tokens_used,
            processing_time_ms=processing_time,
            ai_metadata=ai_metadata
        )

        # Определяем финальный ответ
        final_response = ai_response if config.DEBUG_MODE else response_text
        
        if not final_response or not final_response.strip():
            final_response = "Извините, произошла ошибка при формировании ответа. Попробуйте еще раз."

        # Обрабатываем файлы
        files_list = ai_metadata.get('файлы', [])
        directories_list = ai_metadata.get('каталоги', [])
        
        # Отправляем ответ пользователю
        await send_message(message, final_response, files_list=files_list, directories_list=directories_list)
        logger.info(f"✅ Ответ отправлен пользователю {message.from_user.id}")
                
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА в process_voice_message: {e}")
        logger.exception("Полный стек ошибки:")
        try:
            await message.answer("Произошла критическая ошибка. Попробуйте написать /start")
        except:
            pass