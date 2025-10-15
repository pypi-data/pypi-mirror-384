"""
Декораторы для обработчиков событий и временных задач
"""

import asyncio
import logging
import re
from typing import Callable, Any, Dict, Union
from datetime import datetime, timedelta, timezone
from functools import wraps

logger = logging.getLogger(__name__)

def format_seconds_to_human(seconds: int) -> str:
    """
    Форматирует секунды в человекочитаемый формат
    
    Args:
        seconds: Количество секунд
    
    Returns:
        str: Человекочитаемое время
    
    Examples:
        format_seconds_to_human(3600) -> "1ч 0м"
        format_seconds_to_human(5445) -> "1ч 30м"
        format_seconds_to_human(102461) -> "1д 4ч 28м"
    """
    if seconds < 60:
        return f"{seconds}с"
    
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}д")
    if hours > 0:
        parts.append(f"{hours}ч")
    if minutes > 0:
        parts.append(f"{minutes}м")
    
    return " ".join(parts) if parts else "0м"

def parse_time_string(time_str: Union[str, int]) -> int:
    """
    Парсит время в удобном формате и возвращает секунды
    
    Args:
        time_str: Время в формате "1h 30m 45s" или число (секунды)
    
    Returns:
        int: Количество секунд
    
    Examples:
        parse_time_string("1h 30m 45s") -> 5445
        parse_time_string("2h") -> 7200
        parse_time_string("45m") -> 2700
        parse_time_string("30s") -> 30
        parse_time_string(3600) -> 3600
    """
    if isinstance(time_str, int):
        return time_str
       
    # Убираем лишние пробелы и приводим к нижнему регистру
    time_str = time_str.strip().lower()
    
    # Если это просто число - возвращаем как секунды
    if time_str.isdigit():
        return int(time_str)
    
    total_seconds = 0
    
    # Регулярное выражение для поиска времени: число + единица (h, m, s)
    pattern = r'(\d+)\s*(h|m|s)'
    matches = re.findall(pattern, time_str)
    
    if not matches:
        raise ValueError(f"Неверный формат времени: '{time_str}'. Используйте формат '1h 30m 45s'")
    
    for value, unit in matches:
        value = int(value)
        
        if unit == 'h':  # часы
            total_seconds += value * 3600
        elif unit == 'm':  # минуты
            total_seconds += value * 60
        elif unit == 's':  # секунды
            total_seconds += value
    
    if total_seconds <= 0:
        raise ValueError(f"Время должно быть больше 0: '{time_str}'")
    
    return total_seconds

def parse_supabase_datetime(datetime_str: str) -> datetime:
    """
    Парсит дату и время из формата Supabase в объект datetime
    
    Args:
        datetime_str: Строка даты и времени из Supabase (ISO 8601 формат)
    
    Returns:
        datetime: Объект datetime с timezone
    
    Examples:
        parse_supabase_datetime("2024-01-15T10:30:45.123456Z") -> datetime(2024, 1, 15, 10, 30, 45, 123456, tzinfo=timezone.utc)
        parse_supabase_datetime("2024-01-15T10:30:45+00:00") -> datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        parse_supabase_datetime("2024-01-15T10:30:45") -> datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
    """
    if not datetime_str:
        raise ValueError("Пустая строка даты и времени")
    
    # Убираем лишние пробелы
    datetime_str = datetime_str.strip()
    
    try:
        # Пробуем парсить ISO 8601 формат с Z в конце
        if datetime_str.endswith('Z'):
            # Заменяем Z на +00:00 для корректного парсинга
            datetime_str = datetime_str[:-1] + '+00:00'
            return datetime.fromisoformat(datetime_str)
        
        # Пробуем парсить ISO 8601 формат с timezone
        if '+' in datetime_str or datetime_str.count('-') > 2:
            return datetime.fromisoformat(datetime_str)
        
        # Если нет timezone, добавляем UTC
        if 'T' in datetime_str:
            return datetime.fromisoformat(datetime_str + '+00:00')
        
        # Если это только дата, добавляем время 00:00:00 и UTC
        return datetime.fromisoformat(datetime_str + 'T00:00:00+00:00')
        
    except ValueError as e:
        raise ValueError(f"Неверный формат даты и времени: '{datetime_str}'. Ошибка: {e}")

def format_datetime_for_supabase(dt: datetime) -> str:
    """
    Форматирует объект datetime в формат для Supabase
    
    Args:
        dt: Объект datetime
    
    Returns:
        str: Строка в формате ISO 8601 для Supabase
    
    Examples:
        format_datetime_for_supabase(datetime.now(timezone.utc)) -> "2024-01-15T10:30:45.123456+00:00"
    """
    if not isinstance(dt, datetime):
        raise ValueError("Ожидается объект datetime")
    
    # Если нет timezone, добавляем UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.isoformat()

def get_time_difference_seconds(dt1: datetime, dt2: datetime) -> int:
    """
    Вычисляет разность между двумя датами в секундах
    
    Args:
        dt1: Первая дата
        dt2: Вторая дата
    
    Returns:
        int: Разность в секундах (dt2 - dt1)
    
    Examples:
        get_time_difference_seconds(datetime1, datetime2) -> 3600  # 1 час
    """
    
    # Если у дат нет timezone, добавляем UTC
    if dt1.tzinfo is None:
        dt1 = dt1.replace(tzinfo=timezone.utc)
    if dt2.tzinfo is None:
        dt2 = dt2.replace(tzinfo=timezone.utc)
    
    return int((dt2 - dt1).total_seconds())

def is_datetime_recent(dt: datetime, max_age_seconds: int = 3600) -> bool:
    """
    Проверяет, является ли дата недавней (не старше указанного времени)
    
    Args:
        dt: Дата для проверки
        max_age_seconds: Максимальный возраст в секундах (по умолчанию 1 час)
    
    Returns:
        bool: True если дата недавняя, False если старая
    
    Examples:
        is_datetime_recent(datetime.now(), 1800) -> True  # если дата сейчас
        is_datetime_recent(datetime.now() - timedelta(hours=2), 3600) -> False  # если дата 2 часа назад
    """
    if not isinstance(dt, datetime):
        raise ValueError("Ожидается объект datetime")
    
    now = datetime.now(timezone.utc)
    
    # Если у даты нет timezone, добавляем UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    age_seconds = (now - dt).total_seconds()
    return age_seconds <= max_age_seconds

def parse_appointment_data(data_str: str) -> Dict[str, Any]:
    """
    Парсит данные записи на прием из строки формата "ключ: значение, ключ: значение"
    
    Args:
        data_str: Строка с данными записи
    
    Returns:
        Dict[str, Any]: Словарь с распарсенными данными
    
    Examples:
        parse_appointment_data("имя: Михаил, телефон: +79965214968, процедура: Ламинирование + окрашивание, мастер: Софья, дата: 2025-10-01, время: 19:00")
        -> {
            'имя': 'Михаил',
            'телефон': '+79965214968', 
            'процедура': 'Ламинирование + окрашивание',
            'мастер': 'Софья',
            'дата': '2025-10-01',
            'время': '19:00'
        }
    """
    if not data_str or not isinstance(data_str, str):
        return {}
    
    result = {}
    
    try:
        # Разделяем по запятым, но учитываем что внутри значений могут быть запятые
        # Используем более умный подход - ищем паттерн "ключ: значение"
        pattern = r'([^:]+):\s*([^,]+?)(?=,\s*[^:]+:|$)'
        matches = re.findall(pattern, data_str.strip())
        
        for key, value in matches:
            # Очищаем ключ и значение от лишних пробелов
            clean_key = key.strip()
            clean_value = value.strip()
            
            # Убираем запятые в конце значения если есть
            if clean_value.endswith(','):
                clean_value = clean_value[:-1].strip()
            
            result[clean_key] = clean_value
        
        # Дополнительная обработка для даты и времени
        if 'дата' in result and 'время' in result:
            try:
                # Создаем полную дату и время
                date_str = result['дата']
                time_str = result['время']
                
                # Парсим дату и время
                appointment_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                
                # Добавляем в результат
                result['datetime'] = appointment_datetime
                result['datetime_str'] = appointment_datetime.strftime("%Y-%m-%d %H:%M")
                
                # Проверяем, не в прошлом ли запись
                now = datetime.now()
                if appointment_datetime < now:
                    result['is_past'] = True
                else:
                    result['is_past'] = False
                    
            except ValueError as e:
                logger.warning(f"Ошибка парсинга даты/времени: {e}")
                result['datetime_error'] = str(e)
        
        logger.info(f"Распарсены данные записи: {list(result.keys())}")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка парсинга данных записи: {e}")
        return {'error': str(e), 'raw_data': data_str}

def format_appointment_data(appointment_data: Dict[str, Any]) -> str:
    """
    Форматирует данные записи обратно в строку
    
    Args:
        appointment_data: Словарь с данными записи
    
    Returns:
        str: Отформатированная строка
    
    Examples:
        format_appointment_data({
            'имя': 'Михаил',
            'телефон': '+79965214968',
            'процедура': 'Ламинирование + окрашивание',
            'мастер': 'Софья',
            'дата': '2025-10-01',
            'время': '19:00'
        })
        -> "имя: Михаил, телефон: +79965214968, процедура: Ламинирование + окрашивание, мастер: Софья, дата: 2025-10-01, время: 19:00"
    """
    if not appointment_data or not isinstance(appointment_data, dict):
        return ""
    
    # Исключаем служебные поля
    exclude_fields = {'datetime', 'datetime_str', 'is_past', 'datetime_error', 'error', 'raw_data'}
    
    parts = []
    for key, value in appointment_data.items():
        if key not in exclude_fields and value is not None:
            parts.append(f"{key}: {value}")
    
    return ", ".join(parts)

def validate_appointment_data(appointment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Валидирует данные записи на прием
    
    Args:
        appointment_data: Словарь с данными записи
    
    Returns:
        Dict[str, Any]: Результат валидации с полями 'valid', 'errors', 'warnings'
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Проверяем обязательные поля
    required_fields = ['имя', 'телефон', 'процедура', 'мастер', 'дата', 'время']
    
    for field in required_fields:
        if field not in appointment_data or not appointment_data[field]:
            result['errors'].append(f"Отсутствует обязательное поле: {field}")
            result['valid'] = False
    
    # Проверяем формат телефона
    if 'телефон' in appointment_data:
        phone = appointment_data['телефон']
        if not re.match(r'^\+?[1-9]\d{10,14}$', phone.replace(' ', '').replace('-', '')):
            result['warnings'].append(f"Неверный формат телефона: {phone}")
    
    # Проверяем дату
    if 'дата' in appointment_data:
        try:
            datetime.strptime(appointment_data['дата'], "%Y-%m-%d")
        except ValueError:
            result['errors'].append(f"Неверный формат даты: {appointment_data['дата']}")
            result['valid'] = False
    
    # Проверяем время
    if 'время' in appointment_data:
        try:
            datetime.strptime(appointment_data['время'], "%H:%M")
        except ValueError:
            result['errors'].append(f"Неверный формат времени: {appointment_data['время']}")
            result['valid'] = False
    
    # Проверяем, не в прошлом ли запись
    if 'is_past' in appointment_data and appointment_data['is_past']:
        result['warnings'].append("Запись назначена на прошедшую дату")
    
    return result

# Глобальный реестр обработчиков событий
_event_handlers: Dict[str, Callable] = {}
_scheduled_tasks: Dict[str, Dict[str, Any]] = {}
_global_handlers: Dict[str, Dict[str, Any]] = {}

# Глобальный менеджер роутеров
_router_manager = None

def event_handler(event_type: str, notify: bool = False, once_only: bool = True):
    """
    Декоратор для регистрации обработчика события
    
    Args:
        event_type: Тип события (например, 'appointment_booking', 'phone_collection')
        notify: Уведомлять ли админов о выполнении события (по умолчанию False)
        once_only: Обрабатывать ли событие только один раз (по умолчанию True)
    
    Example:
        # Обработчик только один раз (по умолчанию)
        @event_handler("appointment_booking", notify=True)
        async def book_appointment(user_id: int, appointment_data: dict):
            # Логика записи на прием
            return {"status": "success", "appointment_id": "123"}
        
        # Обработчик может выполняться многократно
        @event_handler("phone_collection", once_only=False)
        async def collect_phone(user_id: int, phone_data: dict):
            # Логика сбора телефона
            return {"status": "phone_collected"}
    """
    def decorator(func: Callable) -> Callable:
        _event_handlers[event_type] = {
            'handler': func,
            'name': func.__name__,
            'notify': notify,
            'once_only': once_only
        }
        
        logger.info(f"📝 Зарегистрирован обработчик события '{event_type}': {func.__name__}")
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                logger.info(f"🔧 Выполняем обработчик события '{event_type}'")
                result = await func(*args, **kwargs)
                logger.info(f"✅ Обработчик '{event_type}' выполнен успешно")
                
                # Автоматически добавляем флаг notify к результату
                if isinstance(result, dict):
                    result['notify'] = notify
                else:
                    # Если результат не словарь, создаем словарь
                    result = {
                        'status': 'success',
                        'result': result,
                        'notify': notify
                    }
                
                return result
            except Exception as e:
                logger.error(f"❌ Ошибка в обработчике '{event_type}': {e}")
                raise
        
        return wrapper
    return decorator

def schedule_task(task_name: str, notify: bool = False, smart_check: bool = True, once_only: bool = True, delay: Union[str, int] = None, event_type: Union[str, Callable] = None):
    """
    Декоратор для регистрации задачи, которую можно запланировать на время
    
    Args:
        task_name: Название задачи (например, 'send_reminder', 'follow_up')
        notify: Уведомлять ли админов о выполнении задачи (по умолчанию False)
        smart_check: Использовать ли умную проверку активности пользователя (по умолчанию True)
        once_only: Выполнять ли задачу только один раз (по умолчанию True)
        delay: Время задержки в удобном формате (например, "1h 30m", "45m", 3600) - ОБЯЗАТЕЛЬНО
        event_type: Источник времени события - ОПЦИОНАЛЬНО:
            - str: Тип события для поиска в БД (например, 'appointment_booking')
            - Callable: Функция для получения datetime (например, async def(user_id, user_data) -> datetime)
    
    Example:
        # Обычная задача с фиксированным временем
        @schedule_task("send_reminder", delay="1h 30m")
        async def send_reminder(user_id: int, user_data: str):
            # Задача будет запланирована на 1 час 30 минут
            return {"status": "sent", "message": user_data}
        
        # Напоминание о событии из БД (за delay времени до события)
        @schedule_task("appointment_reminder", delay="2h", event_type="appointment_booking")
        async def appointment_reminder(user_id: int, user_data: str):
            # Ищет событие "appointment_booking" в БД
            # Напоминание будет за 2 часа до времени из события
            return {"status": "sent", "message": user_data}
        
        # Напоминание с кастомной функцией получения времени
        async def get_yclients_appointment_time(user_id: int, user_data: str) -> datetime:
            '''Получает время записи из YClients API'''
            from yclients_api import get_next_booking
            booking = await get_next_booking(user_id)
            return booking['datetime']  # datetime объект
        
        @schedule_task("yclients_reminder", delay="1h", event_type=get_yclients_appointment_time)
        async def yclients_reminder(user_id: int, user_data: str):
            # Вызовет get_yclients_appointment_time(user_id, user_data)
            # Напоминание будет за 1 час до возвращенного datetime
            return {"status": "sent"}
        
        # Форматы времени:
        # delay="1h 30m 45s" - 1 час 30 минут 45 секунд
        # delay="2h" - 2 часа
        # delay="30m" - 30 минут
        # delay=3600 - 3600 секунд (число)
        
        # ИИ может передавать только данные (текст):
        # {"тип": "send_reminder", "инфо": "Текст напоминания"} - только текст
        # {"тип": "appointment_reminder", "инфо": ""} - пустой текст, время берется из события/функции
    """
    def decorator(func: Callable) -> Callable:
        # Время ОБЯЗАТЕЛЬНО должно быть указано
        if delay is None:
            raise ValueError(f"Для задачи '{task_name}' ОБЯЗАТЕЛЬНО нужно указать параметр delay")
        
        # Парсим время
        try:
            default_delay_seconds = parse_time_string(delay)
            if event_type:
                logger.info(f"⏰ Задача '{task_name}' настроена как напоминание о событии '{event_type}' за {delay} ({default_delay_seconds}с)")
            else:
                logger.info(f"⏰ Задача '{task_name}' настроена с задержкой: {delay} ({default_delay_seconds}с)")
        except ValueError as e:
            logger.error(f"❌ Ошибка парсинга времени для задачи '{task_name}': {e}")
            raise
        
        _scheduled_tasks[task_name] = {
            'handler': func,
            'name': func.__name__,
            'notify': notify,
            'smart_check': smart_check,
            'once_only': once_only,
            'default_delay': default_delay_seconds,
            'event_type': event_type  # Новое поле для типа события
        }
        
        if event_type:
            logger.info(f"⏰ Зарегистрирована задача-напоминание '{task_name}' для события '{event_type}': {func.__name__}")
        else:
            logger.info(f"⏰ Зарегистрирована задача '{task_name}': {func.__name__}")
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                logger.info(f"⏰ Выполняем запланированную задачу '{task_name}'")
                result = await func(*args, **kwargs)
                logger.info(f"✅ Задача '{task_name}' выполнена успешно")
                
                # Автоматически добавляем флаг notify к результату
                if isinstance(result, dict):
                    result['notify'] = notify
                else:
                    # Если результат не словарь, создаем словарь
                    result = {
                        'status': 'success',
                        'result': result,
                        'notify': notify
                    }
                
                return result
            except Exception as e:
                logger.error(f"❌ Ошибка в задаче '{task_name}': {e}")
                raise
        
        return wrapper
    return decorator

def global_handler(handler_type: str, notify: bool = False, once_only: bool = True, delay: Union[str, int] = None, event_type: Union[str, Callable] = None):
    """
    Декоратор для регистрации глобального обработчика (для всех пользователей)
    
    Args:
        handler_type: Тип глобального обработчика (например, 'global_announcement', 'mass_notification')
        notify: Уведомлять ли админов о выполнении (по умолчанию False)
        once_only: Выполнять ли обработчик только один раз (по умолчанию True)
        delay: Время задержки в удобном формате (например, "1h 30m", "45m", 3600) - ОБЯЗАТЕЛЬНО
        event_type: Источник времени события - ОПЦИОНАЛЬНО:
            - str: Тип события для поиска в БД
            - Callable: Функция для получения datetime (например, async def(handler_data: str) -> datetime)
    
    Example:
        # Глобальный обработчик с задержкой
        @global_handler("global_announcement", delay="2h", notify=True)
        async def send_global_announcement(announcement_text: str):
            # Выполнится через 2 часа
            return {"status": "sent", "recipients_count": 150}
        
        # Глобальный обработчик может выполняться многократно
        @global_handler("daily_report", delay="24h", once_only=False)
        async def send_daily_report(report_data: str):
            # Может запускаться каждый день через 24 часа
            return {"status": "sent", "report_type": "daily"}
        
        # С кастомной функцией для получения времени
        async def get_promo_end_time(handler_data: str) -> datetime:
            '''Получает время окончания акции из CRM'''
            from crm_api import get_active_promo
            promo = await get_active_promo()
            return promo['end_datetime']
        
        @global_handler("promo_ending_notification", delay="2h", event_type=get_promo_end_time)
        async def notify_promo_ending(handler_data: str):
            # Уведомление за 2 часа до окончания акции
            return {"status": "sent"}
        
        # Форматы времени:
        # delay="1h 30m 45s" - 1 час 30 минут 45 секунд
        # delay="2h" - 2 часа
        # delay="45m" - 45 минут
        # delay=3600 - 3600 секунд (число)
        
        # ИИ может передавать только данные (текст):
        # {"тип": "global_announcement", "инфо": "Важное объявление!"} - только текст
        # {"тип": "global_announcement", "инфо": ""} - пустой текст, время из функции
    """
    def decorator(func: Callable) -> Callable:
        # Время ОБЯЗАТЕЛЬНО должно быть указано
        if delay is None:
            raise ValueError(f"Для глобального обработчика '{handler_type}' ОБЯЗАТЕЛЬНО нужно указать параметр delay")
        
        # Парсим время
        try:
            default_delay_seconds = parse_time_string(delay)
            logger.info(f"🌍 Глобальный обработчик '{handler_type}' настроен с задержкой: {delay} ({default_delay_seconds}с)")
        except ValueError as e:
            logger.error(f"❌ Ошибка парсинга времени для глобального обработчика '{handler_type}': {e}")
            raise
        
        _global_handlers[handler_type] = {
            'handler': func,
            'name': func.__name__,
            'notify': notify,
            'once_only': once_only,
            'default_delay': default_delay_seconds,
            'event_type': event_type  # Добавляем event_type для глобальных обработчиков
        }
        
        logger.info(f"🌍 Зарегистрирован глобальный обработчик '{handler_type}': {func.__name__}")
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                logger.info(f"🌍 Выполняем глобальный обработчик '{handler_type}'")
                result = await func(*args, **kwargs)
                logger.info(f"✅ Глобальный обработчик '{handler_type}' выполнен успешно")
                
                # Автоматически добавляем флаг notify к результату
                if isinstance(result, dict):
                    result['notify'] = notify
                else:
                    # Если результат не словарь, создаем словарь
                    result = {
                        'status': 'success',
                        'result': result,
                        'notify': notify
                    }
                
                return result
            except Exception as e:
                logger.error(f"❌ Ошибка в глобальном обработчике '{handler_type}': {e}")
                raise
        
        return wrapper
    return decorator

def get_event_handlers() -> Dict[str, Dict[str, Any]]:
    """Возвращает все зарегистрированные обработчики событий"""
    return _event_handlers.copy()

def get_scheduled_tasks() -> Dict[str, Dict[str, Any]]:
    """Возвращает все зарегистрированные задачи"""
    return _scheduled_tasks.copy()

def get_global_handlers() -> Dict[str, Dict[str, Any]]:
    """Возвращает все зарегистрированные глобальные обработчики"""
    return _global_handlers.copy()

def set_router_manager(router_manager):
    """Устанавливает глобальный менеджер роутеров"""
    global _router_manager
    _router_manager = router_manager
    logger.info("🔄 RouterManager установлен в decorators")

def get_router_manager():
    """Получает глобальный менеджер роутеров"""
    return _router_manager

def get_handlers_for_prompt() -> str:
    """
    Возвращает описание всех обработчиков для добавления в промпт
    """
    # Сначала пробуем получить из роутеров
    if _router_manager:
        return _router_manager.get_handlers_for_prompt()
    
    # Fallback к старым декораторам
    if not _event_handlers and not _scheduled_tasks and not _global_handlers:
        return ""
    
    prompt_parts = []
    
    if _event_handlers:
        prompt_parts.append("ДОСТУПНЫЕ ОБРАБОТЧИКИ СОБЫТИЙ:")
        for event_type, handler_info in _event_handlers.items():
            prompt_parts.append(f"- {event_type}: {handler_info['name']}")
    
    if _scheduled_tasks:
        prompt_parts.append("\nДОСТУПНЫЕ ЗАДАЧИ ДЛЯ ПЛАНИРОВАНИЯ:")
        for task_name, task_info in _scheduled_tasks.items():
            prompt_parts.append(f"- {task_name}: {task_info['name']}")
    
    if _global_handlers:
        prompt_parts.append("\nДОСТУПНЫЕ ГЛОБАЛЬНЫЕ ОБРАБОТЧИКИ:")
        for handler_type, handler_info in _global_handlers.items():
            prompt_parts.append(f"- {handler_type}: {handler_info['name']}")
    
    return "\n".join(prompt_parts)

async def execute_event_handler(event_type: str, *args, **kwargs) -> Any:
    """Выполняет обработчик события по типу"""
    # Сначала пробуем получить из роутеров
    if _router_manager:
        event_handlers = _router_manager.get_event_handlers()
        if event_type in event_handlers:
            handler_info = event_handlers[event_type]
            return await handler_info['handler'](*args, **kwargs)
    
    # Fallback к старым декораторам
    if event_type not in _event_handlers:
        import inspect
        frame = inspect.currentframe()
        line_no = frame.f_lineno if frame else "unknown"
        logger.error(f"❌ [decorators.py:{line_no}] Обработчик события '{event_type}' не найден")
        raise ValueError(f"Обработчик события '{event_type}' не найден")
    
    handler_info = _event_handlers[event_type]
    return await handler_info['handler'](*args, **kwargs)

async def execute_scheduled_task(task_name: str, user_id: int, user_data: str) -> Any:
    """Выполняет запланированную задачу по имени (без планирования, только выполнение)"""
    # Сначала пробуем получить из роутеров
    if _router_manager:
        scheduled_tasks = _router_manager.get_scheduled_tasks()
        if task_name in scheduled_tasks:
            task_info = scheduled_tasks[task_name]
            return await task_info['handler'](user_id, user_data)
    
    
    task_info = _scheduled_tasks[task_name]
    return await task_info['handler'](user_id, user_data)

async def execute_global_handler(handler_type: str, *args, **kwargs) -> Any:
    """Выполняет глобальный обработчик по типу"""
    router_manager = get_router_manager()
    if router_manager:
        global_handlers = router_manager.get_global_handlers()
    else:
        global_handlers = _global_handlers
    
    if handler_type not in global_handlers:
        raise ValueError(f"Глобальный обработчик '{handler_type}' не найден")
    
    handler_info = global_handlers[handler_type]
    return await handler_info['handler'](*args, **kwargs)

async def schedule_task_for_later(task_name: str, delay_seconds: int, user_id: int, user_data: str):
    """
    Планирует выполнение задачи через указанное время
    
    Args:
        task_name: Название задачи
        delay_seconds: Задержка в секундах
        user_id: ID пользователя
        user_data: Простой текст для задачи
    """
    # Ищем задачу через RouterManager (новая логика)
    router_manager = get_router_manager()
    if router_manager:
        scheduled_tasks = router_manager.get_scheduled_tasks()
        logger.debug(f"🔍 Поиск задачи '{task_name}' через RouterManager")
    else:
        scheduled_tasks = _scheduled_tasks
        logger.debug(f"🔍 Поиск задачи '{task_name}' через глобальный реестр")
    
    if task_name not in scheduled_tasks:
        available_tasks = list(scheduled_tasks.keys())
        logger.error(f"❌ Задача '{task_name}' не найдена. Доступные задачи: {available_tasks}")
        raise ValueError(f"Задача '{task_name}' не найдена. Доступные: {available_tasks}")
    
    logger.info(f"⏰ Планируем задачу '{task_name}' через {delay_seconds} секунд")
    
    async def delayed_task():
        await asyncio.sleep(delay_seconds)
        await execute_scheduled_task(task_name, user_id, user_data)
    
    # Запускаем задачу в фоне
    asyncio.create_task(delayed_task())
    
    return {
        "status": "scheduled",
        "task_name": task_name,
        "delay_seconds": delay_seconds,
        "scheduled_at": datetime.now().isoformat()
    }

async def execute_scheduled_task_from_event(user_id: int, task_name: str, event_info: str, session_id: str = None):
    """
    Выполняет запланированную задачу на основе события от ИИ
    
    Args:
        user_id: ID пользователя
        task_name: Название задачи
        event_info: Информация от ИИ (только текст, время задается в декораторе или событии)
        session_id: ID сессии для отслеживания
    """
    router_manager = get_router_manager()
    if router_manager:
        scheduled_tasks = router_manager.get_scheduled_tasks()
        logger.debug(f"🔍 RouterManager найден, доступные задачи: {list(scheduled_tasks.keys())}")
    else:
        scheduled_tasks = _scheduled_tasks
        logger.debug(f"🔍 RouterManager не найден, старые задачи: {list(scheduled_tasks.keys())}")
    
    if task_name not in scheduled_tasks:
        available_tasks = list(scheduled_tasks.keys())
        logger.error(f"❌ Задача '{task_name}' не найдена. Доступные задачи: {available_tasks}")
        logger.error(f"❌ RouterManager статус: {'найден' if router_manager else 'НЕ НАЙДЕН'}")
        raise ValueError(f"Задача '{task_name}' не найдена. Доступные задачи: {available_tasks}")
    
    task_info = scheduled_tasks[task_name]
    default_delay = task_info.get('default_delay')
    event_type = task_info.get('event_type')
    
    # Время всегда берется из декоратора, ИИ может передавать только текст
    if default_delay is None:
        raise ValueError(f"Для задачи '{task_name}' не указано время в декораторе (параметр delay)")
    
    # event_info содержит только текст для задачи (если ИИ не передал - пустая строка)
    user_data = event_info.strip() if event_info else ""
    
    # Если указан event_type, то это напоминание о событии
    if event_type:
        event_datetime = None
        
        # ========== ПРОВЕРЯЕМ ТИП event_type: СТРОКА ИЛИ ФУНКЦИЯ ==========
        if callable(event_type):
            # ВАРИАНТ 2: Функция - вызываем для получения datetime
            logger.info(f"⏰ Задача '{task_name}' - вызываем функцию для получения времени события")
            
            try:
                # Вызываем функцию пользователя с теми же аргументами что у обработчика
                event_datetime = await event_type(user_id, user_data)
                
                if not isinstance(event_datetime, datetime):
                    raise ValueError(f"Функция event_type должна вернуть datetime, получен {type(event_datetime)}")
                
                logger.info(f"✅ Функция вернула время события: {event_datetime}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка в функции event_type: {e}")
                # Fallback - планируем через default_delay
                result = await schedule_task_for_later_with_db(task_name, user_id, user_data, default_delay, session_id)
                return result
        
        else:
            # ВАРИАНТ 1: Строка - ищем событие в БД (текущая логика)
            logger.info(f"⏰ Задача '{task_name}' - напоминание о событии '{event_type}' за {default_delay}с")
            
            # Получаем клиент Supabase
            supabase_client = get_supabase_client()
            if not supabase_client:
                raise RuntimeError("Supabase клиент не найден для получения времени события")
            
            try:
                # Получаем данные события из БД
                event_data_str = await supabase_client.get_last_event_info_by_user_and_type(user_id, event_type)
                
                if not event_data_str:
                    logger.warning(f"Событие '{event_type}' не найдено для пользователя {user_id}")
                    # Fallback - планируем через default_delay
                    result = await schedule_task_for_later_with_db(task_name, user_id, user_data, default_delay, session_id)
                    return result
                
                # Парсим данные события
                event_data = parse_appointment_data(event_data_str)
                
                if 'datetime' not in event_data:
                    logger.warning(f"Не удалось распарсить дату/время из события '{event_type}'")
                    # Fallback - планируем через default_delay
                    result = await schedule_task_for_later_with_db(task_name, user_id, user_data, default_delay, session_id)
                    return result
                
                event_datetime = event_data['datetime']
                logger.info(f"✅ Получено время события из БД: {event_datetime}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка получения события из БД: {e}")
                # Fallback - планируем через default_delay
                result = await schedule_task_for_later_with_db(task_name, user_id, user_data, default_delay, session_id)
                return result
        
        # ========== ОБЩАЯ ЛОГИКА ДЛЯ ОБОИХ ВАРИАНТОВ ==========
        # Теперь у нас есть event_datetime (из БД или из функции)
        now = datetime.now()
        
        # Вычисляем время напоминания (за default_delay до события)
        reminder_datetime = event_datetime - timedelta(seconds=default_delay)
        
        # Проверяем, не в прошлом ли напоминание
        if reminder_datetime <= now:
            logger.warning(f"Напоминание уже в прошлом, отправляем немедленно")
            # Выполняем задачу немедленно
            result = await execute_scheduled_task(task_name, user_id, user_data)
            return {
                "status": "executed_immediately",
                "task_name": task_name,
                "reason": "reminder_time_passed",
                "event_datetime": event_datetime.isoformat(),
                "result": result
            }
        
        # Вычисляем задержку до напоминания
        delay_seconds = int((reminder_datetime - now).total_seconds())
        
        event_source = "функции" if callable(task_info.get('event_type')) else f"события '{event_type}'"
        human_time = format_seconds_to_human(delay_seconds)
        logger.info(f"⏰ Планируем напоминание '{task_name}' за {format_seconds_to_human(default_delay)} до {event_source} (через {human_time} / {delay_seconds}с)")
        
        # Планируем напоминание
        result = await schedule_task_for_later_with_db(task_name, user_id, user_data, delay_seconds, session_id)
        result['event_datetime'] = event_datetime.isoformat()
        result['reminder_type'] = 'event_reminder'
        
        return result
    else:
        # Обычная задача с фиксированным временем
        human_time = format_seconds_to_human(default_delay)
        logger.info(f"⏰ Планируем задачу '{task_name}' через {human_time} ({default_delay}с) с текстом: '{user_data}'")
        
        # Планируем задачу на фоне с сохранением в БД
        result = await schedule_task_for_later_with_db(task_name, user_id, user_data, default_delay, session_id)
        
        return result

async def schedule_global_handler_for_later(handler_type: str, delay_seconds: int, handler_data: str):
    """
    Планирует выполнение глобального обработчика через указанное время
    
    Args:
        handler_type: Тип глобального обработчика
        delay_seconds: Задержка в секундах
        handler_data: Данные для обработчика (время в секундах как строка)
    """
    # Ищем глобальный обработчик через RouterManager (новая логика)
    router_manager = get_router_manager()
    if router_manager:
        global_handlers = router_manager.get_global_handlers()
        logger.debug(f"🔍 Поиск глобального обработчика '{handler_type}' через RouterManager")
    else:
        global_handlers = _global_handlers
        logger.debug(f"🔍 Поиск глобального обработчика '{handler_type}' через глобальный реестр")
    
    if handler_type not in global_handlers:
        available_handlers = list(global_handlers.keys())
        logger.error(f"❌ Глобальный обработчик '{handler_type}' не найден. Доступные: {available_handlers}")
        raise ValueError(f"Глобальный обработчик '{handler_type}' не найден. Доступные: {available_handlers}")
    
    logger.info(f"🌍 Планируем глобальный обработчик '{handler_type}' через {delay_seconds} секунд")
    
    async def delayed_global_handler():
        await asyncio.sleep(delay_seconds)
        # Передаем данные обработчику (может быть текст анонса или другие данные)
        await execute_global_handler(handler_type, handler_data)
    
    # Запускаем задачу в фоне
    asyncio.create_task(delayed_global_handler())
    
    return {
        "status": "scheduled",
        "handler_type": handler_type,
        "delay_seconds": delay_seconds,
        "scheduled_at": datetime.now().isoformat()
    }

async def execute_global_handler_from_event(handler_type: str, event_info: str):
    """
    Выполняет глобальный обработчик на основе события от ИИ
    
    Args:
        handler_type: Тип глобального обработчика
        event_info: Информация от ИИ (только текст, время задается в декораторе или функции)
    """
    router_manager = get_router_manager()
    if router_manager:
        global_handlers = router_manager.get_global_handlers()
    else:
        global_handlers = _global_handlers
    
    if handler_type not in global_handlers:
        raise ValueError(f"Глобальный обработчик '{handler_type}' не найден")
    
    handler_info = global_handlers[handler_type]
    default_delay = handler_info.get('default_delay')
    event_type = handler_info.get('event_type')
    
    # Время всегда берется из декоратора, ИИ может передавать только текст
    if default_delay is None:
        raise ValueError(f"Для глобального обработчика '{handler_type}' не указано время в декораторе (параметр delay)")
    
    # event_info содержит только текст для обработчика (если ИИ не передал - пустая строка)
    handler_data = event_info.strip() if event_info else ""
    
    # Если указан event_type, вычисляем время относительно события
    if event_type:
        event_datetime = None
        
        # Проверяем тип event_type: строка или функция
        if callable(event_type):
            # ВАРИАНТ 2: Функция - вызываем для получения datetime
            logger.info(f"🌍 Глобальный обработчик '{handler_type}' - вызываем функцию для получения времени")
            
            try:
                # Вызываем функцию (только с handler_data для глобальных)
                event_datetime = await event_type(handler_data)
                
                if not isinstance(event_datetime, datetime):
                    raise ValueError(f"Функция event_type должна вернуть datetime, получен {type(event_datetime)}")
                
                logger.info(f"✅ Функция вернула время события: {event_datetime}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка в функции event_type: {e}")
                # Fallback - планируем через default_delay
                result = await schedule_global_handler_for_later_with_db(handler_type, default_delay, handler_data)
                return result
        
        else:
            # ВАРИАНТ 1: Строка - ищем в БД (можно расширить логику если нужно)
            logger.info(f"🌍 Глобальный обработчик '{handler_type}' - event_type '{event_type}' (строка)")
            # Для глобальных обработчиков пока просто используем default_delay
            # Можно расширить логику если понадобится
            result = await schedule_global_handler_for_later_with_db(handler_type, default_delay, handler_data)
            return result
        
        # Общая логика для функций
        now = datetime.now()
        
        # Вычисляем время напоминания (за default_delay до события)
        reminder_datetime = event_datetime - timedelta(seconds=default_delay)
        
        # Проверяем, не в прошлом ли напоминание
        if reminder_datetime <= now:
            logger.warning(f"Напоминание глобального события уже в прошлом, выполняем немедленно")
            # Выполняем немедленно
            result = await execute_global_handler(handler_type, handler_data)
            return {
                "status": "executed_immediately",
                "handler_type": handler_type,
                "reason": "reminder_time_passed",
                "event_datetime": event_datetime.isoformat(),
                "result": result
            }
        
        # Вычисляем задержку до напоминания
        delay_seconds = int((reminder_datetime - now).total_seconds())
        
        human_time = format_seconds_to_human(delay_seconds)
        logger.info(f"🌍 Планируем глобальный обработчик '{handler_type}' за {format_seconds_to_human(default_delay)} до события (через {human_time} / {delay_seconds}с)")
        
        # Планируем обработчик
        result = await schedule_global_handler_for_later_with_db(handler_type, delay_seconds, handler_data)
        result['event_datetime'] = event_datetime.isoformat()
        result['reminder_type'] = 'global_event_reminder'
        
        return result
    
    else:
        # Обычный глобальный обработчик с фиксированной задержкой
        logger.info(f"🌍 Планируем глобальный обработчик '{handler_type}' через {default_delay}с с данными: '{handler_data}'")
        
        # Планируем обработчик на фоне с сохранением в БД
        result = await schedule_global_handler_for_later_with_db(handler_type, default_delay, handler_data)
        
        return result


# =============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БД СОБЫТИЙ
# =============================================================================

def get_supabase_client():
    """Получает клиент Supabase из глобальных переменных"""
    import sys
    current_module = sys.modules[__name__]
    supabase_client = getattr(current_module, 'supabase_client', None)
    
    # Если не найден в decorators, пробуем получить из bot_utils
    if not supabase_client:
        try:
            bot_utils_module = sys.modules.get('smart_bot_factory.core.bot_utils')
            if bot_utils_module:
                supabase_client = getattr(bot_utils_module, 'supabase_client', None)
        except:
            pass
    
    return supabase_client

async def save_immediate_event(
    event_type: str,
    user_id: int,
    event_data: str,
    session_id: str = None
) -> str:
    """Сохраняет событие для немедленного выполнения"""
    
    supabase_client = get_supabase_client()
    if not supabase_client:
        logger.error("❌ Supabase клиент не найден")
        raise RuntimeError("Supabase клиент не инициализирован")
    
    # Проверяем, нужно ли предотвращать дублирование
    router_manager = get_router_manager()
    if router_manager:
        event_handlers = router_manager.get_event_handlers()
    else:
        event_handlers = _event_handlers
    
    event_handler_info = event_handlers.get(event_type, {})
    once_only = event_handler_info.get('once_only', True)
    
    if once_only:
        # Проверяем, было ли уже обработано аналогичное событие для этого пользователя
        already_processed = await check_event_already_processed(event_type, user_id, session_id)
        if already_processed:
            logger.info(f"🔄 Событие '{event_type}' уже обрабатывалось для пользователя {user_id}, пропускаем")
            raise ValueError(f"Событие '{event_type}' уже обрабатывалось (once_only=True)")
    
    event_record = {
        'event_type': event_type,
        'event_category': 'user_event',
        'user_id': user_id,
        'event_data': event_data,
        'scheduled_at': None,  # Немедленное выполнение
        'status': 'immediate',
        'session_id': session_id
    }
    
    try:
        response = supabase_client.client.table('scheduled_events').insert(event_record).execute()
        event_id = response.data[0]['id']
        logger.info(f"💾 Событие сохранено в БД: {event_id}")
        return event_id
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения события в БД: {e}")
        raise

async def save_scheduled_task(
    task_name: str,
    user_id: int,
    user_data: str,
    delay_seconds: int,
    session_id: str = None
) -> str:
    """Сохраняет запланированную задачу"""
    
    supabase_client = get_supabase_client()
    if not supabase_client:
        logger.error("❌ Supabase клиент не найден")
        raise RuntimeError("Supabase клиент не инициализирован")
    
    # Проверяем, нужно ли предотвращать дублирование
    router_manager = get_router_manager()
    if router_manager:
        scheduled_tasks = router_manager.get_scheduled_tasks()
    else:
        scheduled_tasks = _scheduled_tasks
    
    task_info = scheduled_tasks.get(task_name, {})
    once_only = task_info.get('once_only', True)
    
    if once_only:
        # Проверяем, была ли уже запланирована аналогичная задача для этого пользователя
        already_processed = await check_event_already_processed(task_name, user_id, session_id)
        if already_processed:
            logger.info(f"🔄 Задача '{task_name}' уже запланирована для пользователя {user_id}, пропускаем")
            raise ValueError(f"Задача '{task_name}' уже запланирована (once_only=True)")
    
    scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
    
    event_record = {
        'event_type': task_name,
        'event_category': 'scheduled_task',
        'user_id': user_id,
        'event_data': user_data,
        'scheduled_at': scheduled_at.isoformat(),
        'status': 'pending',
        'session_id': session_id
    }
    
    try:
        response = supabase_client.client.table('scheduled_events').insert(event_record).execute()
        event_id = response.data[0]['id']
        logger.info(f"⏰ Запланированная задача сохранена в БД: {event_id} (через {delay_seconds}с)")
        return event_id
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения запланированной задачи в БД: {e}")
        raise

async def save_global_event(
    handler_type: str,
    handler_data: str,
    delay_seconds: int = 0
) -> str:
    """Сохраняет глобальное событие"""
    
    supabase_client = get_supabase_client()
    if not supabase_client:
        logger.error("❌ Supabase клиент не найден")
        raise RuntimeError("Supabase клиент не инициализирован")
    
    # Проверяем, нужно ли предотвращать дублирование
    router_manager = get_router_manager()
    if router_manager:
        global_handlers = router_manager.get_global_handlers()
    else:
        global_handlers = _global_handlers
    
    handler_info = global_handlers.get(handler_type, {})
    once_only = handler_info.get('once_only', True)
    
    if once_only:
        # Проверяем, было ли уже запланировано аналогичное глобальное событие
        already_processed = await check_event_already_processed(handler_type, user_id=None)
        if already_processed:
            logger.info(f"🔄 Глобальное событие '{handler_type}' уже запланировано, пропускаем")
            raise ValueError(f"Глобальное событие '{handler_type}' уже запланировано (once_only=True)")
    
    scheduled_at = None
    status = 'immediate'
    
    if delay_seconds > 0:
        scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        status = 'pending'
    
    event_record = {
        'event_type': handler_type,
        'event_category': 'global_handler',
        'user_id': None,  # Глобальное событие
        'event_data': handler_data,
        'scheduled_at': scheduled_at.isoformat() if scheduled_at else None,
        'status': status
    }
    
    try:
        response = supabase_client.client.table('scheduled_events').insert(event_record).execute()
        event_id = response.data[0]['id']
        logger.info(f"🌍 Глобальное событие сохранено в БД: {event_id}")
        return event_id
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения глобального события в БД: {e}")
        raise

async def update_event_result(
    event_id: str,
    status: str,
    result_data: Any = None,
    error_message: str = None
):
    """Обновляет результат выполнения события"""
    
    supabase_client = get_supabase_client()
    if not supabase_client:
        logger.error("❌ Supabase клиент не найден")
        return
    
    update_data = {
        'status': status,
        'executed_at': datetime.now(timezone.utc).isoformat()
    }
    
    if result_data:
        import json
        update_data['result_data'] = json.dumps(result_data, ensure_ascii=False)
    
    if error_message:
        update_data['last_error'] = error_message
        # Получаем текущее количество попыток
        try:
            current_retry = supabase_client.client.table('scheduled_events').select('retry_count').eq('id', event_id).execute().data[0]['retry_count']
            update_data['retry_count'] = current_retry + 1
        except:
            update_data['retry_count'] = 1
    
    try:
        supabase_client.client.table('scheduled_events').update(update_data).eq('id', event_id).execute()
        logger.info(f"📝 Результат события {event_id} обновлен: {status}")
    except Exception as e:
        logger.error(f"❌ Ошибка обновления результата события {event_id}: {e}")

async def get_pending_events(limit: int = 50) -> list:
    """Получает события готовые к выполнению СЕЙЧАС"""
    
    supabase_client = get_supabase_client()
    if not supabase_client:
        logger.error("❌ Supabase клиент не найден")
        return []
    
    try:
        now = datetime.now(timezone.utc).isoformat()
        
        response = supabase_client.client.table('scheduled_events')\
            .select('*')\
            .in_('status', ['pending', 'immediate'])\
            .or_(f'scheduled_at.is.null,scheduled_at.lte.{now}')\
            .order('created_at')\
            .limit(limit)\
            .execute()
        
        return response.data
    except Exception as e:
        logger.error(f"❌ Ошибка получения событий из БД: {e}")
        return []

async def get_pending_events_in_next_minute(limit: int = 100) -> list:
    """Получает события готовые к выполнению в течение следующей минуты"""
    
    supabase_client = get_supabase_client()
    if not supabase_client:
        logger.error("❌ Supabase клиент не найден")
        return []
    
    try:
        now = datetime.now(timezone.utc)
        next_minute = now + timedelta(seconds=60)
        
        response = supabase_client.client.table('scheduled_events')\
            .select('*')\
            .in_('status', ['pending', 'immediate'])\
            .or_(f'scheduled_at.is.null,scheduled_at.lte.{next_minute.isoformat()}')\
            .order('created_at')\
            .limit(limit)\
            .execute()
        
        return response.data
    except Exception as e:
        logger.error(f"❌ Ошибка получения событий из БД: {e}")
        return []

async def background_event_processor():
    """Фоновый процессор для ВСЕХ типов событий включая админские (проверяет БД каждую минуту)"""
    
    logger.info("🔄 Запуск фонового процессора событий (user_event, scheduled_task, global_handler, admin_event)")
    
    while True:
        try:
            # Получаем события готовые к выполнению в следующую минуту
            pending_events = await get_pending_events_in_next_minute(limit=100)
            
            if pending_events:
                logger.info(f"📋 Найдено {len(pending_events)} событий для обработки")
                
                for event in pending_events:
                    try:
                        event_type = event['event_type']
                        event_category = event['event_category']
                        user_id = event.get('user_id')
                        session_id = event.get('session_id')
                        
                        # ========== ОБРАБОТКА АДМИНСКИХ СОБЫТИЙ ==========
                        if event_category == 'admin_event':
                            try:
                                # Обрабатываем и получаем результат
                                result = await process_admin_event(event)
                                
                                # Сохраняем результат в result_data
                                import json
                                supabase_client = get_supabase_client()
                                supabase_client.client.table('scheduled_events').update({
                                    'status': 'completed',
                                    'executed_at': datetime.now(timezone.utc).isoformat(),
                                    'result_data': json.dumps(result, ensure_ascii=False) if result else None
                                }).eq('id', event['id']).execute()
                                
                                logger.info(f"✅ Админское событие {event['id']} выполнено")
                                continue
                                
                            except Exception as e:
                                logger.error(f"❌ Ошибка обработки админского события {event['id']}: {e}")
                                
                                # Обновляем статус на failed
                                supabase_client = get_supabase_client()
                                supabase_client.client.table('scheduled_events').update({
                                    'status': 'failed',
                                    'last_error': str(e),
                                    'executed_at': datetime.now(timezone.utc).isoformat()
                                }).eq('id', event['id']).execute()
                                continue
                        
                        # ========== ОБРАБОТКА USER СОБЫТИЙ ==========
                        if event_category == 'user_event':
                            router_manager = get_router_manager()
                            if router_manager:
                                event_handlers = router_manager.get_event_handlers()
                            else:
                                event_handlers = _event_handlers
                            
                            event_handler_info = event_handlers.get(event_type, {})
                            once_only = event_handler_info.get('once_only', True)
                            
                            if once_only:
                                # Проверяем, было ли уже выполнено это событие для данного пользователя
                                supabase_client = get_supabase_client()
                                check_query = supabase_client.client.table('scheduled_events')\
                                    .select('id')\
                                    .eq('event_type', event_type)\
                                    .eq('user_id', user_id)\
                                    .eq('status', 'completed')\
                                    .neq('id', event['id'])  # Исключаем текущее событие
                                
                                if session_id:
                                    check_query = check_query.eq('session_id', session_id)
                                
                                existing = check_query.execute()
                                
                                if existing.data:
                                    await update_event_result(event['id'], 'cancelled', {"reason": "already_executed_once_only"})
                                    logger.info(f"⛔ Событие {event['id']} ({event_type}) пропущено: уже выполнялось для пользователя {user_id} (once_only=True)")
                                    continue
                        
                        # Для scheduled_task - проверяем smart_check и once_only
                        if event_category == 'scheduled_task':
                            router_manager = get_router_manager()
                            scheduled_tasks = router_manager.get_scheduled_tasks() if router_manager else _scheduled_tasks
                            task_info = scheduled_tasks.get(event_type, {})
                            use_smart_check = task_info.get('smart_check', True)
                            once_only = task_info.get('once_only', True)
                            
                            # Проверяем once_only для задач
                            if once_only:
                                supabase_client = get_supabase_client()
                                check_query = supabase_client.client.table('scheduled_events')\
                                    .select('id')\
                                    .eq('event_type', event_type)\
                                    .eq('user_id', user_id)\
                                    .eq('status', 'completed')\
                                    .neq('id', event['id'])
                                
                                if session_id:
                                    check_query = check_query.eq('session_id', session_id)
                                
                                existing = check_query.execute()
                                
                                if existing.data:
                                    await update_event_result(event['id'], 'cancelled', {"reason": "already_executed_once_only"})
                                    logger.info(f"⛔ Задача {event['id']} ({event_type}) пропущена: уже выполнялась для пользователя {user_id} (once_only=True)")
                                    continue
                            
                            if use_smart_check:
                                # Умная проверка
                                check_result = await smart_execute_check(
                                    event['id'], 
                                    user_id, 
                                    session_id,
                                    event_type,
                                    event['event_data']
                                )
                                
                                if check_result['action'] == 'cancel':
                                    await update_event_result(event['id'], 'cancelled', {"reason": check_result['reason']})
                                    logger.info(f"⛔ Задача {event['id']} отменена: {check_result['reason']}")
                                    continue
                                elif check_result['action'] == 'reschedule':
                                    # Обновляем scheduled_at в БД
                                    new_scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=check_result['new_delay'])
                                    supabase_client = get_supabase_client()
                                    supabase_client.client.table('scheduled_events').update({
                                        'scheduled_at': new_scheduled_at.isoformat(),
                                        'status': 'pending'
                                    }).eq('id', event['id']).execute()
                                    logger.info(f"🔄 Задача {event['id']} перенесена на {check_result['new_delay']}с")
                                    continue
                        
                        # Выполняем событие
                        await process_scheduled_event(event)
                        await update_event_result(event['id'], 'completed', {"processed": True})
                        logger.info(f"✅ Событие {event['id']} выполнено")
                        
                    except Exception as e:
                        logger.error(f"❌ Ошибка обработки события {event['id']}: {e}")
                        await update_event_result(event['id'], 'failed', None, str(e))
            
            await asyncio.sleep(60)  # Проверяем каждую минуту
            
        except Exception as e:
            logger.error(f"❌ Ошибка в фоновом процессоре: {e}")
            await asyncio.sleep(60)

async def process_scheduled_event(event: Dict):
    """Обрабатывает одно событие из БД"""
    
    event_type = event['event_type']
    event_category = event['event_category']
    event_data = event['event_data']
    user_id = event.get('user_id')
    
    logger.info(f"🔄 Обработка события {event['id']}: {event_category}/{event_type}")
    
    if event_category == 'scheduled_task':
        await execute_scheduled_task(event_type, user_id, event_data)
    elif event_category == 'global_handler':
        await execute_global_handler(event_type, event_data)
    elif event_category == 'user_event':
        await execute_event_handler(event_type, user_id, event_data)
    else:
        logger.warning(f"⚠️ Неизвестная категория события: {event_category}")

# =============================================================================
# ОБНОВЛЕННЫЕ ФУНКЦИИ С СОХРАНЕНИЕМ В БД
# =============================================================================

async def schedule_task_for_later_with_db(task_name: str, user_id: int, user_data: str, delay_seconds: int, session_id: str = None):
    """Планирует выполнение задачи через указанное время с сохранением в БД (без asyncio.sleep)"""
    
    # Проверяем через RouterManager или fallback к старым декораторам
    router_manager = get_router_manager()
    if router_manager:
        scheduled_tasks = router_manager.get_scheduled_tasks()
    else:
        scheduled_tasks = _scheduled_tasks
    
    if task_name not in scheduled_tasks:
        import inspect
        frame = inspect.currentframe()
        line_no = frame.f_lineno if frame else "unknown"
        available_tasks = list(scheduled_tasks.keys())
        logger.error(f"❌ [decorators.py:{line_no}] Задача '{task_name}' не найдена. Доступные: {available_tasks}")
        raise ValueError(f"Задача '{task_name}' не найдена")
    
    human_time = format_seconds_to_human(delay_seconds)
    logger.info(f"⏰ Планируем задачу '{task_name}' через {human_time} ({delay_seconds}с) для user_id={user_id}")
    
    # Просто сохраняем в БД - фоновый процессор сам выполнит задачу
    event_id = await save_scheduled_task(task_name, user_id, user_data, delay_seconds, session_id)
    
    logger.info(f"💾 Задача '{task_name}' сохранена в БД с ID {event_id}, будет обработана фоновым процессором")
    
    return {
        "status": "scheduled",
        "task_name": task_name,
        "delay_seconds": delay_seconds,
        "event_id": event_id,
        "scheduled_at": datetime.now(timezone.utc).isoformat()
    }

async def schedule_global_handler_for_later_with_db(handler_type: str, delay_seconds: int, handler_data: str):
    """Планирует выполнение глобального обработчика через указанное время с сохранением в БД (без asyncio.sleep)"""
    
    # Проверяем обработчик через RouterManager или fallback к старым декораторам
    router_manager = get_router_manager()
    if router_manager:
        global_handlers = router_manager.get_global_handlers()
    else:
        global_handlers = _global_handlers
    
    if handler_type not in global_handlers:
        raise ValueError(f"Глобальный обработчик '{handler_type}' не найден")
    
    logger.info(f"🌍 Планируем глобальный обработчик '{handler_type}' через {delay_seconds} секунд")
    
    # Просто сохраняем в БД - фоновый процессор сам выполнит обработчик
    event_id = await save_global_event(handler_type, handler_data, delay_seconds)
    
    logger.info(f"💾 Глобальный обработчик '{handler_type}' сохранен в БД с ID {event_id}, будет обработан фоновым процессором")
    
    return {
        "status": "scheduled",
        "handler_type": handler_type,
        "delay_seconds": delay_seconds,
        "event_id": event_id,
        "scheduled_at": datetime.now(timezone.utc).isoformat()
    }

async def smart_execute_check(event_id: str, user_id: int, session_id: str, task_name: str, user_data: str) -> Dict[str, Any]:
    """
    Умная проверка перед выполнением запланированной задачи
    
    Логика:
    1. Если пользователь перешел на новый этап - отменяем событие
    2. Если прошло меньше времени чем планировалось - переносим на разницу
    3. Если прошло достаточно времени - выполняем
    
    Returns:
        Dict с action: 'execute', 'cancel', 'reschedule'
    """
    supabase_client = get_supabase_client()
    if not supabase_client:
        logger.error("❌ Supabase клиент не найден для умной проверки")
        return {"action": "execute", "reason": "no_supabase_client"}
    
    try:
        # Получаем информацию о последнем сообщении пользователя
        user_info = await supabase_client.get_user_last_message_info(user_id)
        
        if not user_info:
            logger.info(f"🔄 Пользователь {user_id} не найден, выполняем задачу")
            return {"action": "execute", "reason": "user_not_found"}
        
        # Проверяем, изменился ли этап
        stage_changed = await supabase_client.check_user_stage_changed(user_id, session_id)
        if stage_changed:
            logger.info(f"🔄 Пользователь {user_id} перешел на новый этап, отменяем задачу {task_name}")
            return {"action": "cancel", "reason": "user_stage_changed"}
        
        # Получаем информацию о событии из БД
        event_response = supabase_client.client.table('scheduled_events').select(
            'created_at', 'scheduled_at'
        ).eq('id', event_id).execute()
        
        if not event_response.data:
            logger.error(f"❌ Событие {event_id} не найдено в БД")
            return {"action": "execute", "reason": "event_not_found"}
        
        event = event_response.data[0]
        created_at = datetime.fromisoformat(event['created_at'].replace('Z', '+00:00'))
        scheduled_at = datetime.fromisoformat(event['scheduled_at'].replace('Z', '+00:00'))
        last_message_at = datetime.fromisoformat(user_info['last_message_at'].replace('Z', '+00:00'))
        
        # Вычисляем разницу во времени
        now = datetime.now(timezone.utc)
        time_since_creation = (now - created_at).total_seconds()
        time_since_last_message = (now - last_message_at).total_seconds()
        planned_delay = (scheduled_at - created_at).total_seconds()
        
        # Проверяем, писал ли пользователь после создания события
        time_between_creation_and_last_message = (last_message_at - created_at).total_seconds()
        
        logger.info(f"🔄 Анализ для пользователя {user_id}:")
        logger.info(f"   Время с создания события: {time_since_creation:.0f}с")
        logger.info(f"   Время с последнего сообщения: {time_since_last_message:.0f}с")
        logger.info(f"   Запланированная задержка: {planned_delay:.0f}с")
        logger.info(f"   Пользователь писал после создания события: {time_between_creation_and_last_message > 0}")
        
        # Если пользователь писал ПОСЛЕ создания события (недавно активен)
        # И с момента его последнего сообщения прошло меньше planned_delay
        if time_between_creation_and_last_message > 0 and time_since_last_message < planned_delay:
            # Пересчитываем время - отправляем через planned_delay после последнего сообщения
            new_delay = max(0, planned_delay - time_since_last_message)
            logger.info(f"🔄 Переносим задачу на {new_delay:.0f}с (пользователь был активен, через {planned_delay:.0f}с после последнего сообщения)")
            return {
                "action": "reschedule", 
                "new_delay": new_delay,
                "reason": f"user_active_after_event_creation_{new_delay:.0f}s_delay"
            }
        
        # Если прошло достаточно времени с последнего сообщения - выполняем
        if time_since_last_message >= planned_delay:
            logger.info(f"🔄 Выполняем задачу {task_name} для пользователя {user_id} (прошло {time_since_last_message:.0f}с с последнего сообщения)")
            return {"action": "execute", "reason": "time_expired_since_last_message"}
        
        # Если что-то пошло не так - выполняем
        logger.info(f"🔄 Неожиданная ситуация, выполняем задачу {task_name}")
        return {"action": "execute", "reason": "unexpected_situation"}
        
    except Exception as e:
        logger.error(f"❌ Ошибка в умной проверке для пользователя {user_id}: {e}")
        return {"action": "execute", "reason": f"error_in_check: {str(e)}"}

async def check_event_already_processed(event_type: str, user_id: int = None, session_id: str = None) -> bool:
    """
    Проверяет, был ли уже обработан аналогичный event_type для пользователя/сессии
    
    Args:
        event_type: Тип события
        user_id: ID пользователя (для user_event и scheduled_task)
        session_id: ID сессии (для дополнительной проверки)
    
    Returns:
        True если событие уже обрабатывалось или в процессе
    """
    supabase_client = get_supabase_client()
    if not supabase_client:
        logger.error("❌ Supabase клиент не найден для проверки дублирования")
        return False
    
    try:
        # Строим запрос для поиска аналогичных событий
        query = supabase_client.client.table('scheduled_events').select('id').eq('event_type', event_type)
        
        # Для глобальных событий (user_id = None)
        if user_id is None:
            query = query.is_('user_id', 'null')
        else:
            query = query.eq('user_id', user_id)
        
        # Добавляем фильтр по статусам (pending, immediate, completed)
        query = query.in_('status', ['pending', 'immediate', 'completed'])
        
        # Если есть session_id, добавляем его в фильтр
        if session_id:
            query = query.eq('session_id', session_id)
        
        response = query.execute()
        
        if response.data:
            logger.info(f"🔄 Найдено {len(response.data)} аналогичных событий для '{event_type}'")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки дублирования для '{event_type}': {e}")
        return False


async def process_admin_event(event: Dict):
    """
    Обрабатывает одно админское событие - скачивает файлы из Storage и отправляет пользователям
    
    Args:
        event: Событие из БД с данными для отправки
    """
    import json
    import os
    import shutil
    from pathlib import Path
    from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaDocument, InputMediaVideo
    
    event_id = event['id']
    event_name = event['event_type']
    event_data_str = event['event_data']
    
    try:
        event_data = json.loads(event_data_str)
    except Exception as e:
        logger.error(f"❌ Не удалось распарсить event_data для события {event_id}: {e}")
        return {
            'success_count': 0,
            'failed_count': 0,
            'total_users': 0,
            'error': f'Ошибка парсинга event_data: {str(e)}'
        }
    
    segment = event_data.get('segment')
    message_text = event_data.get('message')
    files_metadata = event_data.get('files', [])
    
    logger.info(f"📨 Обработка события '{event_name}': сегмент='{segment}', файлов={len(files_metadata)}")
    
    # Получаем клиенты
    supabase_client = get_supabase_client()
    if not supabase_client:
        logger.error("❌ Supabase клиент не найден")
        return {'success_count': 0, 'failed_count': 0, 'total_users': 0, 'error': 'Нет Supabase клиента'}
    
    from ..handlers.handlers import get_global_var
    bot = get_global_var('bot')
    if not bot:
        logger.error("❌ Бот не найден")
        return {'success_count': 0, 'failed_count': 0, 'total_users': 0, 'error': 'Нет бота'}
    
    # Создаем временные папки
    temp_with_msg = Path("temp_with_msg")
    temp_after_msg = Path("temp_after_msg")
    temp_with_msg.mkdir(exist_ok=True)
    temp_after_msg.mkdir(exist_ok=True)
    
    try:
        # 1. Скачиваем файлы из Storage
        for file_info in files_metadata:
            try:
                file_bytes = await supabase_client.download_event_file(
                    event_id=event_id,
                    storage_path=file_info['storage_path']
                )
                
                # Сохраняем в соответствующую папку
                if file_info['stage'] == 'with_message':
                    file_path = temp_with_msg / file_info['original_name']
                else:
                    file_path = temp_after_msg / file_info['original_name']
                
                with open(file_path, 'wb') as f:
                    f.write(file_bytes)
                
                logger.info(f"📥 Скачан файл: {file_path}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка скачивания файла {file_info['name']}: {e}")
                raise
        
        # 2. Получаем пользователей
        users = await supabase_client.get_users_by_segment(segment)
        
        if not users:
            logger.warning(f"⚠️ Нет пользователей для сегмента '{segment}'")
            return {
                'success_count': 0,
                'failed_count': 0,
                'total_users': 0,
                'segment': segment or 'Все',
                'warning': 'Нет пользователей'
            }
        
        success_count = 0
        failed_count = 0
        
        # 3. Отправляем каждому пользователю
        for user in users:
            telegram_id = user['telegram_id']
            
            try:
                # 3.1. Отправляем медиа-группу с сообщением
                files_with_msg = [f for f in files_metadata if f['stage'] == 'with_message']
                
                if files_with_msg:
                    media_group = []
                    first_file = True
                    
                    # Сортируем файлы по порядку
                    sorted_files = sorted(files_with_msg, key=lambda x: x.get('order', 0))
                    
                    for file_info in sorted_files:
                        file_path = temp_with_msg / file_info['original_name']
                        
                        if file_info['type'] == 'photo':
                            media = InputMediaPhoto(
                                media=FSInputFile(file_path),
                                caption=message_text if first_file else None,
                                parse_mode='Markdown' if first_file else None
                            )
                            media_group.append(media)
                        elif file_info['type'] == 'video':
                            media = InputMediaVideo(
                                media=FSInputFile(file_path),
                                caption=message_text if first_file else None,
                                parse_mode='Markdown' if first_file else None
                            )
                            media_group.append(media)
                        
                        first_file = False
                    
                    if media_group:
                        await bot.send_media_group(chat_id=telegram_id, media=media_group)
                else:
                    # Только текст без файлов
                    await bot.send_message(chat_id=telegram_id, text=message_text, parse_mode='Markdown')
                
                # 3.2. Отправляем файлы после сообщения
                files_after = [f for f in files_metadata if f['stage'] == 'after_message']
                
                for file_info in files_after:
                    file_path = temp_after_msg / file_info['original_name']
                    
                    if file_info['type'] == 'document':
                        await bot.send_document(chat_id=telegram_id, document=FSInputFile(file_path))
                    elif file_info['type'] == 'photo':
                        await bot.send_photo(chat_id=telegram_id, photo=FSInputFile(file_path))
                    elif file_info['type'] == 'video':
                        await bot.send_video(chat_id=telegram_id, video=FSInputFile(file_path))
                
                success_count += 1
                logger.info(f"✅ Отправлено пользователю {telegram_id}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка отправки пользователю {telegram_id}: {e}")
                failed_count += 1
        
        logger.info(f"📊 Результат '{event_name}': успешно={success_count}, ошибок={failed_count}")
        
        # 4. Очистка после успешной отправки
        # 4.1. Удаляем локальные временные файлы
        shutil.rmtree(temp_with_msg, ignore_errors=True)
        shutil.rmtree(temp_after_msg, ignore_errors=True)
        logger.info("🗑️ Временные папки очищены")
        
            # 4.2. Удаляем файлы из Supabase Storage
        try:
            await supabase_client.delete_event_files(event_id)
            logger.info(f"🗑️ Файлы события '{event_id}' удалены из Storage")
        except Exception as e:
            logger.error(f"❌ Ошибка удаления из Storage: {e}")
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'total_users': len(users),
            'segment': segment or 'Все пользователи',
            'files_count': len(files_metadata)
        }
        
    except Exception as e:
        # В случае ошибки все равно чистим временные файлы
        shutil.rmtree(temp_with_msg, ignore_errors=True)
        shutil.rmtree(temp_after_msg, ignore_errors=True)
        logger.error(f"❌ Критическая ошибка обработки события: {e}")
        raise
