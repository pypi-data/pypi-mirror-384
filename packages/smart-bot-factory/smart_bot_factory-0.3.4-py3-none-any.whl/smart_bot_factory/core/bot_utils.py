import asyncio
import json
import logging
import re
from datetime import datetime
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    FSInputFile,
)
from aiogram.utils.media_group import MediaGroupBuilder

from pathlib import Path
from ..core.decorators import (
    execute_scheduled_task_from_event,
    execute_global_handler_from_event,
)

# Функция для получения глобальных переменных
def get_global_var(var_name):
    """Получает глобальную переменную из модуля bot_utils"""
    import sys
    current_module = sys.modules[__name__]
    return getattr(current_module, var_name, None)

logger = logging.getLogger(__name__)


# Создаем роутер для общих команд
utils_router = Router()

def setup_utils_handlers(dp):
    """Настройка обработчиков утилит"""
    dp.include_router(utils_router)

def parse_ai_response(ai_response: str) -> tuple[str, dict]:
    """Исправленная функция парсинга JSON из конца ответа ИИ"""
    try:
        # Метод 1: Ищем последнюю позицию, где начинается JSON с "этап"
        last_etap_pos = ai_response.rfind('"этап"')
        if last_etap_pos == -1:
            logger.debug("JSON без ключа 'этап' не найден")
            return ai_response, {}
        
        # Ищем открывающую скобку перед "этап"
        json_start = -1
        for i in range(last_etap_pos, -1, -1):
            if ai_response[i] == '{':
                json_start = i
                break
        
        if json_start == -1:
            logger.debug("Открывающая скобка перед 'этап' не найдена")
            return ai_response, {}
        
        # Теперь найдем соответствующую закрывающую скобку
        brace_count = 0
        json_end = -1
        
        for i in range(json_start, len(ai_response)):
            char = ai_response[i]
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i
                    break
        
        if json_end == -1:
            logger.debug("Соответствующая закрывающая скобка не найдена")
            return ai_response, {}
        
        # Извлекаем JSON и текст ответа
        json_str = ai_response[json_start:json_end + 1]
        response_text = ai_response[:json_start].strip()
        
        # 🆕 ИСПРАВЛЕНИЕ: Если response_text пустой, используем исходный ответ БЕЗ JSON
        if not response_text:
            logger.debug("Текст ответа пустой после удаления JSON, используем исходный ответ без JSON части")
            # Берем все кроме JSON части
            remaining_text = ai_response[json_end + 1:].strip()
            if remaining_text:
                response_text = remaining_text
            else:
                # Если и после JSON ничего нет, значит ответ был только JSON
                response_text = "Ответ обработан системой."
                logger.warning("Ответ ИИ содержал только JSON без текста")
        
        try:
            metadata = json.loads(json_str)
            logger.debug(f"JSON успешно распарсен: {metadata}")
            return response_text, metadata
        except json.JSONDecodeError as e:
            logger.warning(f"Ошибка парсинга JSON: {e}")
            logger.debug(f"JSON строка: {json_str}")
            return parse_ai_response_method2(ai_response)
            
    except Exception as e:
        logger.warning(f"Ошибка парсинга JSON от ИИ: {e}")
        return parse_ai_response_method2(ai_response)

def parse_ai_response_method2(ai_response: str) -> tuple[str, dict]:
    """Резервный метод парсинга JSON - поиск по строкам (переименован для соответствия тестам)"""
    try:
        logger.debug("Используем резервный метод парсинга JSON")
        
        lines = ai_response.strip().split('\n')
        
        # Ищем строку с "этап"
        etap_line = -1
        for i, line in enumerate(lines):
            if '"этап"' in line:
                etap_line = i
                break
        
        if etap_line == -1:
            return ai_response, {}
        
        # Ищем начало JSON (строку с { перед этап)
        json_start_line = -1
        for i in range(etap_line, -1, -1):
            if lines[i].strip().startswith('{'):
                json_start_line = i
                break
        
        if json_start_line == -1:
            return ai_response, {}
        
        # Ищем конец JSON (балансируем скобки)
        brace_count = 0
        json_end_line = -1
        
        for i in range(json_start_line, len(lines)):
            line = lines[i]
            for char in line:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end_line = i
                        break
            if json_end_line != -1:
                break
        
        if json_end_line == -1:
            return ai_response, {}
        
        # Собираем JSON
        json_lines = lines[json_start_line:json_end_line + 1]
        json_str = '\n'.join(json_lines)
        
        # Собираем текст ответа
        response_lines = lines[:json_start_line]
        response_text = '\n'.join(response_lines).strip()
        
        try:
            metadata = json.loads(json_str)
            logger.debug(f"JSON распарсен резервным методом: {metadata}")
            return response_text, metadata
        except json.JSONDecodeError as e:
            logger.warning(f"Резервный метод: ошибка JSON: {e}")
            return ai_response, {}
            
    except Exception as e:
        logger.warning(f"Ошибка резервного метода: {e}")
        return ai_response, {}

async def process_events(session_id: str, events: list, user_id: int):
    """Обрабатывает события из ответа ИИ"""
    
    # Проверяем кастомный процессор
    custom_processor = get_global_var('custom_event_processor')
    
    if custom_processor:
        # Используем кастомную функцию обработки событий
        logger.info(f"🔄 Используется кастомная обработка событий: {custom_processor.__name__}")
        await custom_processor(session_id, events, user_id)
        return
    
    # Стандартная обработка
    supabase_client = get_global_var('supabase_client')
    
    for event in events:
        try:
            event_type = event.get('тип', '')
            event_info = event.get('инфо', '')
            
            if not event_type:
                logger.warning(f"⚠️ Событие без типа: {event}")
                continue
            
            logger.info(f"\n🔔 Обработка события:")
            logger.info(f"   📝 Тип: {event_type}")
            logger.info(f"   📄 Данные: {event_info}")
            
            # Определяем категорию события и сохраняем в БД
            event_id = None
            should_execute_immediately = False
            should_notify = False
            
            try:
                # Проверяем зарегистрированные обработчики через роутер-менеджер
                from ..core.decorators import get_router_manager, _event_handlers, _scheduled_tasks, _global_handlers
                
                # Получаем обработчики из роутеров или fallback к старым декораторам
                router_manager = get_router_manager()
                if router_manager:
                    event_handlers = router_manager.get_event_handlers()
                    scheduled_tasks = router_manager.get_scheduled_tasks()
                    global_handlers = router_manager.get_global_handlers()
                    logger.debug(f"🔍 RouterManager найден: {len(event_handlers)} событий, {len(scheduled_tasks)} задач, {len(global_handlers)} глобальных обработчиков")
                    logger.debug(f"🔍 Доступные scheduled_tasks: {list(scheduled_tasks.keys())}")
                else:
                    event_handlers = _event_handlers
                    scheduled_tasks = _scheduled_tasks
                    global_handlers = _global_handlers
                    logger.warning("⚠️ RouterManager не найден, используем старые декораторы")
                    logger.debug(f"🔍 Старые scheduled_tasks: {list(scheduled_tasks.keys())}")
                
                # Сначала пробуем как обычное событие
                if event_type in event_handlers:
                    from ..core.decorators import execute_event_handler, update_event_result
                    
                    event_handler_info = event_handlers.get(event_type, {})
                    once_only = event_handler_info.get('once_only', True)
                    
                    logger.info(f"   🔍 Обработчик '{event_type}': once_only={once_only}")
                    
                    # Если once_only=True - проверяем в БД наличие выполненных событий
                    if once_only:
                        check_query = supabase_client.client.table('scheduled_events')\
                            .select('id, status, session_id')\
                            .eq('event_type', event_type)\
                            .eq('user_id', user_id)\
                            .eq('status', 'completed')
                        
                        # НЕ фильтруем по session_id - проверяем ВСЕ выполненные события пользователя
                        # if session_id:
                        #     check_query = check_query.eq('session_id', session_id)
                        
                        existing = check_query.execute()
                        
                        logger.info(f"   🔍 Проверка БД: найдено {len(existing.data) if existing.data else 0} выполненных событий '{event_type}' для user_id={user_id}")
                        
                        if existing.data:
                            logger.info(f"   🔄 Событие '{event_type}' уже выполнялось для пользователя {user_id}, пропускаем (once_only=True)")
                            logger.info(f"   📋 Найденные события: {existing.data}")
                            continue
                    
                    # Немедленно выполняем событие
                    logger.info(f"   🎯 Немедленно выполняем user_event: '{event_type}'")
                    
                    try:
                        # Выполняем СНАЧАЛА
                        result = await execute_event_handler(event_type, user_id, event_info)
                        
                        # Сохраняем в БД УЖЕ со статусом completed (избегаем дублирования)
                        event_record = {
                            'event_type': event_type,
                            'event_category': 'user_event',
                            'user_id': user_id,
                            'event_data': event_info,
                            'scheduled_at': None,
                            'status': 'completed',  # Сразу completed!
                            'session_id': session_id,
                            'executed_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                            'result_data': __import__('json').dumps(result, ensure_ascii=False) if result else None
                        }
                        response = supabase_client.client.table('scheduled_events').insert(event_record).execute()
                        event_id = response.data[0]['id']
                        
                        should_notify = event_handler_info.get('notify', False)
                        should_execute_immediately = True
                        
                        logger.info(f"   ✅ Событие {event_id} выполнено и сохранено как completed")
                        
                    except Exception as e:
                        logger.error(f"   ❌ Ошибка выполнения события: {e}")
                        # Сохраняем ошибку в БД
                        event_record = {
                            'event_type': event_type,
                            'event_category': 'user_event',
                            'user_id': user_id,
                            'event_data': event_info,
                            'scheduled_at': None,
                            'status': 'failed',
                            'session_id': session_id,
                            'last_error': str(e)
                        }
                        supabase_client.client.table('scheduled_events').insert(event_record).execute()
                        raise
                
                # Если не user_event, пробуем как запланированную задачу
                elif event_type in scheduled_tasks:
                    try:
                        # Используем новую логику - время берется из декоратора
                        logger.info(f"   ⏰ Планируем scheduled_task: '{event_type}' с данными: '{event_info}'")
                        result = await execute_scheduled_task_from_event(user_id, event_type, event_info, session_id)
                        event_id = result.get('event_id', 'unknown')
                        should_notify = result.get('notify', False)
                        logger.info(f"   💾 Задача запланирована: {event_id}")
                        
                    except Exception as e:
                        if "once_only=True" in str(e):
                            logger.info(f"   🔄 Задача '{event_type}' уже запланирована, пропускаем")
                            continue
                        else:
                            logger.error(f"   ❌ Ошибка планирования scheduled_task '{event_type}': {e}")
                            continue
                
                # Если не scheduled_task, пробуем как глобальный обработчик
                elif event_type in global_handlers:
                    try:
                        # Используем новую логику - время берется из декоратора
                        logger.info(f"   🌍 Планируем global_handler: '{event_type}' с данными: '{event_info}'")
                        result = await execute_global_handler_from_event(event_type, event_info)
                        event_id = result.get('event_id', 'unknown')
                        should_notify = result.get('notify', False)
                        logger.info(f"   💾 Глобальное событие запланировано: {event_id}")
                        
                    except Exception as e:
                        if "once_only=True" in str(e):
                            logger.info(f"   🔄 Глобальное событие '{event_type}' уже запланировано, пропускаем")
                            continue
                        else:
                            logger.error(f"   ❌ Ошибка планирования global_handler '{event_type}': {e}")
                            continue
                
                else:
                    logger.warning(f"   ⚠️ Обработчик '{event_type}' не найден среди зарегистрированных")
                    logger.debug(f"   🔍 Доступные обработчики:")
                    logger.debug(f"      - event_handlers: {list(event_handlers.keys())}")
                    logger.debug(f"      - scheduled_tasks: {list(scheduled_tasks.keys())}")
                    logger.debug(f"      - global_handlers: {list(global_handlers.keys())}")
                    
            except ValueError as e:
                logger.warning(f"   ⚠️ Обработчик/задача не найдены: {e}")
            except Exception as e:
                logger.error(f"   ❌ Ошибка в обработчике/задаче: {e}")
                logger.exception("   Стек ошибки:")
            
            # Уведомляем админов только если result.notify = True
            if should_notify:
                await notify_admins_about_event(user_id, event)
                logger.info(f"   ✅ Админы уведомлены")
            else:
                logger.info(f"   🔕 Уведомления админам отключены для '{event_type}'")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки события {event}: {e}")
            logger.exception("Стек ошибки:")

async def notify_admins_about_event(user_id: int, event: dict):
    """Отправляем уведомление админам о событии с явным указанием ID пользователя"""
    supabase_client = get_global_var('supabase_client')
    admin_manager = get_global_var('admin_manager')
    bot = get_global_var('bot')
    
    event_type = event.get('тип', '')
    event_info = event.get('инфо', '')
    
    if not event_type:
        return
    
    # Получаем информацию о пользователе для username
    try:
        user_response = supabase_client.client.table('sales_users').select(
            'first_name', 'last_name', 'username'
        ).eq('telegram_id', user_id).execute()
        
        user_info = user_response.data[0] if user_response.data else {}
        
        # Формируем имя пользователя (без ID)
        name_parts = []
        if user_info.get('first_name'):
            name_parts.append(user_info['first_name'])
        if user_info.get('last_name'):
            name_parts.append(user_info['last_name'])
        
        user_name = " ".join(name_parts) if name_parts else "Без имени"
        
        # Формируем отображение пользователя с ОБЯЗАТЕЛЬНЫМ ID
        if user_info.get('username'):
            user_display = f"{user_name} (@{user_info['username']})"
        else:
            user_display = user_name
            
    except Exception as e:
        logger.error(f"Ошибка получения информации о пользователе {user_id}: {e}")
        user_display = "Пользователь"
    
    emoji_map = {
        'телефон': '📱',
        'консультация': '💬',
        'покупка': '💰',
        'отказ': '❌'
    }
    
    emoji = emoji_map.get(event_type, '🔔')
    
    # 🆕 ИСПРАВЛЕНИЕ: ID всегда отображается отдельной строкой для удобства копирования
    notification = f"""
{emoji} {event_type.upper()}!
👤 {user_display}
🆔 ID: {user_id}
📝 {event_info}
🕐 {datetime.now().strftime('%H:%M')}
"""
    
    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Чат", callback_data=f"admin_chat_{user_id}"),
            InlineKeyboardButton(text="📋 История", callback_data=f"admin_history_{user_id}")
        ]
    ])
    
    try:
        # Отправляем всем активным админам
        active_admins = await admin_manager.get_active_admins()
        for admin_id in active_admins:
            try:
                await bot.send_message(admin_id, notification.strip(), reply_markup=keyboard)
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления админам: {e}")
        
async def send_message(message: Message, text: str, files_list: list = [], directories_list: list = [], **kwargs):
    """Вспомогательная функция для отправки сообщений с настройкой parse_mode"""
    config = get_global_var('config')
    
    logger.info(f"📤 send_message вызвана:")
    logger.info(f"   👤 Пользователь: {message.from_user.id}")
    logger.info(f"   📝 Длина текста: {len(text)} символов")
    logger.info(f"   🐛 Debug режим: {config.DEBUG_MODE}")
    
    try:
        parse_mode = config.MESSAGE_PARSE_MODE if config.MESSAGE_PARSE_MODE != 'None' else None
        logger.info(f"   🔧 Parse mode: {parse_mode}")
        
        # Получаем user_id и импортируем supabase_client
        user_id = message.from_user.id
        supabase_client = get_global_var('supabase_client')
        
        # Текст уже готов, используем как есть
        final_text = text
        
        # Работаем с переданными файлами и каталогами
        logger.info(f"   📦 Передано файлов: {files_list}")
        logger.info(f"   📂 Передано каталогов: {directories_list}")
        
        # Получаем список уже отправленных файлов и каталогов
        sent_files = await supabase_client.get_sent_files(user_id)
        sent_directories = await supabase_client.get_sent_directories(user_id)
        
        logger.info(f"   📋 Уже отправлено файлов: {sent_files}")
        logger.info(f"   📋 Уже отправлено каталогов: {sent_directories}")
        
        # Фильтруем файлы и каталоги, которые уже отправлялись
        actual_files_list = [f for f in files_list if f not in sent_files]
        actual_directories_list = [d for d in directories_list if str(d) not in sent_directories]
        
        logger.info(f"   🆕 После фильтрации файлов: {actual_files_list}")
        logger.info(f"   🆕 После фильтрации каталогов: {actual_directories_list}")
                    
        
        # Проверяем, что есть что отправлять
        if not final_text or not final_text.strip():
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: final_text пуст после обработки!")
            logger.error(f"   Исходный text: '{text[:200]}...'")
            final_text = "Ошибка формирования ответа. Попробуйте еще раз."
        
        logger.info(f"📱 Подготовка сообщения: {len(final_text)} символов")
        logger.info(f"   📦 Файлов для обработки: {actual_files_list}")
        logger.info(f"   📂 Каталогов для обработки: {actual_directories_list}")
        
        # Проверяем наличие файлов для отправки
        if actual_files_list or actual_directories_list:
            # Функция определения типа медиа по расширению
            def get_media_type(file_path: str) -> str:
                ext = Path(file_path).suffix.lower()
                if ext in {'.jpg', '.jpeg', '.png'}:
                    return 'photo'
                elif ext in {'.mp4', '.mov'}:
                    return 'video'
                else:
                    return 'document'
            
            # Создаем списки для разных типов файлов
            video_files = []  # для видео
            photo_files = []  # для фото
            document_files = []  # для документов
            
            # Функция обработки файла
            def process_file(file_path: Path, source: str = ""):
                if file_path.is_file():
                    media_type = get_media_type(str(file_path))
                    if media_type == 'video':
                        video_files.append(file_path)
                        logger.info(f"   🎥 Добавлено видео{f' из {source}' if source else ''}: {file_path.name}")
                    elif media_type == 'photo':
                        photo_files.append(file_path)
                        logger.info(f"   📸 Добавлено фото{f' из {source}' if source else ''}: {file_path.name}")
                    else:
                        document_files.append(file_path)
                        logger.info(f"   📄 Добавлен документ{f' из {source}' if source else ''}: {file_path.name}")
                else:
                    logger.warning(f"   ⚠️ Файл не найден: {file_path}")
            
            # Обрабатываем прямые файлы
            for file_name in actual_files_list:
                try:
                    process_file(Path(f"files/{file_name}"))
                except Exception as e:
                    logger.error(f"   ❌ Ошибка обработки файла {file_name}: {e}")
            
            # Обрабатываем файлы из каталогов
            for dir_name in actual_directories_list:
                dir_name = Path(dir_name)
                try:
                    if dir_name.is_dir():
                        for file_path in dir_name.iterdir():
                            try:
                                process_file(file_path, dir_name)
                            except Exception as e:
                                logger.error(f"   ❌ Ошибка обработки файла {file_path}: {e}")
                    else:
                        logger.warning(f"   ⚠️ Каталог не найден: {dir_name}")
                except Exception as e:
                    logger.error(f"   ❌ Ошибка обработки каталога {dir_name}: {e}")
            
            # Списки для отслеживания реально отправленных файлов
            sent_files_to_save = []
            sent_dirs_to_save = []
            
            # 1. Отправляем видео (если есть)
            if video_files:
                video_group = MediaGroupBuilder()
                for file_path in video_files:
                    video_group.add_video(media=FSInputFile(str(file_path)))
                
                videos = video_group.build()
                if videos:
                    await message.answer_media_group(media=videos)
                    logger.info(f"   ✅ Отправлено {len(videos)} видео")
            
            # 2. Отправляем фото (если есть)
            if photo_files:
                photo_group = MediaGroupBuilder()
                for file_path in photo_files:
                    photo_group.add_photo(media=FSInputFile(str(file_path)))
                
                photos = photo_group.build()
                if photos:
                    await message.answer_media_group(media=photos)
                    logger.info(f"   ✅ Отправлено {len(photos)} фото")
            
            # 3. Отправляем текст
            result = await message.answer(final_text, parse_mode=parse_mode)
            logger.info(f"   ✅ Отправлен текст сообщения")
            
            # 4. Отправляем документы (если есть)
            if document_files:
                doc_group = MediaGroupBuilder()
                for file_path in document_files:
                    doc_group.add_document(media=FSInputFile(str(file_path)))
                
                docs = doc_group.build()
                if docs:
                    await message.answer_media_group(media=docs)
                    logger.info(f"   ✅ Отправлено {len(docs)} документов")
            
            # 5. Собираем список реально отправленных файлов и каталогов
            # Если были отправлены файлы из actual_files_list - сохраняем их
            if video_files or photo_files or document_files:
                # Сохраняем прямые файлы из actual_files_list (если отправлены)
                sent_files_to_save.extend(actual_files_list)
                logger.info(f"   📝 Добавляем в список для сохранения файлы: {actual_files_list}")
                # Сохраняем каталоги из actual_directories_list (если отправлены файлы из них)
                sent_dirs_to_save.extend([str(d) for d in actual_directories_list])
                logger.info(f"   📝 Добавляем в список для сохранения каталоги: {actual_directories_list}")
            
            # 6. Обновляем информацию в БД
            if sent_files_to_save or sent_dirs_to_save:
                try:
                    if sent_files_to_save:
                        logger.info(f"   💾 Сохраняем файлы в БД: {sent_files_to_save}")
                        await supabase_client.add_sent_files(user_id, sent_files_to_save)
                    if sent_dirs_to_save:
                        logger.info(f"   💾 Сохраняем каталоги в БД: {sent_dirs_to_save}")
                        await supabase_client.add_sent_directories(user_id, sent_dirs_to_save)
                    logger.info(f"   ✅ Обновлена информация о отправленных файлах в БД")
                except Exception as e:
                    logger.error(f"   ❌ Ошибка обновления информации о файлах в БД: {e}")
            else:
                logger.info(f"   ℹ️ Нет новых файлов для сохранения в БД")
            
            return result
        else:
            # Если нет файлов, отправляем просто текст
                logger.warning("   ⚠️ Нет файлов для отправки, отправляем как текст")
                result = await message.answer(final_text, parse_mode=parse_mode, **kwargs)
                return result
        
    except Exception as e:
        # Проверяем, является ли ошибка блокировкой бота
        if "Forbidden: bot was blocked by the user" in str(e):
            logger.warning(f"🚫 Бот заблокирован пользователем {user_id}")
            return None
        elif "TelegramForbiddenError" in str(type(e).__name__):
            logger.warning(f"🚫 Бот заблокирован пользователем {user_id}")
            return None
        
        logger.error(f"❌ ОШИБКА в send_message: {e}")
        logger.exception("Полный стек ошибки send_message:")
        
        # Пытаемся отправить простое сообщение без форматирования
        try:
            fallback_text = "Произошла ошибка при отправке ответа. Попробуйте еще раз."
            result = await message.answer(fallback_text)
            logger.info(f"✅ Запасное сообщение отправлено")
            return result
        except Exception as e2:
            # Проверяем и здесь блокировку бота
            if "Forbidden: bot was blocked by the user" in str(e2):
                logger.warning(f"🚫 Бот заблокирован пользователем {user_id} (fallback)")
                return None
            elif "TelegramForbiddenError" in str(type(e2).__name__):
                logger.warning(f"🚫 Бот заблокирован пользователем {user_id} (fallback)")
                return None
            
            logger.error(f"❌ Даже запасное сообщение не отправилось: {e2}")
            raise
        
async def cleanup_expired_conversations():
    """Периодическая очистка просроченных диалогов"""
    conversation_manager = get_global_var('conversation_manager')
    
    while True:
        try:
            await asyncio.sleep(300)  # каждые 5 минут
            await conversation_manager.cleanup_expired_conversations()
        except Exception as e:
            logger.error(f"Ошибка очистки просроченных диалогов: {e}")

# 🆕 Вспомогательные функции для приветственного файла

async def get_welcome_file_path() -> str | None:
    """Возвращает путь к PDF файлу из папки WELCOME_FILE_DIR из конфига.

    Источник настроек: configs/<bot_id>/.env (переменная WELCOME_FILE_DIR)
    Рабочая директория уже установлена запускалкой на configs/<bot_id>.
    
    Returns:
        str | None: Путь к PDF файлу или None, если файл не найден
    """
    config = get_global_var('config') 
    try:
        folder_value = config.WELCOME_FILE_DIR
        if not folder_value:
            return None

        folder = Path(folder_value)
        if not folder.exists():
            logger.info(f"Директория приветственных файлов не существует: {folder_value}")
            return None
        
        if not folder.is_dir():
            logger.info(f"Путь не является директорией: {folder_value}")
            return None

        # Ищем первый PDF файл в директории
        for path in folder.iterdir():
            if path.is_file() and path.suffix.lower() == '.pdf':
                return str(path)
        
        logger.info(f"PDF файл не найден в директории: {folder_value}")
        return None
        
    except Exception as e:
        logger.error(f"Ошибка при поиске приветственного файла: {e}")
        return None

async def get_welcome_msg_path() -> str | None:
    """Возвращает путь к файлу welcome_file_msg.txt из той же директории, где находится PDF файл.
    
    Returns:
        str | None: Путь к файлу с подписью или None, если файл не найден
    """
    try:
        pdf_path = await get_welcome_file_path()
        if not pdf_path:
            return None
            
        msg_path = str(Path(pdf_path).parent / 'welcome_file_msg.txt')
        if not Path(msg_path).is_file():
            logger.info(f"Файл подписи не найден: {msg_path}")
            return None
            
        return msg_path
        
    except Exception as e:
        logger.error(f"Ошибка при поиске файла подписи: {e}")
        return None

async def send_welcome_file(message: Message) -> str:
    """
    Отправляет приветственный файл с подписью из файла welcome_file_msg.txt.
    Если файл подписи не найден, используется пустая подпись.
    
    Returns:
         str: текст подписи
    """
    try:
        config = get_global_var('config')

        file_path = await get_welcome_file_path()
        if not file_path:
            return ""

        # Получаем путь к файлу с подписью и читаем его
        caption = ""
        msg_path = await get_welcome_msg_path()
        if msg_path:
            try:
                with open(msg_path, 'r', encoding='utf-8') as f:
                    caption = f.read().strip()
                    logger.info(f"Подпись загружена из файла: {msg_path}")
            except Exception as e:
                logger.error(f"Ошибка при чтении файла подписи {msg_path}: {e}")

        parse_mode = config.MESSAGE_PARSE_MODE
        document = FSInputFile(file_path)
        
        await message.answer_document(document=document, caption=caption, parse_mode=parse_mode)
    
        logger.info(f"Приветственный файл отправлен: {file_path}")
        return caption
    except Exception as e:
        logger.error(f"Ошибка при отправке приветственного файла: {e}")
        return ""

# Общие команды

@utils_router.message(Command("help"))
async def help_handler(message: Message):
    """Справка"""
    admin_manager = get_global_var('admin_manager')
    prompt_loader = get_global_var('prompt_loader')
    
    try:
        # Разная справка для админов и пользователей
        if admin_manager.is_admin(message.from_user.id):
            if admin_manager.is_in_admin_mode(message.from_user.id):
                help_text = """
👑 **Справка для администратора**

**Команды:**
• `/стат` - статистика воронки и событий
• `/история <user_id>` - история пользователя
• `/чат <user_id>` - начать диалог с пользователем
• `/чаты` - показать активные диалоги
• `/стоп` - завершить текущий диалог
• `/админ` - переключиться в режим пользователя

**Особенности:**
• Все сообщения пользователей к админу пересылаются
• Ваши сообщения отправляются пользователю как от бота
• Диалоги автоматически завершаются через 30 минут
"""
                await message.answer(help_text, parse_mode='Markdown')
                return
        
        # Обычная справка для пользователей
        help_text = await prompt_loader.load_help_message()
        await send_message(message, help_text)
        
    except Exception as e:
        logger.error(f"Ошибка загрузки справки: {e}")
        # Fallback справка
        await send_message(message, "🤖 Ваш помощник готов к работе! Напишите /start для начала диалога.")

@utils_router.message(Command("status"))
async def status_handler(message: Message):
    """Проверка статуса системы"""
    openai_client = get_global_var('openai_client')
    prompt_loader = get_global_var('prompt_loader')
    admin_manager = get_global_var('admin_manager')
    config = get_global_var('config')
    
    try:
        # Проверяем OpenAI
        openai_status = await openai_client.check_api_health()
        
        # Проверяем промпты
        prompts_status = await prompt_loader.validate_prompts()
        
        # Статистика для админов
        if admin_manager.is_admin(message.from_user.id):
            admin_stats = admin_manager.get_stats()
            
            status_message = f"""
🔧 **Статус системы:**

OpenAI API: {'✅' if openai_status else '❌'}
Промпты: {'✅ ' + str(sum(prompts_status.values())) + '/' + str(len(prompts_status)) + ' загружено' if any(prompts_status.values()) else '❌'}
База данных: ✅ (соединение активно)

👑 **Админы:** {admin_stats['active_admins']}/{admin_stats['total_admins']} активны
🐛 **Режим отладки:** {'Включен' if config.DEBUG_MODE else 'Выключен'}

Все системы работают нормально!
            """
        else:
            status_message = f"""
🔧 **Статус системы:**

OpenAI API: {'✅' if openai_status else '❌'}
Промпты: {'✅ ' + str(sum(prompts_status.values())) + '/' + str(len(prompts_status)) + ' загружено' if any(prompts_status.values()) else '❌'}
База данных: ✅ (соединение активно)

Все системы работают нормально!
            """
        
        await send_message(message, status_message)
        
    except Exception as e:
        logger.error(f"Ошибка проверки статуса: {e}")
        await send_message(message, "❌ Ошибка при проверке статуса системы")
        
        
def parse_utm_from_start_param(start_param: str) -> dict:
    """Парсит UTM-метки и сегмент из start параметра в формате source-vk_campaign-summer2025_seg-premium
    
    Args:
        start_param: строка вида 'source-vk_campaign-summer2025_seg-premium' или полная ссылка
        
    Returns:
        dict: {'utm_source': 'vk', 'utm_campaign': 'summer2025', 'segment': 'premium'}
        
    Examples:
        >>> parse_utm_from_start_param('source-vk_campaign-summer2025_seg-premium')
        {'utm_source': 'vk', 'utm_campaign': 'summer2025', 'segment': 'premium'}
        
        >>> parse_utm_from_start_param('https://t.me/bot?start=source-vk_campaign-summer2025_seg-vip')
        {'utm_source': 'vk', 'utm_campaign': 'summer2025', 'segment': 'vip'}
    """
    import re
    from urllib.parse import unquote
    
    utm_data = {}
    
    try:
        # Если это полная ссылка, извлекаем start параметр
        if 't.me/' in start_param or 'https://' in start_param:
            match = re.search(r'[?&]start=([^&]+)', start_param)
            if match:
                start_param = unquote(match.group(1))
            else:
                return {}
        
        # Парсим новый формат: source-vk_campaign-summer2025_seg-premium
        # Поддерживает как комбинированные параметры, так и одиночные (например, только seg-prem)
        if '-' in start_param:
            # Разделяем по _ (если есть несколько параметров) или используем весь параметр
            parts = start_param.split('_') if '_' in start_param else [start_param]
            
            for part in parts:
                if '-' in part:
                    key, value = part.split('-', 1)
                    # Преобразуем source/medium/campaign/content/term в utm_*
                    if key in ['source', 'medium', 'campaign', 'content', 'term']:
                        key = 'utm_' + key
                        utm_data[key] = value
                    # Обрабатываем seg как segment
                    elif key == 'seg':
                        utm_data['segment'] = value
            
    except Exception as e:
        print(f"Ошибка парсинга UTM параметров: {e}")
        
    return utm_data