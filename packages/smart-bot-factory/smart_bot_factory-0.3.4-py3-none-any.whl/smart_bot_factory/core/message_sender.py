"""
Функции для отправки сообщений через ИИ и от человека
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import pytz

logger = logging.getLogger(__name__)

async def send_message_by_ai(
    user_id: int, 
    message_text: str, 
    session_id: str = None
) -> Dict[str, Any]:
    """
    Отправляет сообщение пользователю через ИИ (копирует логику process_user_message)
    
    Args:
        user_id: ID пользователя в Telegram
        message_text: Текст сообщения для обработки ИИ
        session_id: ID сессии чата (если не указан, будет использована активная сессия)
        
    Returns:
        Результат отправки
    """
    try:
        # Импортируем необходимые компоненты
        from .bot_utils import parse_ai_response, process_events

        # Получаем компоненты из глобального контекста
        from ..handlers.handlers import get_global_var
        bot = get_global_var('bot')
        supabase_client = get_global_var('supabase_client')
        openai_client = get_global_var('openai_client')
        config = get_global_var('config')
        prompt_loader = get_global_var('prompt_loader')
        
        # Если session_id не указан, получаем активную сессию пользователя
        if not session_id:
            session_info = await supabase_client.get_active_session(user_id)
            if not session_info:
                return {
                    "status": "error",
                    "error": "Активная сессия не найдена",
                    "user_id": user_id
                }
            session_id = session_info['id']
        
        # Загружаем системный промпт
        try:
            system_prompt = await prompt_loader.load_system_prompt()
            logger.info(f"✅ Системный промпт загружен ({len(system_prompt)} символов)")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки системного промпта: {e}")
            return {
                "status": "error",
                "error": "Не удалось загрузить системный промпт",
                "user_id": user_id
            }
        
        # Сохраняем сообщение пользователя в БД
        await supabase_client.add_message(
            session_id=session_id,
            role='user',
            content=message_text,
            message_type='text'
        )
        logger.info(f"✅ Сообщение пользователя сохранено в БД")
        
        # Получаем историю сообщений
        chat_history = await supabase_client.get_chat_history(session_id, limit=config.MAX_CONTEXT_MESSAGES)
        logger.info(f"📚 Загружена история: {len(chat_history)} сообщений")
        
        # Добавляем текущее время
        moscow_tz = pytz.timezone('Europe/Moscow')
        current_time = datetime.now(moscow_tz)
        time_info = current_time.strftime('%H:%M, %d.%m.%Y, %A')
        
        # Модифицируем системный промпт, добавляя время
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
        
        # Отправляем действие "печатает"
        await bot.send_chat_action(user_id, "typing")
        
        # Получаем ответ от ИИ
        start_time = time.time()
        ai_response = await openai_client.get_completion(messages)
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"🤖 OpenAI ответил за {processing_time}мс")
        
        # Обрабатываем ответ
        tokens_used = 0
        ai_metadata = {}
        response_text = ""
        
        if not ai_response or not ai_response.strip():
            logger.warning(f"❌ OpenAI вернул пустой ответ!")
            fallback_message = "Извините, произошла техническая ошибка. Попробуйте переформулировать вопрос."
            ai_response = fallback_message
            response_text = fallback_message
        else:
            tokens_used = openai_client.estimate_tokens(ai_response)
            response_text, ai_metadata = parse_ai_response(ai_response)
            
            if not ai_metadata:
                response_text = ai_response
                ai_metadata = {}
            elif not response_text.strip():
                response_text = ai_response
        
        # Обновляем этап сессии и качество лида
        if ai_metadata:
            stage = ai_metadata.get('этап')
            quality = ai_metadata.get('качество')
            
            if stage or quality is not None:
                await supabase_client.update_session_stage(session_id, stage, quality)
                logger.info(f"✅ Этап и качество обновлены в БД")
            
            # Обрабатываем события
            events = ai_metadata.get('события', [])
            if events:
                logger.info(f"🔔 Обрабатываем {len(events)} событий")
                await process_events(session_id, events, user_id)
        
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
        if config.DEBUG_MODE:
            final_response = ai_response
        else:
            final_response = response_text
        
        # Отправляем ответ пользователю напрямую через бота
        await bot.send_message(
            chat_id=user_id,
            text=final_response
        )
        
        return {
            "status": "success",
            "user_id": user_id,
            "response_text": response_text,
            "tokens_used": tokens_used,
            "processing_time_ms": processing_time,
            "events_processed": len(events) if events else 0
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка в send_message_by_ai: {e}")
        return {
            "status": "error",
            "error": str(e),
            "user_id": user_id
        }

async def send_message_by_human(
    user_id: int, 
    message_text: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Отправляет сообщение пользователю от имени человека (готовый текст)
    
    Args:
        user_id: ID пользователя в Telegram
        message_text: Готовый текст сообщения
        session_id: ID сессии (опционально, для сохранения в БД)
        
    Returns:
        Результат отправки
    """
    try:
        # Импортируем необходимые компоненты
        from ..handlers.handlers import get_global_var
        bot = get_global_var('bot')
        supabase_client = get_global_var('supabase_client')
        
        # Отправляем сообщение пользователю
        message = await bot.send_message(
            chat_id=user_id,
            text=message_text
        )
        
        # Если указана сессия, сохраняем сообщение в БД
        if session_id:
            await supabase_client.add_message(
                session_id=session_id,
                role='assistant',
                content=message_text,
                message_type='text',
                metadata={'sent_by_human': True}
            )
            logger.info(f"💾 Сообщение от человека сохранено в БД")
        
        return {
            "status": "success",
            "user_id": user_id,
            "message_id": message.message_id,
            "message_text": message_text,
            "saved_to_db": bool(session_id)
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка в send_message_by_human: {e}")
        return {
            "status": "error",
            "error": str(e),
            "user_id": user_id
        }

async def send_message_to_users_by_stage(
    stage: str,
    message_text: str,
    bot_id: str
) -> Dict[str, Any]:
    """
    Отправляет сообщение всем пользователям, находящимся на определенной стадии
    
    Args:
        stage: Стадия диалога (например, 'introduction', 'qualification', 'closing')
        message_text: Текст сообщения для отправки
        bot_id: ID бота (если не указан, используется текущий бот)
        
    Returns:
        Результат отправки с количеством отправленных сообщений
    """
    try:
        # Импортируем необходимые компоненты
        from ..handlers.handlers import get_global_var
        bot = get_global_var('bot')
        supabase_client = get_global_var('supabase_client')
        current_bot_id = get_global_var('config').BOT_ID if get_global_var('config') else bot_id
        
        if not current_bot_id:
            return {
                "status": "error",
                "error": "Не удалось определить bot_id"
            }
        
        logger.info(f"🔍 Ищем пользователей на стадии '{stage}' для бота '{current_bot_id}'")
        
        # Получаем последние сессии для каждого пользователя с нужной стадией
        # Сначала получаем все активные сессии с нужной стадией
        sessions_query = supabase_client.client.table('sales_chat_sessions').select(
            'user_id, id, current_stage, created_at'
        ).eq('status', 'active').eq('current_stage', stage)
        
        # Фильтруем по bot_id если указан
        if current_bot_id:
            sessions_query = sessions_query.eq('bot_id', current_bot_id)
        
        # Сортируем по дате создания (последние сначала)
        sessions_query = sessions_query.order('created_at', desc=True)
        
        sessions_data = sessions_query.execute()
        
        if not sessions_data.data:
            logger.info(f"📭 Пользователи на стадии '{stage}' не найдены")
            return {
                "status": "success",
                "stage": stage,
                "users_found": 0,
                "messages_sent": 0,
                "errors": []
            }
        
        # Выбираем уникальные user_id (берем только последнюю сессию для каждого пользователя)
        unique_users = {}
        for session in sessions_data.data:
            user_id = session['user_id']
            # Если пользователь еще не добавлен, добавляем его (так как сессии отсортированы по дате, первая будет самой последней)
            if user_id not in unique_users:
                unique_users[user_id] = {
                    'session_id': session['id'],
                    'current_stage': session['current_stage']
                }
        
        logger.info(f"👥 Найдено {len(unique_users)} уникальных пользователей на стадии '{stage}'")
        
        # Отправляем сообщения
        messages_sent = 0
        errors = []
        
        for user_id, user_data in unique_users.items():
            session_id = user_data['session_id']
            
            try:
                # Отправляем сообщение пользователю
                await bot.send_message(
                    chat_id=user_id,
                    text=message_text
                )
                
                # Сохраняем сообщение в БД
                await supabase_client.add_message(
                    session_id=session_id,
                    role='assistant',
                    content=message_text,
                    message_type='text',
                    metadata={
                        'sent_by_stage_broadcast': True,
                        'target_stage': stage,
                        'broadcast_timestamp': datetime.now().isoformat()
                    }
                )
                
                messages_sent += 1
                logger.info(f"✅ Сообщение отправлено пользователю {user_id} (стадия: {stage})")
                
            except Exception as e:
                error_msg = f"Ошибка отправки пользователю {user_id}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        result = {
            "status": "success",
            "stage": stage,
            "users_found": len(unique_users),
            "messages_sent": messages_sent,
            "errors": errors
        }
        
        logger.info(f"📊 Результат рассылки по стадии '{stage}': {messages_sent}/{len(unique_users)} сообщений отправлено")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка в send_message_to_users_by_stage: {e}")
        return {
            "status": "error",
            "error": str(e),
            "stage": stage
        }

async def get_users_by_stage_stats(
    bot_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Получает статистику пользователей по стадиям
    
    Args:
        bot_id: ID бота (если не указан, используется текущий бот)
        
    Returns:
        Статистика по стадиям с количеством пользователей
    """
    try:
        # Импортируем необходимые компоненты
        from ..handlers.handlers import get_global_var
        supabase_client = get_global_var('supabase_client')
        current_bot_id = get_global_var('config').BOT_ID if get_global_var('config') else bot_id
        
        if not current_bot_id:
            return {
                "status": "error",
                "error": "Не удалось определить bot_id"
            }
        
        logger.info(f"📊 Получаем статистику по стадиям для бота '{current_bot_id}'")
        
        # Получаем статистику по стадиям с user_id для подсчета уникальных пользователей
        stats_query = supabase_client.client.table('sales_chat_sessions').select(
            'user_id, current_stage, created_at'
        ).eq('status', 'active')
        
        # Фильтруем по bot_id если указан
        if current_bot_id:
            stats_query = stats_query.eq('bot_id', current_bot_id)
        
        # Сортируем по дате создания (последние сначала)
        stats_query = stats_query.order('created_at', desc=True)
        
        sessions_data = stats_query.execute()
        
        # Подсчитываем уникальных пользователей по стадиям (берем последнюю сессию каждого пользователя)
        user_stages = {}  # {user_id: stage}
        
        for session in sessions_data.data:
            user_id = session['user_id']
            stage = session['current_stage'] or 'unknown'
            
            # Если пользователь еще не добавлен, добавляем его стадию (первая встреченная - самая последняя)
            if user_id not in user_stages:
                user_stages[user_id] = stage
        
        # Подсчитываем количество пользователей по стадиям
        stage_stats = {}
        for stage in user_stages.values():
            stage_stats[stage] = stage_stats.get(stage, 0) + 1
        
        total_users = len(user_stages)
        
        # Сортируем по количеству пользователей (по убыванию)
        sorted_stages = sorted(stage_stats.items(), key=lambda x: x[1], reverse=True)
        
        result = {
            "status": "success",
            "bot_id": current_bot_id,
            "total_active_users": total_users,
            "stages": dict(sorted_stages),
            "stages_list": sorted_stages
        }
        
        logger.info(f"📊 Статистика по стадиям: {total_users} активных пользователей")
        for stage, count in sorted_stages:
            logger.info(f"   {stage}: {count} пользователей")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка в get_users_by_stage_stats: {e}")
        return {
            "status": "error",
            "error": str(e),
            "bot_id": bot_id
        }

async def send_message(
    message,
    text: str,
    supabase_client,
    files_list: list = [],
    directories_list: list = [],
    parse_mode: str = "Markdown",
    **kwargs
):
    """
    Пользовательская функция для отправки сообщений с файлами и кнопками
    
    Args:
        message: Message объект от aiogram
        text: Текст сообщения
        supabase_client: SupabaseClient для работы с БД
        files_list: Список файлов для отправки
        directories_list: Список каталогов (отправятся все файлы)
        parse_mode: Режим парсинга ('Markdown', 'HTML' или None)
        **kwargs: Дополнительные параметры (reply_markup и т.д.)
    
    Returns:
        Message объект отправленного сообщения или None
        
    Example:
        from smart_bot_factory.message import send_message
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Кнопка", callback_data="action")]
        ])
        
        await send_message(
            message=message,
            text="Привет!",
            supabase_client=supabase_client,
            files_list=["file.pdf"],
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    """
    from pathlib import Path
    from aiogram.types import FSInputFile
    from aiogram.utils.media_group import MediaGroupBuilder
    
    logger.info(f"📤 send_message вызвана:")
    logger.info(f"   👤 Пользователь: {message.from_user.id}")
    logger.info(f"   📝 Длина текста: {len(text)} символов")
    logger.info(f"   🔧 Parse mode: {parse_mode}")
    
    try:
        user_id = message.from_user.id
        
        # Устанавливаем parse_mode (None если передана строка 'None')
        actual_parse_mode = None if parse_mode == 'None' else parse_mode
        
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
            video_files = []
            photo_files = []
            document_files = []
            
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
            result = await message.answer(final_text, parse_mode=actual_parse_mode, **kwargs)
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
            if video_files or photo_files or document_files:
                sent_files_to_save.extend(actual_files_list)
                logger.info(f"   📝 Добавляем в список для сохранения файлы: {actual_files_list}")
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
            logger.info("   ⚠️ Нет файлов для отправки, отправляем как текст")
            result = await message.answer(final_text, parse_mode=actual_parse_mode, **kwargs)
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
            if "Forbidden: bot was blocked by the user" in str(e2):
                logger.warning(f"🚫 Бот заблокирован пользователем {user_id} (fallback)")
                return None
            elif "TelegramForbiddenError" in str(type(e2).__name__):
                logger.warning(f"🚫 Бот заблокирован пользователем {user_id} (fallback)")
                return None
            
            logger.error(f"❌ Даже запасное сообщение не отправилось: {e2}")
            raise
