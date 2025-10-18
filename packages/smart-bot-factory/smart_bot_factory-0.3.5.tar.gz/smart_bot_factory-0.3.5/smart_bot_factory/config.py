# Обновленный config.py с автоопределением bot_id

import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv
from typing import List

# Переменные из .env файла загружаются в BotBuilder

logger = logging.getLogger(__name__)

@dataclass
class Config:
    """Конфигурация приложения"""
    
    # 🆕 Bot ID автоматически из переменной окружения (устанавливается в запускалке)
    BOT_ID: str = field(init=False)
    
    # Telegram Bot Token
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    # Supabase настройки
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY: str = os.getenv('SUPABASE_KEY', '')
    
    # OpenAI настройки
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-5-mini')
    OPENAI_MAX_TOKENS: int = int(os.getenv('OPENAI_MAX_TOKENS', '1500'))
    OPENAI_TEMPERATURE: float = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    
    # Каталог с файлами промптов
    PROMT_FILES_DIR: str = os.getenv('PROMT_FILES_DIR', 'prompts')
    
    # Файл после стартого сообщения
    WELCOME_FILE_DIR: str = os.getenv('WELCOME_FILE_URL', 'welcome_file')
    WELCOME_FILE_MSG: str = os.getenv('WELCOME_FILE_MSG', 'welcome_file_msg.txt')
    
    # Настройки базы данных
    MAX_CONTEXT_MESSAGES: int = int(os.getenv('MAX_CONTEXT_MESSAGES', '50'))
    
    # Настройки логирования
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

    # Настройки продаж
    LEAD_QUALIFICATION_THRESHOLD: int = int(os.getenv('LEAD_QUALIFICATION_THRESHOLD', '7'))
    SESSION_TIMEOUT_HOURS: int = int(os.getenv('SESSION_TIMEOUT_HOURS', '24'))
    
    # Настройки форматирования сообщений
    MESSAGE_PARSE_MODE: str = os.getenv('MESSAGE_PARSE_MODE', 'Markdown')    

    # Список найденных файлов промптов (заполняется автоматически)
    PROMPT_FILES: List[str] = field(default_factory=list)

    # Администраторы (заполняется из переменной окружения)
    ADMIN_TELEGRAM_IDS: List[int] = field(default_factory=list)
    ADMIN_SESSION_TIMEOUT_MINUTES: int = int(os.getenv('ADMIN_SESSION_TIMEOUT_MINUTES', '30'))
    
    # Режим отладки - показывать JSON пользователю
    DEBUG_MODE: bool = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

    def __post_init__(self):
        """Проверка обязательных параметров и инициализация"""
        
        # 🆕 Автоматически получаем BOT_ID из переменной окружения
        self.BOT_ID = os.getenv('BOT_ID', '')
        
        if not self.BOT_ID or not self.BOT_ID.strip():
            error_msg = "BOT_ID не установлен. Запускайте бота через запускалку (например: python growthmed-october-24.py)"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Проверяем формат BOT_ID
        import re
        if not re.match(r'^[a-z0-9\-]+$', self.BOT_ID):
            error_msg = f"BOT_ID должен содержать только латинские буквы, цифры и дефисы: {self.BOT_ID}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Сканируем каталог с промптами
        self._scan_prompt_files()
        
        # Парсим список админов
        self._parse_admin_ids()
        
        # Проверяем обязательные поля
        required_fields = [
            'TELEGRAM_BOT_TOKEN',
            'SUPABASE_URL', 
            'SUPABASE_KEY',
            'OPENAI_API_KEY'
        ]
        
        missing_fields = []
        for field_name in required_fields:
            if not getattr(self, field_name):
                missing_fields.append(field_name)
        
        if missing_fields:
            error_msg = f"Отсутствуют обязательные переменные окружения: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Настройка уровня логирования
        log_level = getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)
        
        # Настраиваем корневой логгер
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Настраиваем форматтер
        if not root_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)
        
        # Устанавливаем уровень для всех модулей
        logging.getLogger('openai_client').setLevel(log_level)
        logging.getLogger('supabase_client').setLevel(log_level)
        logging.getLogger('handlers').setLevel(log_level)
        logging.getLogger('bot_utils').setLevel(log_level)
        logging.getLogger('conversation_manager').setLevel(log_level)
        logging.getLogger('admin_manager').setLevel(log_level)
        logging.getLogger('prompt_loader').setLevel(log_level)
        logging.getLogger('admin_logic').setLevel(log_level)
        logging.getLogger('debug_routing').setLevel(log_level)
        
        # Валидация значений
        if self.OPENAI_MAX_TOKENS < 100 or self.OPENAI_MAX_TOKENS > 4000:
            logger.warning(f"Необычное значение OPENAI_MAX_TOKENS: {self.OPENAI_MAX_TOKENS}")
        
        if self.OPENAI_TEMPERATURE < 0 or self.OPENAI_TEMPERATURE > 1:
            logger.warning(f"Необычное значение OPENAI_TEMPERATURE: {self.OPENAI_TEMPERATURE}")
        
        logger.info(f"✅ Конфигурация загружена успешно")
        logger.info(f"🤖 Bot ID (автоопределен): {self.BOT_ID}")
        logger.debug(f"Модель OpenAI: {self.OPENAI_MODEL}")
        logger.debug(f"Каталог промптов: {self.PROMT_FILES_DIR}")
        logger.debug(f"Найдено файлов: {len(self.PROMPT_FILES)}")
        logger.info(f"👥 Админов настроено: {len(self.ADMIN_TELEGRAM_IDS)}")
        if self.DEBUG_MODE:
            logger.warning("🐛 Режим отладки ВКЛЮЧЕН - JSON будет показываться пользователям")

    def get_summary(self) -> dict:
        """Возвращает сводку конфигурации (без секретов)"""
        return {
            'bot_id': self.BOT_ID,  # 🆕 автоопределенный
            'openai_model': self.OPENAI_MODEL,
            'max_tokens': self.OPENAI_MAX_TOKENS,
            'temperature': self.OPENAI_TEMPERATURE,
            'prompts_dir': self.PROMT_FILES_DIR,
            'max_context': self.MAX_CONTEXT_MESSAGES,
            'log_level': self.LOG_LEVEL,
            'prompt_files_count': len(self.PROMPT_FILES),
            'prompt_files': self.PROMPT_FILES,
            'has_telegram_token': bool(self.TELEGRAM_BOT_TOKEN),
            'has_supabase_config': bool(self.SUPABASE_URL and self.SUPABASE_KEY),
            'has_openai_key': bool(self.OPENAI_API_KEY),
            'admin_count': len(self.ADMIN_TELEGRAM_IDS),
            'debug_mode': self.DEBUG_MODE
        }

    def _parse_admin_ids(self):
        """Парсит список ID админов из переменной окружения"""
        admin_ids_str = os.getenv('ADMIN_TELEGRAM_IDS', '')
        
        if not admin_ids_str.strip():
            logger.warning("⚠️ ADMIN_TELEGRAM_IDS не настроен - админские функции недоступны")
            return
        
        try:
            # Парсим строку вида "123456,789012,345678"
            ids = admin_ids_str.split(',')
            admin_ids = [int(id_str.strip()) for id_str in ids if id_str.strip()]
            
            if not admin_ids:
                logger.warning("⚠️ ADMIN_TELEGRAM_IDS пуст - админские функции недоступны")
            else:
                self.ADMIN_TELEGRAM_IDS.extend(admin_ids)
                logger.info(f"👥 Загружены админы: {self.ADMIN_TELEGRAM_IDS}")
                
        except ValueError as e:
            logger.error(f"❌ Ошибка парсинга ADMIN_TELEGRAM_IDS: {e}")
            logger.error(f"   Формат должен быть: ADMIN_TELEGRAM_IDS=123456,789012")
    
    def _scan_prompt_files(self):
        """Сканирует каталог с промптами и проверяет необходимые файлы"""
        prompts_dir = Path(self.PROMT_FILES_DIR).absolute()
        
        # Проверяем существование каталога
        if not prompts_dir.exists():
            error_msg = f"Каталог с промптами не найден: {prompts_dir.absolute()}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        if not prompts_dir.is_dir():
            error_msg = f"Путь не является каталогом: {prompts_dir.absolute()}"
            logger.error(error_msg)
            raise NotADirectoryError(error_msg)
        
        # Ищем все .txt файлы
        txt_files = list(prompts_dir.glob('*.txt'))
        
        if not txt_files:
            error_msg = f"В каталоге {prompts_dir.absolute()} не найдено ни одного .txt файла"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Проверяем обязательное наличие welcome_message.txt
        welcome_file = prompts_dir / 'welcome_message.txt'
        if not welcome_file.exists():
            error_msg = f"Обязательный файл welcome_message.txt не найден в {prompts_dir}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Формируем список файлов промптов (исключая welcome_message.txt и help_message.txt)
        excluded_files = {'welcome_message.txt', 'help_message.txt'}
        for txt_file in txt_files:
            if txt_file.name not in excluded_files:
                self.PROMPT_FILES.append(txt_file.name)

        if not self.PROMPT_FILES:
            error_msg = f"В каталоге {prompts_dir.absolute()} найден только welcome_message.txt, но нет других файлов промптов"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Сортируем для предсказуемого порядка
        self.PROMPT_FILES.sort()
        
        logger.info(f"📁 Найдено файлов промптов: {len(self.PROMPT_FILES)}")
        logger.info(f"📝 Файлы промптов: {', '.join(self.PROMPT_FILES)}")
        logger.info(f"👋 Файл приветствия: welcome_message.txt")
