# Обработчики для создания админских событий

import logging
import os
import shutil
from datetime import datetime
from dateutil.relativedelta import relativedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_media_group import media_group_handler
from ..aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
import pytz
import uuid
import json

TEMP_DIR = "temp_event_files"

def generate_file_id() -> str:
    """Генерирует уникальный ID для файла"""
    return f"file_{uuid.uuid4().hex}"

def ensure_temp_dir():
    """Создает временную папку если её нет"""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        logger.info(f"📁 Создана временная папка {TEMP_DIR}")

async def cleanup_temp_files(state: FSMContext = None):
    """Очистка временных файлов события"""
    # Удаляем все файлы из временной папки
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
            logger.info(f"🗑️ Удалена папка {TEMP_DIR}")
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении {TEMP_DIR}: {e}")
    
    # Очищаем информацию о файлах в состоянии
    if state:
        try:
            data = await state.get_data()
            if 'files' in data:
                data['files'] = []
                await state.set_data(data)
        except Exception as e:
            logger.error(f"❌ Ошибка при очистке состояния: {e}")

logger = logging.getLogger(__name__)

# Московская временная зона
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

# Импортируем состояния
from ..core.states import AdminStates

# Создаем роутер для админских событий
admin_events_router = Router()

def setup_admin_events_handlers(dp):
    """Настройка обработчиков админских событий"""
    dp.include_router(admin_events_router)

@admin_events_router.message(Command(commands=["создать_событие", "create_event"]))
async def create_event_start(message: Message, state: FSMContext):
    """Начало создания события"""
    from ..handlers.handlers import get_global_var
    admin_manager = get_global_var('admin_manager')
    
    if not admin_manager.is_admin(message.from_user.id):
        return
    
    await state.set_state(AdminStates.create_event_name)
    
    await message.answer(
        "📝 **Введите название события**\n\n"
        "💡 _По этому названию вы сможете:\n"
        "• Найти событие в списке\n"
        "• Отменить его при необходимости_",
        parse_mode='Markdown'
    )

@admin_events_router.message(AdminStates.create_event_name)
async def process_event_name(message: Message, state: FSMContext):
    """Обработка названия события"""
    from ..handlers.handlers import get_global_var
    
    event_name = message.text.strip()
    
    if not event_name:
        await message.answer("❌ Название не может быть пустым. Попробуйте еще раз:")
        return
    
    # Проверяем уникальность названия (только среди активных событий)
    supabase_client = get_global_var('supabase_client')
    name_exists = await supabase_client.check_event_name_exists(event_name)
    
    if name_exists:
        await message.answer(
            f"⚠️ **Событие с названием «{event_name}» уже существует и находится в статусе ожидания!**\n\n"
            f"Пожалуйста, выберите другое название или дождитесь выполнения/отмены существующего события.\n\n"
            f"💡 _Вы можете использовать это же название после завершения или отмены текущего события._",
            parse_mode='Markdown'
        )
        return
    
    # Сохраняем название
    await state.update_data(event_name=event_name)
    await state.set_state(AdminStates.create_event_date)
    
    # Показываем календарь для выбора даты
    calendar = SimpleCalendar(locale='ru', today_btn='Сегодня', cancel_btn='Отмена')
    # Ограничиваем выбор датами от вчера до +12 месяцев (чтобы сегодня был доступен)
    calendar.set_dates_range(datetime.now() + relativedelta(days=-1), datetime.now() + relativedelta(months=+12))
    calendar_markup = await calendar.start_calendar()
    
    await message.answer(
        f"✅ Название события: **{event_name}**\n\n"
        "📅 Выберите дату отправки:",
        reply_markup=calendar_markup,
        parse_mode='Markdown'
    )

@admin_events_router.callback_query(SimpleCalendarCallback.filter(), AdminStates.create_event_date)
async def process_event_date(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    """Обработка выбора даты"""
    calendar = SimpleCalendar(locale='ru', cancel_btn='Отмена', today_btn='Сегодня')
    
    # Ограничиваем выбор датами от вчера до +12 месяцев (чтобы сегодня был доступен)
    calendar.set_dates_range(datetime.now() + relativedelta(days=-1), datetime.now() + relativedelta(months=+12))
    selected, date = await calendar.process_selection(callback_query, callback_data)
    
    if selected == 'cancel':
        # Нажата кнопка "Отмена"
        await state.clear()
        await callback_query.message.edit_text(
            "❌ Создание события отменено",
            parse_mode='Markdown'
        )
    elif selected:
        # Дата выбрана успешно (True или обычный выбор)
        await state.update_data(event_date=date.strftime('%Y-%m-%d'))
        await state.set_state(AdminStates.create_event_time)
        
        await callback_query.message.edit_text(
            f"✅ Дата: **{date.strftime('%d.%m.%Y')}**\n\n"
            "⏰ Введите время отправки в формате ЧЧ:ММ\n"
            "_(Например: 14:30)_",
            parse_mode='Markdown'
        )
    # Если selected is False/None - это навигация по календарю, ничего не делаем
    # Календарь сам обновится при навигации

@admin_events_router.message(AdminStates.create_event_time)
async def process_event_time(message: Message, state: FSMContext):
    """Обработка времени события"""
    time_str = message.text.strip()
    
    # Валидация формата времени
    try:
        event_time = datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        await message.answer(
            "❌ Неверный формат времени. Используйте формат HH:MM\n"
            "_(Например: 14:30)_",
            parse_mode='Markdown'
        )
        return
    
    # Сохраняем время
    await state.update_data(event_time=time_str)
    await state.set_state(AdminStates.create_event_segment)
    
    # Получаем все доступные сегменты
    from ..handlers.handlers import get_global_var
    supabase_client = get_global_var('supabase_client')
    
    segments = await supabase_client.get_all_segments()
    
    # Создаем клавиатуру с сегментами
    keyboard = []
    
    # Большая кнопка "Отправить всем" на два столбца
    keyboard.append([
        InlineKeyboardButton(text="📢 Отправить всем", callback_data="segment:all")
    ])
    
    # Кнопки сегментов (по 2 в ряд)
    if segments:
        for i in range(0, len(segments), 2):
            row = []
            row.append(InlineKeyboardButton(
                text=f"👥 {segments[i]}", 
                callback_data=f"segment:{segments[i]}"
            ))
            if i + 1 < len(segments):
                row.append(InlineKeyboardButton(
                    text=f"👥 {segments[i+1]}", 
                    callback_data=f"segment:{segments[i+1]}"
                ))
            keyboard.append(row)
    
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    data = await state.get_data()
    await message.answer(
        f"✅ Время: **{time_str}**\n\n"
        f"👥 Выберите сегмент пользователей для отправки:\n"
        f"_(Найдено сегментов: {len(segments)})_",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@admin_events_router.callback_query(F.data.startswith("segment:"), AdminStates.create_event_segment)
async def process_event_segment(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора сегмента"""
    segment_data = callback_query.data.split(":", 1)[1]
    
    # segment_data = "all" или название сегмента
    segment_name = None if segment_data == "all" else segment_data
    segment_display = "Все пользователи" if segment_data == "all" else segment_data
    
    # Сохраняем сегмент
    await state.update_data(segment=segment_name, segment_display=segment_display)
    await state.set_state(AdminStates.create_event_message)
    
    await callback_query.message.edit_text(
        f"✅ Сегмент: **{segment_display}**\n\n"
        "💬 **Введите сообщение для пользователей**\n\n"
        "📸 _Вы можете прикрепить к сообщению **фото или видео** — они будут отправлены пользователям в том же порядке_\n\n"
        "📄 _Если нужно добавить **PDF или другие документы**, вы сможете это сделать на следующем шаге_",
        parse_mode='Markdown'
    )
    
@admin_events_router.message(AdminStates.create_event_message, F.media_group_id, F.content_type.in_({'photo', 'video'}))
@media_group_handler
async def handle_album(messages: list[Message], state: FSMContext):
    """Обработка альбома фотографий/видео"""
    if not messages:
        return
    
    # Берем текст из первого сообщения с подписью
    event_message = next((msg.caption for msg in messages if msg.caption), None)
    if not event_message:
        await messages[0].answer(
            "❌ **Добавьте подпись к альбому**\n\n"
            "💡 _Отправьте альбом заново с текстом сообщения в подписи к любой фотографии_",
            parse_mode='Markdown'
        )
        return
    
    # Сохраняем сообщение
    await state.update_data(event_message=event_message)
    
    # Показываем сообщение о начале загрузки
    await messages[0].answer(
        "📸 **Загружаю файлы...**\n\n"
        "💡 _Дождитесь загрузки всех файлов из альбома_",
        parse_mode='Markdown'
    )
    
    # Сохраняем все файлы
    from ..handlers.handlers import get_global_var
    bot = get_global_var('bot')
    ensure_temp_dir()
    
    data = await state.get_data()
    files = data.get('files', [])
    
    for i, message in enumerate(messages, 1):
        try:
            if message.photo:
                photo = message.photo[-1]
                file = await bot.get_file(photo.file_id)
                file_name = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.jpg"
                file_path = os.path.join(TEMP_DIR, file_name)
                await bot.download_file(file.file_path, file_path)
                
                files.append({
                    'type': 'photo',
                    'file_path': file_path,
                    'name': file_name,
                    'stage': 'with_message',
                    'has_caption': bool(message.caption),
                    'order': i  # Сохраняем порядок в альбоме
                })
                
            elif message.video:
                file = await bot.get_file(message.video.file_id)
                file_name = message.video.file_name or f"{message.video.file_id}.mp4"
                file_path = os.path.join(TEMP_DIR, file_name)
                await bot.download_file(file.file_path, file_path)
                
                files.append({
                    'type': 'video',
                    'file_path': file_path,
                    'name': file_name,
                    'stage': 'with_message',
                    'has_caption': bool(message.caption),
                    'order': i  # Сохраняем порядок в альбоме
                })
            
            # Показываем прогресс каждые 5 файлов
            if i % 5 == 0:
                await messages[0].answer(
                    f"📸 Загружено файлов: {i}/{len(messages)}",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки файла {i}: {e}")
            continue
    
    # Сохраняем файлы
    await state.update_data(files=files)
    
    # Переходим к следующему этапу
    await state.set_state(AdminStates.create_event_files)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Продолжить без файлов", callback_data="files:skip")]
    ])
    
    await messages[0].answer(
        f"✅ **Сообщение и {len(files)} файлов сохранены!**\n\n"
        "📎 **Дополнительные файлы**\n\n"
        "Теперь вы можете отправить:\n"
        "📄 PDF документы\n"
        "📁 Файлы любых форматов\n"
        "🎥 Дополнительные видео\n"
        "🖼 Дополнительные фото\n\n"
        "💡 _Можно отправить несколько файлов по очереди_\n\n"
        "Или нажмите кнопку, если дополнительных файлов нет:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@admin_events_router.message(AdminStates.create_event_message, F.text | F.photo | F.video)
async def process_event_message(message: Message, state: FSMContext):
    """Обработка одиночного сообщения с текстом/фото/видео"""
    # Если это часть альбома - пропускаем, его обработает другой handler
    if message.media_group_id:
        return
    
    event_message = message.text or message.caption or ""
    
    # Проверяем текст
    if not event_message.strip():
        await message.answer("❌ Сообщение не может быть пустым. Попробуйте еще раз:")
        return
    
    # Сохраняем сообщение
    await state.update_data(event_message=event_message)
    
    # Если есть медиа, сохраняем его
    data = await state.get_data()
    files = data.get('files', [])
    
    if message.photo or message.video:
        import os
        from ..handlers.handlers import get_global_var
        bot = get_global_var('bot')
        
        # Создаем временную папку
        ensure_temp_dir()
        
        if message.photo:
            # Скачиваем фото
            photo = message.photo[-1]  # Берем самое большое фото
            file = await bot.get_file(photo.file_id)
            file_name = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            file_path = os.path.join(TEMP_DIR, file_name)
            await bot.download_file(file.file_path, file_path)
            
            files.append({
                'type': 'photo',
                'file_path': file_path,
                'name': file_name,
                'stage': 'with_message',
                'has_caption': bool(message.caption)
            })
            logger.info(f"Фото сохранено: {file_path} (with_message)")
            
        elif message.video:
            # Скачиваем видео
            file = await bot.get_file(message.video.file_id)
            file_name = message.video.file_name or f"{message.video.file_id}.mp4"
            file_path = os.path.join(TEMP_DIR, file_name)
            await bot.download_file(file.file_path, file_path)
            
            files.append({
                'type': 'video',
                'file_path': file_path,
                'name': file_name,
                'stage': 'with_message',
                'has_caption': bool(message.caption)
            })
            logger.info(f"Видео сохранено: {file_path} (with_message)")
    
    await state.update_data(files=files)
    
    # Переходим к добавлению файлов
    await state.set_state(AdminStates.create_event_files)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Продолжить без файлов", callback_data="files:skip")]
    ])
    
    await message.answer(
        "✅ **Сообщение сохранено!**\n\n"
        "📎 **Дополнительные файлы**\n\n"
        "Теперь вы можете отправить:\n"
        "📄 PDF документы\n"
        "📁 Файлы любых форматов\n"
        "🎥 Дополнительные видео\n"
        "🖼 Дополнительные фото\n\n"
        "💡 _Можно отправить несколько файлов по очереди_\n\n"
        "Или нажмите кнопку, если дополнительных файлов нет:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


@admin_events_router.message(AdminStates.create_event_files, F.document | F.photo | F.video)
async def process_event_files(message: Message, state: FSMContext):
    """Обработка файлов для события"""
    import os
    from ..handlers.handlers import get_global_var
    
    data = await state.get_data()
    files = data.get('files', [])
    bot = get_global_var('bot')
    
    # Создаем временную папку
    ensure_temp_dir()
    
    # Скачиваем и добавляем файл в список
    if message.document:
        file = await bot.get_file(message.document.file_id)
        file_path = os.path.join(TEMP_DIR, message.document.file_name)
        await bot.download_file(file.file_path, file_path)
        
        files.append({
            'type': 'document',
            'file_path': file_path,
            'name': message.document.file_name,
            'stage': 'after_message'
        })
        logger.info(f"Документ сохранен: {file_path} (after_message)")
        
    elif message.photo:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        file_name = f"photo_{datetime.now().strftime('%H%M%S')}.jpg"
        file_path = os.path.join(TEMP_DIR, file_name)
        await bot.download_file(file.file_path, file_path)
        
        files.append({
            'type': 'photo',
            'file_path': file_path,
            'name': file_name,
            'stage': 'after_message'
        })
        logger.info(f"Фото сохранено: {file_path} (after_message)")
        
    elif message.video:
        file = await bot.get_file(message.video.file_id)
        file_name = message.video.file_name or f"{message.video.file_id}.mp4"  # Используем оригинальное имя или file_id
        file_path = os.path.join(TEMP_DIR, file_name)
        await bot.download_file(file.file_path, file_path)
        
        files.append({
            'type': 'video',
            'file_path': file_path,
            'name': file_name,
            'stage': 'after_message'
        })
        logger.info(f"Видео сохранено: {file_path} (after_message)")
    
    await state.update_data(files=files)
    
    # Кнопка для завершения добавления файлов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Завершить добавление файлов", callback_data="files:done")]
    ])
    
    await message.answer(
        f"✅ Файл добавлен (всего: {len(files)})\n\n"
        "Отправьте еще файлы или нажмите кнопку для завершения:",
        reply_markup=keyboard
    )

@admin_events_router.callback_query(F.data.startswith("files:"), AdminStates.create_event_files)
async def process_files_action(callback_query: CallbackQuery, state: FSMContext):
    """Обработка действий с файлами"""
    action = callback_query.data.split(":", 1)[1]
    
    data = await state.get_data()
    files = data.get('files', [])
    
    if action == "skip" and not files:
        # Если файлов нет и нажали "Продолжить без файлов" - очищаем
        files = []
        await state.update_data(files=files)
    elif action == "skip":
        # Если файлы уже есть - оставляем их
        logger.info(f"Продолжаем с {len(files)} существующими файлами")
    
    # Переход к подтверждению
    await state.set_state(AdminStates.create_event_confirm)
    
    # Формируем дату и время для отображения (московское время)
    event_date = data.get('event_date')
    event_time = data.get('event_time')
    naive_datetime = datetime.strptime(f"{event_date} {event_time}", '%Y-%m-%d %H:%M')
    moscow_datetime = MOSCOW_TZ.localize(naive_datetime)
    
    # Отправляем сообщение с подтверждением
    summary = (
        f"📋 **Подтверждение создания события**\n\n"
        f"📝 Название: **{data.get('event_name')}**\n"
        f"📅 Дата и время: **{moscow_datetime.strftime('%d.%m.%Y %H:%M')} (МСК)**\n"
        f"👥 Сегмент: **{data.get('segment_display')}**\n"
        f"📎 Файлов: **{len(files)}**\n\n"
        "Подтвердите создание события:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Создать", callback_data="confirm:yes"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="confirm:no")
        ],
        [
            InlineKeyboardButton(text="👁 Предпросмотр", callback_data="preview:show")
        ]
    ])
    
    await callback_query.message.edit_text(
        summary,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@admin_events_router.callback_query(F.data == "preview:show", AdminStates.create_event_confirm)
async def show_event_preview(callback_query: CallbackQuery, state: FSMContext):
    """Показываем предпросмотр сообщения"""
    from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
    
    # Получаем данные
    data = await state.get_data()
    files = data.get('files', [])
    logger.info(f"Предпросмотр: получено {len(files)} файлов из состояния")
    
    # Удаляем сообщение с кнопкой предпросмотра
    await callback_query.message.delete()
    
    # Анализируем файлы
    files_with_msg = [f for f in files if f.get('stage') == 'with_message']
    files_after = [f for f in files if f.get('stage') == 'after_message']
    logger.info(f"Предпросмотр: {len(files_with_msg)} файлов с сообщением, {len(files_after)} дополнительных файлов")
    
    # 1. Отправляем сообщение с прикрепленными файлами
    if files_with_msg:
        media_group = []
        first_file = True
        
        # Сортируем файлы по порядку
        sorted_files = sorted(files_with_msg, key=lambda x: x.get('order', 0))
        
        # Добавляем файлы в том порядке, в котором они были загружены
        for file_info in sorted_files:
            logger.info(f"Добавляем в медиа-группу: {file_info['type']} файл {file_info['file_path']}")
            try:
                if file_info['type'] == 'photo':
                    media = InputMediaPhoto(
                        media=FSInputFile(file_info['file_path']),
                        caption=data.get('event_message') if first_file else None,
                        parse_mode='Markdown' if first_file else None
                    )
                    media_group.append(media)
                    first_file = False
                elif file_info['type'] == 'video':
                    media = InputMediaVideo(
                        media=FSInputFile(file_info['file_path']),
                        caption=data.get('event_message') if first_file else None,
                        parse_mode='Markdown' if first_file else None
                    )
                    media_group.append(media)
                    first_file = False
                logger.info("✅ Файл успешно добавлен в медиа-группу")
            except Exception as e:
                logger.error(f"❌ Ошибка добавления файла в медиа-группу: {e}")
        
        if media_group:
            try:
                from ..handlers.handlers import get_global_var
                bot = get_global_var('bot')
                await bot.send_media_group(chat_id=callback_query.message.chat.id, media=media_group)
                logger.info(f"✅ Отправлена медиа-группа из {len(media_group)} файлов")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки медиа-группы: {e}")
                # Если не удалось отправить группой, отправляем по одному
                first_file = True
                for media in media_group:
                    try:
                        if isinstance(media, InputMediaPhoto):
                            await callback_query.message.answer_photo(
                                photo=media.media,
                                caption=data.get('event_message') if first_file else None,
                                parse_mode='Markdown' if first_file else None
                            )
                        elif isinstance(media, InputMediaVideo):
                            await callback_query.message.answer_video(
                                video=media.media,
                                caption=data.get('event_message') if first_file else None,
                                parse_mode='Markdown' if first_file else None
                            )
                        first_file = False
                    except Exception as e2:
                        logger.error(f"❌ Ошибка отправки отдельного файла: {e2}")
    else:
        # Только текст
        await callback_query.message.answer(
            data.get('event_message'),
            parse_mode='Markdown'
        )
    
    # 2. Отправляем дополнительные файлы
    for file_info in files_after:
        if file_info['type'] == 'document':
            await callback_query.message.answer_document(
                FSInputFile(file_info['file_path'])
            )
        elif file_info['type'] == 'photo':
            await callback_query.message.answer_photo(
                FSInputFile(file_info['file_path'])
            )
        elif file_info['type'] == 'video':
            await callback_query.message.answer_video(
                FSInputFile(file_info['file_path'])
            )
    
    # 3. Отправляем сообщение с подтверждением (такое же как было)
    event_date = data.get('event_date')
    event_time = data.get('event_time')
    naive_datetime = datetime.strptime(f"{event_date} {event_time}", '%Y-%m-%d %H:%M')
    moscow_datetime = MOSCOW_TZ.localize(naive_datetime)
    
    summary = (
        f"📋 **Подтверждение создания события**\n\n"
        f"📝 Название: **{data.get('event_name')}**\n"
        f"📅 Дата и время: **{moscow_datetime.strftime('%d.%m.%Y %H:%M')} (МСК)**\n"
        f"👥 Сегмент: **{data.get('segment_display')}**\n"
        f"📎 Файлов: **{len(files)}**\n\n"
        "Подтвердите создание события:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Создать", callback_data="confirm:yes"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="confirm:no")
        ],
        [
            InlineKeyboardButton(text="👁 Предпросмотр", callback_data="preview:show")
        ]
    ])
    
    await callback_query.message.answer(
        summary,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@admin_events_router.callback_query(F.data.startswith("confirm:"), AdminStates.create_event_confirm)
async def process_event_confirmation(callback_query: CallbackQuery, state: FSMContext):
    """Обработка подтверждения создания события"""
    action = callback_query.data.split(":", 1)[1]
    
    if action == "no":
        # Очищаем временные файлы
        await cleanup_temp_files(state)
        # Очищаем состояние
        await state.clear()
        await callback_query.message.edit_text(
            "❌ Создание события отменено",
            parse_mode='Markdown'
        )
        return
    
    # Создаем событие
    data = await state.get_data()
    
    from ..handlers.handlers import get_global_var
    supabase_client = get_global_var('supabase_client')
    
    # Формируем datetime для планирования
    event_date = data.get('event_date')
    event_time = data.get('event_time')
    
    # Создаем naive datetime из введенного московского времени
    naive_datetime = datetime.strptime(f"{event_date} {event_time}", '%Y-%m-%d %H:%M')
    
    # Привязываем к московской временной зоне
    moscow_datetime = MOSCOW_TZ.localize(naive_datetime)
    
    # Конвертируем в UTC для сохранения в БД
    utc_datetime = moscow_datetime.astimezone(pytz.UTC)
    
    logger.info(f"⏰ Время события: Москва={moscow_datetime.strftime('%d.%m.%Y %H:%M %Z')}, UTC={utc_datetime.strftime('%d.%m.%Y %H:%M %Z')}")
    
    # Сначала сохраняем событие в БД чтобы получить ID
    try:
        # Создаем событие без файлов
        event = await supabase_client.save_admin_event(
            event_name=data.get('event_name'),
            event_data={
                'segment': data.get('segment'),
                'message': data.get('event_message'),
                'files': []  # Пока пустой список
            },
            scheduled_datetime=utc_datetime
        )
        event_id = event['id']
        logger.info(f"✅ Создано событие с ID {event_id}")
        
        # Теперь загружаем файлы в Storage
        import os
        files = data.get('files', [])
        uploaded_files = []
        
        for file_info in files:
            try:
                # Читаем локальный файл
                with open(file_info['file_path'], 'rb') as f:
                    file_bytes = f.read()
                
                # Генерируем уникальный ID для файла
                file_id = generate_file_id()
                
                # Загружаем в Storage
                storage_info = await supabase_client.upload_event_file(
                    event_id=event_id,
                    file_data=file_bytes,
                    original_name=file_info['name'],
                    file_id=file_id
                )
                
                # Сохраняем метаданные файла
                uploaded_files.append({
                    'type': file_info['type'],
                    'storage_path': storage_info['storage_path'],
                    'original_name': file_info['name'],  # Используем оригинальное имя из file_info
                    'stage': file_info['stage'],
                    'has_caption': file_info.get('has_caption', False),
                    'order': file_info.get('order', 0)
                })
                
                # Удаляем временный локальный файл
                try:
                    os.remove(file_info['file_path'])
                    logger.info(f"🗑️ Удален временный файл: {file_info['file_path']}")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось удалить временный файл: {e}")
            
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки файла {file_info['name']}: {e}")
                # Если ошибка - удаляем все файлы события и само событие
                try:
                    await supabase_client.delete_event_files(event_id)
                    # TODO: добавить метод удаления события
                except:
                    pass
                raise
        
        logger.info(f"✅ Загружено {len(uploaded_files)} файлов в Storage для события {event_id}")
        
        # Обновляем событие с информацией о файлах
        event_data = {
            'segment': data.get('segment'),
            'message': data.get('event_message'),
            'files': uploaded_files
        }
        
        # TODO: добавить метод обновления события
        response = supabase_client.client.table('scheduled_events').update({
            'event_data': json.dumps(event_data, ensure_ascii=False)
        }).eq('id', event_id).execute()
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания события: {e}")
        raise
    
    # Показываем сообщение об успехе
    await callback_query.message.edit_text(
        f"✅ **Событие успешно создано!**\n\n"
        f"📝 Название: `{data.get('event_name')}`\n"
        f"📅 Запланировано на: **{moscow_datetime.strftime('%d.%m.%Y %H:%M')} (МСК)**\n"
        f"👥 Сегмент: **{data.get('segment_display')}**\n\n"
        f"💡 _Нажмите на название для копирования_",
        parse_mode='Markdown'
    )
    
    # Очищаем временные файлы и состояние
    await cleanup_temp_files(state)
    await state.set_state(AdminStates.admin_mode)

@admin_events_router.message(Command(commands=["список_событий", "list_events"]))
async def list_events_command(message: Message, state: FSMContext):
    """Просмотр всех запланированных событий"""
    from ..handlers.handlers import get_global_var
    admin_manager = get_global_var('admin_manager')
    supabase_client = get_global_var('supabase_client')
    
    if not admin_manager.is_admin(message.from_user.id):
        return
    
    try:
        # Получаем все pending события (незавершенные и неотмененные)
        events = await supabase_client.get_admin_events(status='pending')
        
        if not events:
            await message.answer(
                "📋 **Нет активных событий**\n\n"
                "Используйте `/create_event` для создания нового события",
                parse_mode='Markdown'
            )
            return
        
        # Формируем список событий в красивом формате
        text_parts = [
            f"📋 **Активные события** ({len(events)})\n"
        ]
        
        for idx, event in enumerate(events, 1):
            event_name = event['event_type']
            
            # Конвертируем UTC в московское время для отображения
            utc_time = datetime.fromisoformat(event['scheduled_at'].replace('Z', '+00:00'))
            moscow_time = utc_time.astimezone(MOSCOW_TZ)
            
            # Красивый формат с эмодзи и структурой
            text_parts.append(
                f"📌 **{idx}.** `{event_name}`\n"
                f"    🕐 {moscow_time.strftime('%d.%m.%Y в %H:%M')} МСК\n"
            )
        
        text_parts.append(
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _Нажмите на название для копирования_\n"
            f"🗑️ Удалить: `/delete_event название`"
        )
        
        await message.answer(
            "\n".join(text_parts),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения событий: {e}")
        await message.answer(
            f"❌ Ошибка получения событий:\n`{str(e)}`",
            parse_mode='Markdown'
        )


@admin_events_router.message(Command(commands=["удалить_событие", "delete_event"]))
async def delete_event_command(message: Message, state: FSMContext):
    """Удаление события по названию"""
    from ..handlers.handlers import get_global_var
    admin_manager = get_global_var('admin_manager')
    supabase_client = get_global_var('supabase_client')
    
    if not admin_manager.is_admin(message.from_user.id):
        return
    
    # Парсим название из команды
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "❌ Укажите название события:\n"
            "`/delete_event название`\n\n"
            "Используйте /list_events для просмотра списка событий",
            parse_mode='Markdown'
        )
        return
    
    event_name = parts[1].strip()
    
    try:
        # Сначала получаем событие чтобы узнать его ID
        response = supabase_client.client.table('scheduled_events').select(
            'id'
        ).eq('event_type', event_name).eq(
            'event_category', 'admin_event'
        ).eq('status', 'pending').execute()
        
        if response.data:
            event_id = response.data[0]['id']
            
            # Удаляем файлы из Storage
            try:
                await supabase_client.delete_event_files(event_id)
                logger.info(f"🗑️ Удалены файлы события '{event_name}' (ID: {event_id}) из Storage")
            except Exception as e:
                logger.error(f"❌ Ошибка удаления файлов события из Storage: {e}")
            
            # Отмечаем событие как отмененное
            supabase_client.client.table('scheduled_events').update({
                'status': 'cancelled'
            }).eq('id', event_id).execute()
            
            await message.answer(
                f"✅ Событие `{event_name}` успешно отменено\n"
                f"_(файлы удалены из Storage)_",
                parse_mode='Markdown'
            )
            logger.info(f"Отменено событие '{event_name}' (ID: {event_id})")
        else:
            await message.answer(
                f"❌ Активное событие с названием `{event_name}` не найдено\n\n"
                f"Используйте /list_events для просмотра списка активных событий",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Ошибка удаления события: {e}")
        await message.answer(
            f"❌ Ошибка удаления события:\n`{str(e)}`",
            parse_mode='Markdown'
        )

