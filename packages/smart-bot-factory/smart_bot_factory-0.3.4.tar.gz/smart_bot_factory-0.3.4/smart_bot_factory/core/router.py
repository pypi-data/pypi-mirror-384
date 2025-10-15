"""
EventRouter для Smart Bot Factory - роутер для событий, задач и глобальных обработчиков
"""

from typing import Dict, Any, Callable, Union
import logging

logger = logging.getLogger(__name__)

class EventRouter:
    """
    Роутер для организации обработчиков событий, задач и глобальных обработчиков
    """
    
    def __init__(self, name: str = None):
        """
        Инициализация роутера
        
        Args:
            name: Имя роутера для логирования
        """
        self.name = name or f"EventRouter_{id(self)}"
        self._event_handlers: Dict[str, Dict[str, Any]] = {}
        self._scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self._global_handlers: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"🔄 Создан роутер: {self.name}")
    
    def event_handler(self, event_type: str, notify: bool = False, once_only: bool = True):
        """
        Декоратор для регистрации обработчика события в роутере
        
        Args:
            event_type: Тип события
            notify: Уведомлять ли админов
            once_only: Выполнять ли только один раз
        """
        def decorator(func: Callable) -> Callable:
            self._event_handlers[event_type] = {
                'handler': func,
                'name': func.__name__,
                'notify': notify,
                'once_only': once_only,
                'router': self.name
            }
            
            logger.info(f"📝 Роутер {self.name}: зарегистрирован обработчик события '{event_type}': {func.__name__}")
            
            from functools import wraps
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Ошибка выполнения обработчика '{event_type}' в роутере {self.name}: {e}")
                    raise
            return wrapper
        return decorator
    
    def schedule_task(self, task_name: str, notify: bool = False, smart_check: bool = True, once_only: bool = True, delay: Union[str, int] = None, event_type: Union[str, Callable] = None):
        """
        Декоратор для регистрации запланированной задачи в роутере
        
        Args:
            task_name: Название задачи
            notify: Уведомлять ли админов
            smart_check: Использовать ли умную проверку
            once_only: Выполнять ли только один раз
            delay: Время задержки в удобном формате (например, "1h 30m", "45m", 3600) - ОБЯЗАТЕЛЬНО
            event_type: Источник времени события - ОПЦИОНАЛЬНО:
                - str: Тип события для поиска в БД (например, 'appointment_booking')
                - Callable: Функция async def(user_id, user_data) -> datetime
        """
        def decorator(func: Callable) -> Callable:
            # Время ОБЯЗАТЕЛЬНО должно быть указано
            if delay is None:
                raise ValueError(f"Для задачи '{task_name}' в роутере {self.name} ОБЯЗАТЕЛЬНО нужно указать параметр delay")
            
            # Импортируем функцию парсинга времени
            from .decorators import parse_time_string
            
            # Парсим время
            try:
                default_delay_seconds = parse_time_string(delay)
                if event_type:
                    logger.info(f"⏰ Роутер {self.name}: задача '{task_name}' настроена как напоминание о событии '{event_type}' за {delay} ({default_delay_seconds}с)")
                else:
                    logger.info(f"⏰ Роутер {self.name}: задача '{task_name}' настроена с задержкой: {delay} ({default_delay_seconds}с)")
            except ValueError as e:
                logger.error(f"❌ Ошибка парсинга времени для задачи '{task_name}' в роутере {self.name}: {e}")
                raise
            
            self._scheduled_tasks[task_name] = {
                'handler': func,
                'name': func.__name__,
                'notify': notify,
                'smart_check': smart_check,
                'once_only': once_only,
                'router': self.name,
                'default_delay': default_delay_seconds,
                'event_type': event_type  # Новое поле для типа события
            }
            
            if event_type:
                logger.info(f"⏰ Роутер {self.name}: зарегистрирована задача-напоминание '{task_name}' для события '{event_type}': {func.__name__}")
            else:
                logger.info(f"⏰ Роутер {self.name}: зарегистрирована задача '{task_name}': {func.__name__}")
            
            from functools import wraps
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Ошибка выполнения задачи '{task_name}' в роутере {self.name}: {e}")
                    raise
            return wrapper
        return decorator
    
    def global_handler(self, handler_type: str, notify: bool = False, once_only: bool = True, delay: Union[str, int] = None, event_type: Union[str, Callable] = None):
        """
        Декоратор для регистрации глобального обработчика в роутере
        
        Args:
            handler_type: Тип глобального обработчика
            notify: Уведомлять ли админов
            once_only: Выполнять ли только один раз
            delay: Время задержки в удобном формате (например, "1h 30m", "45m", 3600) - ОБЯЗАТЕЛЬНО
        """
        def decorator(func: Callable) -> Callable:
            # Время ОБЯЗАТЕЛЬНО должно быть указано
            if delay is None:
                raise ValueError(f"Для глобального обработчика '{handler_type}' в роутере {self.name} ОБЯЗАТЕЛЬНО нужно указать параметр delay")
            
            # Импортируем функцию парсинга времени
            from .decorators import parse_time_string
            
            # Парсим время
            try:
                default_delay_seconds = parse_time_string(delay)
                logger.info(f"🌍 Роутер {self.name}: глобальный обработчик '{handler_type}' настроен с задержкой: {delay} ({default_delay_seconds}с)")
            except ValueError as e:
                logger.error(f"❌ Ошибка парсинга времени для глобального обработчика '{handler_type}' в роутере {self.name}: {e}")
                raise
            
            self._global_handlers[handler_type] = {
                'handler': func,
                'name': func.__name__,
                'notify': notify,
                'once_only': once_only,
                'router': self.name,
                'default_delay': default_delay_seconds,
                'event_type': event_type  # Добавляем event_type для глобальных обработчиков
            }
            
            logger.info(f"🌍 Роутер {self.name}: зарегистрирован глобальный обработчик '{handler_type}': {func.__name__}")
            
            from functools import wraps
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Ошибка выполнения глобального обработчика '{handler_type}' в роутере {self.name}: {e}")
                    raise
            return wrapper
        return decorator

    def get_event_handlers(self) -> Dict[str, Dict[str, Any]]:
        """Получает все обработчики событий роутера"""
        return self._event_handlers.copy()
    
    def get_scheduled_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Получает все запланированные задачи роутера"""
        return self._scheduled_tasks.copy()
    
    def get_global_handlers(self) -> Dict[str, Dict[str, Any]]:
        """Получает все глобальные обработчики роутера"""
        return self._global_handlers.copy()
    
    def get_all_handlers(self) -> Dict[str, Dict[str, Any]]:
        """Получает все обработчики роутера"""
        all_handlers = {}
        all_handlers.update(self._event_handlers)
        all_handlers.update(self._scheduled_tasks)
        all_handlers.update(self._global_handlers)
        return all_handlers
    
    def include_router(self, router: 'EventRouter'):
        """
        Включает другой роутер в текущий
        
        Args:
            router: EventRouter для включения
        """
        # Добавляем обработчики событий
        for event_type, handler_info in router.get_event_handlers().items():
            if event_type in self._event_handlers:
                logger.warning(f"⚠️ Конфликт обработчиков событий '{event_type}' между роутерами {self.name} и {router.name}")
            self._event_handlers[event_type] = handler_info
        
        # Добавляем запланированные задачи
        for task_name, task_info in router.get_scheduled_tasks().items():
            if task_name in self._scheduled_tasks:
                logger.warning(f"⚠️ Конфликт задач '{task_name}' между роутерами {self.name} и {router.name}")
            self._scheduled_tasks[task_name] = task_info
        
        # Добавляем глобальные обработчики
        for handler_type, handler_info in router.get_global_handlers().items():
            if handler_type in self._global_handlers:
                logger.warning(f"⚠️ Конфликт глобальных обработчиков '{handler_type}' между роутерами {self.name} и {router.name}")
            self._global_handlers[handler_type] = handler_info
        
        logger.info(f"🔗 Роутер {self.name}: включен роутер {router.name}")
    
    def __repr__(self):
        return f"EventRouter(name='{self.name}', events={len(self._event_handlers)}, tasks={len(self._scheduled_tasks)}, globals={len(self._global_handlers)})"