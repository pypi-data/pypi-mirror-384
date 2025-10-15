"""
Строитель ботов для Smart Bot Factory
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from ..config import Config
from ..integrations.openai_client import OpenAIClient
from ..integrations.supabase_client import SupabaseClient
from ..core.conversation_manager import ConversationManager
from ..admin.admin_manager import AdminManager
from ..analytics.analytics_manager import AnalyticsManager
from ..utils.prompt_loader import PromptLoader
from ..core.decorators import get_handlers_for_prompt
from ..core.router_manager import RouterManager

logger = logging.getLogger(__name__)

class BotBuilder:
    """
    Строитель ботов, который использует существующие файлы проекта
    и добавляет новые возможности через декораторы
    """
    
    def __init__(self, bot_id: str, config_dir: Optional[Path] = None):
        """
        Инициализация строителя бота
        
        Args:
            bot_id: Идентификатор бота
            config_dir: Путь к директории конфигурации (по умолчанию configs/bot_id)
        """
        self.bot_id = bot_id
        self.config_dir = config_dir or Path("bots") / bot_id
        
        # Компоненты бота
        self.config: Optional[Config] = None
        self.openai_client: Optional[OpenAIClient] = None
        self.supabase_client: Optional[SupabaseClient] = None
        self.conversation_manager: Optional[ConversationManager] = None
        self.admin_manager: Optional[AdminManager] = None
        self.analytics_manager: Optional[AnalyticsManager] = None
        self.prompt_loader: Optional[PromptLoader] = None
        self.router_manager: Optional[RouterManager] = None
        self._telegram_routers: List = []  # Список Telegram роутеров
        self._start_handlers: List = []  # Список обработчиков on_start
        
        # Хуки для кастомизации process_user_message
        self._message_validators: List = []  # Валидация ДО обработки
        self._prompt_enrichers: List = []    # Обогащение системного промпта
        self._context_enrichers: List = []   # Обогащение контекста для AI
        self._response_processors: List = [] # Обработка ответа AI
        self._send_filters: List = []        # Фильтры перед отправкой пользователю
        
        # Кастомный PromptLoader
        self._custom_prompt_loader = None
        
        # Кастомный процессор событий
        self._custom_event_processor = None
        
        # Флаги инициализации
        self._initialized = False
        
        logger.info(f"🏗️ Создан BotBuilder для бота: {bot_id}")
    
    async def build(self) -> 'BotBuilder':
        """
        Строит и инициализирует все компоненты бота
        
        Returns:
            BotBuilder: Возвращает self для цепочки вызовов
        """
        if self._initialized:
            logger.warning(f"⚠️ Бот {self.bot_id} уже инициализирован")
            return self
        
        try:
            logger.info(f"🚀 Начинаем сборку бота {self.bot_id}")
            
            # 1. Инициализируем конфигурацию
            await self._init_config()
            
            # 2. Инициализируем клиенты
            await self._init_clients()
            
            # 3. Инициализируем менеджеры
            await self._init_managers()
            
            # 4. Обновляем промпты с информацией о доступных инструментах
            await self._update_prompts_with_tools()
            
            self._initialized = True
            logger.info(f"✅ Бот {self.bot_id} успешно собран и готов к работе")
            
            return self
            
        except Exception as e:
            logger.error(f"❌ Ошибка при сборке бота {self.bot_id}: {e}")
            raise
    
    async def _init_config(self):
        """Инициализация конфигурации"""
        logger.info(f"⚙️ Инициализация конфигурации для {self.bot_id}")
        
        # Устанавливаем BOT_ID в переменные окружения
        os.environ['BOT_ID'] = self.bot_id
        
        # Загружаем .env файл если существует
        env_file = self.config_dir / ".env"
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
            logger.info(f"📄 Загружен .env файл: {env_file}")
        
        # Устанавливаем путь к промптам относительно папки бота
        prompts_subdir = os.environ.get("PROMT_FILES_DIR", "prompts")
        logger.info(f"🔍 PROMT_FILES_DIR из .env: {prompts_subdir}")
        
        prompts_dir = self.config_dir / prompts_subdir
        logger.info(f"🔍 Путь к промптам: {prompts_dir}")
        logger.info(f"🔍 Существует ли папка: {prompts_dir.exists()}")
        
        # ВАЖНО: Устанавливаем правильный путь ДО создания Config
        os.environ["PROMT_FILES_DIR"] = str(prompts_dir)
        logger.info(f"📁 Установлен путь к промптам: {prompts_dir}")
        
        # Создаем конфигурацию
        logger.info(f"🔍 PROMT_FILES_DIR перед созданием Config: {os.environ.get('PROMT_FILES_DIR')}")
        self.config = Config()
        logger.info(f"✅ Конфигурация инициализирована")
    
    async def _init_clients(self):
        """Инициализация клиентов"""
        logger.info(f"🔌 Инициализация клиентов для {self.bot_id}")
        
        # OpenAI клиент
        self.openai_client = OpenAIClient(
            api_key=self.config.OPENAI_API_KEY,
            model=self.config.OPENAI_MODEL,
            max_tokens=self.config.OPENAI_MAX_TOKENS,
            temperature=self.config.OPENAI_TEMPERATURE
        )
        logger.info(f"✅ OpenAI клиент инициализирован")
        
        # Supabase клиент
        self.supabase_client = SupabaseClient(
            url=self.config.SUPABASE_URL,
            key=self.config.SUPABASE_KEY,
            bot_id=self.bot_id
        )
        await self.supabase_client.initialize()
        logger.info(f"✅ Supabase клиент инициализирован")
    
    async def _init_managers(self):
        """Инициализация менеджеров"""
        logger.info(f"👥 Инициализация менеджеров для {self.bot_id}")
        
        # Admin Manager
        self.admin_manager = AdminManager(self.config, self.supabase_client)
        await self.admin_manager.sync_admins_from_config()
        logger.info(f"✅ Admin Manager инициализирован")
        
        # Analytics Manager
        self.analytics_manager = AnalyticsManager(self.supabase_client)
        logger.info(f"✅ Analytics Manager инициализирован")
        
        # Conversation Manager
        parse_mode = os.environ.get('MESSAGE_PARSE_MODE', 'Markdown')
        admin_session_timeout_minutes = int(os.environ.get('ADMIN_SESSION_TIMEOUT_MINUTES', '30'))
        
        self.conversation_manager = ConversationManager(self.supabase_client, self.admin_manager, parse_mode, admin_session_timeout_minutes)
        logger.info(f"✅ Conversation Manager инициализирован")
        
        # Router Manager (создаем только если еще не создан)
        if not self.router_manager:
            self.router_manager = RouterManager()
            logger.info(f"✅ Router Manager инициализирован")
        else:
            logger.info(f"✅ Router Manager уже был создан ранее")
        
        # Prompt Loader (используем кастомный если установлен)
        if self._custom_prompt_loader:
            self.prompt_loader = self._custom_prompt_loader
            logger.info(f"✅ Используется кастомный Prompt Loader: {type(self.prompt_loader).__name__}")
        else:
            self.prompt_loader = PromptLoader(
                prompts_dir=self.config.PROMT_FILES_DIR
            )
            logger.info(f"✅ Используется стандартный Prompt Loader")
        
        await self.prompt_loader.validate_prompts()
        logger.info(f"✅ Prompt Loader инициализирован")
    
    async def _update_prompts_with_tools(self):
        """
        Обновляет промпты информацией о доступных обработчиках событий
        """
        logger.info(f"🔧 Обновление промптов с информацией об обработчиках")
        
        # Получаем информацию о доступных обработчиках
        # Сначала пробуем получить из роутеров, если нет - из старых декораторов
        if self.router_manager:
            event_handlers_info = self.router_manager.get_handlers_for_prompt()
        else:
            event_handlers_info = get_handlers_for_prompt()
        
        # Если есть обработчики, добавляем их в системный промпт
        if event_handlers_info:
            # Сохраняем информацию о обработчиках для использования в handlers.py
            self._tools_prompt = event_handlers_info
            
            logger.info(f"✅ Промпты обновлены с информацией об обработчиках")
        else:
            self._tools_prompt = ""
            logger.info(f"ℹ️ Нет зарегистрированных обработчиков")
    
    def get_tools_prompt(self) -> str:
        """Возвращает промпт с информацией об инструментах"""
        return getattr(self, '_tools_prompt', '')
    
    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус бота"""
        return {
            "bot_id": self.bot_id,
            "initialized": self._initialized,
            "config_dir": str(self.config_dir),
            "components": {
                "config": self.config is not None,
                "openai_client": self.openai_client is not None,
                "supabase_client": self.supabase_client is not None,
                "conversation_manager": self.conversation_manager is not None,
                "admin_manager": self.admin_manager is not None,
                "analytics_manager": self.analytics_manager is not None,
                "prompt_loader": self.prompt_loader is not None
            },
            "tools": {
                "event_handlers": len(get_handlers_for_prompt().split('\n')) if get_handlers_for_prompt() else 0
            }
        }
    
    def set_global_vars_in_module(self, module_name: str):
        """
        Устанавливает глобальные переменные в указанном модуле для удобного доступа
        
        Args:
            module_name: Имя модуля (например, 'valera', 'my_bot')
        """
        try:
            import sys
            import importlib
            
            # Получаем модуль бота
            bot_module = sys.modules.get(module_name)
            if not bot_module:
                # Пытаемся импортировать модуль, если он не загружен
                try:
                    bot_module = importlib.import_module(module_name)
                    logger.info(f"📦 Модуль '{module_name}' импортирован для установки глобальных переменных")
                except ImportError as ie:
                    logger.warning(f"⚠️ Не удалось импортировать модуль '{module_name}': {ie}")
                    return
            
            # Устанавливаем глобальные переменные
            bot_module.supabase_client = self.supabase_client
            bot_module.openai_client = self.openai_client
            bot_module.config = self.config
            bot_module.admin_manager = self.admin_manager
            bot_module.analytics_manager = self.analytics_manager
            bot_module.conversation_manager = self.conversation_manager
            bot_module.prompt_loader = self.prompt_loader
            
            logger.info(f"✅ Глобальные переменные установлены в модуле '{module_name}'")
            
        except Exception as e:
            logger.warning(f"⚠️ Не удалось установить глобальные переменные в модуле '{module_name}': {e}")
    
    def register_router(self, router):
        """
        Регистрирует роутер событий в менеджере роутеров
        
        Args:
            router: EventRouter для регистрации
        """
        # Если RouterManager еще не инициализирован, создаем его
        if not self.router_manager:
            from ..core.router_manager import RouterManager
            self.router_manager = RouterManager()
            logger.info(f"✅ Router Manager создан для регистрации роутера '{router.name}'")
        
        self.router_manager.register_router(router)
        logger.info(f"✅ Роутер событий '{router.name}' зарегистрирован в боте {self.bot_id}")
    
    def register_routers(self, *event_routers):
        """
        Регистрирует несколько роутеров событий одновременно
        
        Args:
            *event_routers: Произвольное количество EventRouter
            
        Example:
            bot_builder.register_routers(event_router1, event_router2, event_router3)
        """
        if not event_routers:
            logger.warning("⚠️ register_routers вызван без аргументов")
            return
        
        for router in event_routers:
            self.register_router(router)
        
        logger.info(f"✅ Зарегистрировано {len(event_routers)} роутеров событий")
    
    def register_telegram_router(self, telegram_router):
        """
        Регистрирует Telegram роутер для обработки команд и сообщений
        
        Args:
            telegram_router: aiogram.Router для регистрации
            
        Example:
            from aiogram import Router
            from aiogram.filters import Command
            
            # Создаем обычный aiogram Router
            my_router = Router(name="my_commands")
            
            @my_router.message(Command("price"))
            async def price_handler(message: Message):
                await message.answer("Наши цены...")
            
            # Регистрируем в боте
            bot_builder.register_telegram_router(my_router)
        """
        from aiogram import Router as AiogramRouter
        
        if not isinstance(telegram_router, AiogramRouter):
            raise TypeError(f"Ожидается aiogram.Router, получен {type(telegram_router)}")
        
        self._telegram_routers.append(telegram_router)
        router_name = getattr(telegram_router, 'name', 'unnamed')
        logger.info(f"✅ Telegram роутер '{router_name}' зарегистрирован в боте {self.bot_id}")
    
    def register_telegram_routers(self, *telegram_routers):
        """
        Регистрирует несколько Telegram роутеров одновременно
        
        Args:
            *telegram_routers: Произвольное количество aiogram.Router
            
        Example:
            from aiogram import Router
            
            router1 = Router(name="commands")
            router2 = Router(name="callbacks")
            
            bot_builder.register_telegram_routers(router1, router2)
        """
        if not telegram_routers:
            logger.warning("⚠️ register_telegram_routers вызван без аргументов")
            return
        
        for router in telegram_routers:
            self.register_telegram_router(router)
        
        logger.info(f"✅ Зарегистрировано {len(telegram_routers)} Telegram роутеров")
    
    def on_start(self, handler):
        """
        Регистрирует обработчик, который вызывается после стандартной логики /start
        
        Обработчик получает доступ к:
        - user_id: int - ID пользователя Telegram
        - session_id: str - ID созданной сессии
        - message: Message - Объект сообщения от aiogram
        - state: FSMContext - Контекст состояния
        
        Args:
            handler: Async функция с сигнатурой:
                     async def handler(user_id: int, session_id: str, message: Message, state: FSMContext)
        
        Example:
            @bot_builder.on_start
            async def my_start_handler(user_id, session_id, message, state):
                keyboard = InlineKeyboardMarkup(...)
                await message.answer("Выберите действие:", reply_markup=keyboard)
        """
        if not callable(handler):
            raise TypeError(f"Обработчик должен быть callable, получен {type(handler)}")
        
        self._start_handlers.append(handler)
        logger.info(f"✅ Зарегистрирован обработчик on_start: {handler.__name__}")
        return handler  # Возвращаем handler для использования как декоратор
    
    def get_start_handlers(self) -> List:
        """Получает список обработчиков on_start"""
        return self._start_handlers.copy()
    
    def set_prompt_loader(self, prompt_loader):
        """
        Устанавливает кастомный PromptLoader
        
        Должен быть вызван ДО build()
        
        Args:
            prompt_loader: Экземпляр PromptLoader или его наследника (например UserPromptLoader)
            
        Example:
            from smart_bot_factory.utils import UserPromptLoader
            
            # Использовать UserPromptLoader с автопоиском prompts_dir
            custom_loader = UserPromptLoader("my-bot")
            bot_builder.set_prompt_loader(custom_loader)
            
            # Или кастомный наследник
            class MyPromptLoader(UserPromptLoader):
                def __init__(self, bot_id):
                    super().__init__(bot_id)
                    self.extra_file = self.prompts_dir / 'extra.txt'
            
            my_loader = MyPromptLoader("my-bot")
            bot_builder.set_prompt_loader(my_loader)
        """
        self._custom_prompt_loader = prompt_loader
        logger.info(f"✅ Установлен кастомный PromptLoader: {type(prompt_loader).__name__}")
    
    def set_event_processor(self, custom_processor):
        """
        Устанавливает кастомную функцию для обработки событий
        
        Полностью заменяет стандартную process_events из bot_utils
        
        Args:
            custom_processor: async def(session_id: str, events: list, user_id: int)
            
        Example:
            from smart_bot_factory.message import get_bot
            from smart_bot_factory.core.decorators import execute_event_handler
            
            async def my_process_events(session_id, events, user_id):
                '''Моя кастомная обработка событий'''
                bot = get_bot()
                
                for event in events:
                    event_type = event.get('тип')
                    event_info = event.get('инфо')
                    
                    if event_type == 'запись':
                        # Кастомная логика для бронирования
                        telegram_user = await bot.get_chat(user_id)
                        name = telegram_user.first_name or 'Клиент'
                        # ... ваша обработка
                    else:
                        # Для остальных - стандартная обработка
                        await execute_event_handler(event_type, user_id, event_info)
            
            bot_builder.set_event_processor(my_process_events)
        """
        if not callable(custom_processor):
            raise TypeError(f"Процессор должен быть callable, получен {type(custom_processor)}")
        
        self._custom_event_processor = custom_processor
        logger.info(f"✅ Установлена кастомная функция обработки событий: {custom_processor.__name__}")
    
    # ========== ХУКИ ДЛЯ КАСТОМИЗАЦИИ ОБРАБОТКИ СООБЩЕНИЙ ==========
    
    def validate_message(self, handler):
        """
        Регистрирует валидатор сообщений (вызывается ДО обработки AI)
        
        Если валидатор возвращает False, обработка прерывается
        
        Args:
            handler: async def(message: Message, supabase_client) -> bool
        
        Example:
            @bot_builder.validate_message
            async def check_service_names(message, supabase_client):
                if "неправильное название" in message.text:
                    await message.answer("Пожалуйста, уточните название услуги")
                    return False  # Прерываем обработку
                return True  # Продолжаем
        """
        if not callable(handler):
            raise TypeError(f"Обработчик должен быть callable, получен {type(handler)}")
        
        self._message_validators.append(handler)
        logger.info(f"✅ Зарегистрирован валидатор сообщений: {handler.__name__}")
        return handler
    
    def enrich_prompt(self, handler):
        """
        Регистрирует обогатитель системного промпта
        
        Args:
            handler: async def(system_prompt: str, user_id: int, session_id: str, supabase_client) -> str
        
        Example:
            @bot_builder.enrich_prompt
            async def add_client_info(system_prompt, user_id, session_id, supabase_client):
                session = await supabase_client.get_active_session(user_id)
                phone = session.get('metadata', {}).get('phone')
                if phone:
                    return f"{system_prompt}\\n\\nТелефон клиента: {phone}"
                return system_prompt
        """
        if not callable(handler):
            raise TypeError(f"Обработчик должен быть callable, получен {type(handler)}")
        
        self._prompt_enrichers.append(handler)
        logger.info(f"✅ Зарегистрирован обогатитель промпта: {handler.__name__}")
        return handler
    
    def enrich_context(self, handler):
        """
        Регистрирует обогатитель контекста для AI (messages array)
        
        Args:
            handler: async def(messages: List[dict], user_id: int, session_id: str) -> List[dict]
        
        Example:
            @bot_builder.enrich_context
            async def add_external_data(messages, user_id, session_id):
                # Добавляем данные из внешнего API
                messages.append({
                    "role": "system", 
                    "content": "Дополнительная информация..."
                })
                return messages
        """
        if not callable(handler):
            raise TypeError(f"Обработчик должен быть callable, получен {type(handler)}")
        
        self._context_enrichers.append(handler)
        logger.info(f"✅ Зарегистрирован обогатитель контекста: {handler.__name__}")
        return handler
    
    def process_response(self, handler):
        """
        Регистрирует обработчик ответа AI (ПОСЛЕ получения ответа)
        
        Args:
            handler: async def(response_text: str, ai_metadata: dict, user_id: int) -> tuple[str, dict]
        
        Example:
            @bot_builder.process_response
            async def modify_response(response_text, ai_metadata, user_id):
                # Модифицируем ответ
                if "цена" in response_text.lower():
                    response_text += "\\n\\n💰 Актуальные цены на сайте"
                return response_text, ai_metadata
        """
        if not callable(handler):
            raise TypeError(f"Обработчик должен быть callable, получен {type(handler)}")
        
        self._response_processors.append(handler)
        logger.info(f"✅ Зарегистрирован обработчик ответа: {handler.__name__}")
        return handler
    
    def filter_send(self, handler):
        """
        Регистрирует фильтр отправки (может блокировать отправку пользователю)
        
        Если фильтр возвращает True, сообщение НЕ отправляется
        
        Args:
            handler: async def(user_id: int) -> bool
        
        Example:
            @bot_builder.filter_send
            async def block_during_process(user_id):
                if is_processing(user_id):
                    return True  # Блокируем отправку
                return False  # Разрешаем отправку
            
            # Или совместимый с should_block_ai_response
            @bot_builder.filter_send
            async def should_block_ai_response(user_id):
                # Ваша логика проверки
                return user_is_blocked(user_id)  # True = блокировать
        """
        if not callable(handler):
            raise TypeError(f"Обработчик должен быть callable, получен {type(handler)}")
        
        self._send_filters.append(handler)
        logger.info(f"✅ Зарегистрирован фильтр отправки: {handler.__name__}")
        return handler
    
    def get_message_hooks(self) -> Dict[str, List]:
        """Получает все хуки для обработки сообщений"""
        return {
            'validators': self._message_validators.copy(),
            'prompt_enrichers': self._prompt_enrichers.copy(),
            'context_enrichers': self._context_enrichers.copy(),
            'response_processors': self._response_processors.copy(),
            'send_filters': self._send_filters.copy()
        }
    
    def get_router_manager(self) -> RouterManager:
        """Получает менеджер роутеров событий"""
        return self.router_manager
    
    async def _setup_bot_commands(self, bot):
        """Устанавливает меню команд для бота (разные для админов и пользователей)"""
        from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
        
        try:
            # Команды для обычных пользователей
            user_commands = [
                BotCommand(command="start", description="🚀 Начать/перезапустить бота"),
                BotCommand(command="help", description="❓ Помощь"),
            ]
            
            # Устанавливаем для всех пользователей по умолчанию
            await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
            logger.info("✅ Установлены команды для обычных пользователей")
            
            # Команды для админов (включая команды пользователей + админские)
            admin_commands = [
                BotCommand(command="start", description="🚀 Начать/перезапустить бота"),
                BotCommand(command="help", description="❓ Помощь"),
                BotCommand(command="cancel", description="❌ Отменить текущее действие"),
                BotCommand(command="admin", description="👑 Админ панель"),
                BotCommand(command="stats", description="📊 Статистика"),
                BotCommand(command="chat", description="💬 Начать чат с пользователем"),
                BotCommand(command="chats", description="👥 Активные чаты"),
                BotCommand(command="stop", description="⛔ Остановить текущий чат"),
                BotCommand(command="history", description="📜 История сообщений"),
                BotCommand(command="create_event", description="📝 Создать событие"),
                BotCommand(command="list_events", description="📋 Список событий"),
                BotCommand(command="delete_event", description="🗑️ Удалить событие"),
            ]
            
            # Устанавливаем для каждого админа персональные команды
            for admin_id in self.config.ADMIN_TELEGRAM_IDS:
                try:
                    await bot.set_my_commands(
                        admin_commands, 
                        scope=BotCommandScopeChat(chat_id=admin_id)
                    )
                    logger.info(f"✅ Установлены админские команды для {admin_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось установить команды для админа {admin_id}: {e}")
            
            logger.info(f"✅ Меню команд настроено ({len(self.config.ADMIN_TELEGRAM_IDS)} админов)")
            
        except Exception as e:
            logger.error(f"❌ Ошибка установки команд бота: {e}")
    
    async def start(self):
        """
        Запускает бота (аналог main.py)
        """
        if not self._initialized:
            raise RuntimeError(f"Бот {self.bot_id} не инициализирован. Вызовите build() сначала")
        
        logger.info(f"🚀 Запускаем бота {self.bot_id}")
        
        try:
            # Импортируем необходимые компоненты
            from aiogram import Bot, Dispatcher
            from aiogram.fsm.storage.memory import MemoryStorage
            
            # Создаем бота и диспетчер
            bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
            storage = MemoryStorage()
            dp = Dispatcher(storage=storage)
            
            # Устанавливаем меню команд для бота
            await self._setup_bot_commands(bot)
            
            # Инициализируем базу данных
            await self.supabase_client.initialize()
            
            # Синхронизируем админов из конфигурации
            await self.admin_manager.sync_admins_from_config()
            
            # Проверяем доступность промптов
            prompts_status = await self.prompt_loader.validate_prompts()
            logger.info(f"Статус промптов: {prompts_status}")
            
           
            import importlib
            
            # Устанавливаем глобальные переменные в модулях handlers и admin_logic
            try:
                handlers_module = importlib.import_module('smart_bot_factory.handlers.handlers')
                handlers_module.config = self.config
                handlers_module.bot = bot
                handlers_module.dp = dp
                handlers_module.supabase_client = self.supabase_client
                handlers_module.openai_client = self.openai_client
                handlers_module.prompt_loader = self.prompt_loader
                handlers_module.admin_manager = self.admin_manager
                handlers_module.analytics_manager = self.analytics_manager
                handlers_module.conversation_manager = self.conversation_manager
                handlers_module.start_handlers = self._start_handlers  # Передаем обработчики on_start
                handlers_module.message_hooks = self.get_message_hooks()  # Передаем хуки для обработки сообщений
                handlers_module.custom_event_processor = self._custom_event_processor  # Передаем кастомный процессор событий
                logger.info("✅ Глобальные переменные установлены в handlers")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось установить глобальные переменные в handlers: {e}")
            
            try:
                admin_logic_module = importlib.import_module('smart_bot_factory.admin.admin_logic')
                admin_logic_module.config = self.config
                admin_logic_module.bot = bot
                admin_logic_module.dp = dp
                admin_logic_module.supabase_client = self.supabase_client
                admin_logic_module.openai_client = self.openai_client
                admin_logic_module.prompt_loader = self.prompt_loader
                admin_logic_module.admin_manager = self.admin_manager
                admin_logic_module.analytics_manager = self.analytics_manager
                admin_logic_module.conversation_manager = self.conversation_manager
                logger.info("✅ Глобальные переменные установлены в admin_logic")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось установить глобальные переменные в admin_logic: {e}")
            
            # Также устанавливаем в bot_utils
            try:
                bot_utils_module = importlib.import_module('smart_bot_factory.core.bot_utils')
                bot_utils_module.config = self.config
                bot_utils_module.bot = bot
                bot_utils_module.dp = dp
                bot_utils_module.supabase_client = self.supabase_client
                bot_utils_module.openai_client = self.openai_client
                bot_utils_module.prompt_loader = self.prompt_loader
                bot_utils_module.admin_manager = self.admin_manager
                bot_utils_module.analytics_manager = self.analytics_manager
                bot_utils_module.conversation_manager = self.conversation_manager
                bot_utils_module.custom_event_processor = self._custom_event_processor  # Передаем кастомный процессор событий
                logger.info("✅ Глобальные переменные установлены в bot_utils")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось установить глобальные переменные в bot_utils: {e}")
            
            # Также устанавливаем в debug_routing
            try:
                from ..utils import debug_routing
                debug_routing.config = self.config
                debug_routing.bot = bot
                debug_routing.dp = dp
                debug_routing.supabase_client = self.supabase_client
                debug_routing.openai_client = self.openai_client
                debug_routing.prompt_loader = self.prompt_loader
                debug_routing.admin_manager = self.admin_manager
                debug_routing.conversation_manager = self.conversation_manager
                logger.info("✅ Глобальные переменные установлены в debug_routing")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось установить глобальные переменные в debug_routing: {e}")
            
            # Теперь импортируем и настраиваем обработчики
            from ..handlers.handlers import setup_handlers
            from ..admin.admin_logic import setup_admin_handlers
            from ..admin.admin_events import setup_admin_events_handlers
            from ..core.bot_utils import setup_utils_handlers
            
            # Подключаем пользовательские Telegram роутеры ПЕРВЫМИ (высший приоритет)
            if self._telegram_routers:
                logger.info(f"🔗 Подключаем {len(self._telegram_routers)} пользовательских Telegram роутеров")
                for telegram_router in self._telegram_routers:
                    dp.include_router(telegram_router)
                    router_name = getattr(telegram_router, 'name', 'unnamed')
                    logger.info(f"✅ Подключен Telegram роутер: {router_name}")
            
            # Настраиваем стандартные обработчики (меньший приоритет)
            setup_utils_handlers(dp)    # Утилитарные команды (/status, /help)
            setup_admin_handlers(dp)    # Админские команды (/админ, /стат, /чат)
            setup_admin_events_handlers(dp)  # Админские события (/создать_событие)
            setup_handlers(dp)          # Основные пользовательские обработчики
            
            # Устанавливаем глобальные переменные в модуле бота для удобного доступа
            self.set_global_vars_in_module(self.bot_id)
            
            # Устанавливаем роутер-менеджер в декораторы ПЕРЕД настройкой обработчиков
            if self.router_manager:
                from ..core.decorators import set_router_manager
                set_router_manager(self.router_manager)
                logger.info("✅ RouterManager установлен в decorators")
                
                # Обновляем обработчики после установки RouterManager
                # (на случай если декораторы выполнялись после добавления роутера)
                self.router_manager._update_combined_handlers()
                logger.info("✅ RouterManager обработчики обновлены")
            
            # Фоновые задачи выполняются через asyncio.create_task в decorators.py
            
            # Логируем информацию о запуске
            logger.info(f"✅ Бот {self.bot_id} запущен и готов к работе!")
            logger.info(f"   📊 Изоляция данных: bot_id = {self.config.BOT_ID}")
            logger.info(f"   👑 Админов настроено: {len(self.config.ADMIN_TELEGRAM_IDS)}")
            logger.info(f"   📝 Загружено промптов: {len(self.config.PROMPT_FILES)}")
            
            # Запускаем единый фоновый процессор для всех событий
            from ..core.decorators import background_event_processor
            import asyncio
            asyncio.create_task(background_event_processor())
            logger.info("✅ Фоновый процессор событий запущен (user_event, scheduled_task, global_handler, admin_event)")
            
            # Четкое сообщение о запуске
            print(f"\n🤖 БОТ {self.bot_id.upper()} УСПЕШНО ЗАПУЩЕН!")
            print(f"📱 Telegram Bot ID: {self.config.BOT_ID}")
            print(f"👑 Админов: {len(self.config.ADMIN_TELEGRAM_IDS)}")
            print(f"📝 Промптов: {len(self.config.PROMPT_FILES)}")
            print(f"⏳ Ожидание сообщений...")
            print(f"⏹️ Для остановки нажмите Ctrl+C\n")
            
            # Запуск polling (бесконечная обработка сообщений)
            await dp.start_polling(bot)
            
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота {self.bot_id}: {e}")
            import traceback
            logger.error(f"Стек ошибки: {traceback.format_exc()}")
            raise
        finally:
            # Очистка ресурсов при завершении
            if 'bot' in locals():
                await bot.session.close()
