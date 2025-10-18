"""
Модуль для проверки настройки Telegram Sales Bot v2.0 (с админской системой)
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from .config import Config
from .integrations.supabase_client import SupabaseClient
from .integrations.openai_client import OpenAIClient
from .utils.prompt_loader import PromptLoader
from .admin.admin_manager import AdminManager
from .core.conversation_manager import ConversationManager
from .analytics.analytics_manager import AnalyticsManager
from .core.bot_utils import parse_ai_response

logger = logging.getLogger(__name__)

def setup_bot_environment(bot_name: str = "growthmed-october-24") -> Optional[Path]:
    """
    Настраивает окружение для указанного бота с автоопределением BOT_ID
    
    Args:
        bot_name: Имя бота для настройки
        
    Returns:
        Optional[Path]: Путь к корневой директории проекта, если настройка успешна, None в случае ошибки
    """
    root_dir = Path(os.getcwd())  # Используем текущую директорию как корневую
    config_dir = root_dir / 'bots' / bot_name
    
    if not config_dir.exists():
        logger.error(f"❌ Папка конфигурации не найдена: {config_dir}")
        logger.info(f"   Доступные боты:")
        bots_dir = root_dir / 'bots'
        if bots_dir.exists():
            for bot_dir in bots_dir.iterdir():
                if bot_dir.is_dir():
                    logger.info(f"     - {bot_dir.name}")
        return None
    
    # Устанавливаем BOT_ID из имени бота
    os.environ['BOT_ID'] = bot_name
    logger.info(f"🤖 Автоматически установлен BOT_ID: {bot_name}")
    
    # Загружаем .env из конфигурации бота
    env_file = config_dir / '.env'
    if env_file.exists():
        logger.info(f"🔧 Загружаем .env из: {env_file}")
        from dotenv import load_dotenv
        load_dotenv(env_file)
    else:
        logger.error(f"❌ Файл .env не найден: {env_file}")
        return None
    
    # Меняем рабочую директорию
    os.chdir(str(config_dir))
    logger.info(f"📁 Рабочая директория: {config_dir}")
    
    return root_dir

async def check_config() -> Optional[Config]:
    """Проверяем конфигурацию с новыми админскими настройками"""
    try:
        config = Config()
        
        logger.info("✅ Конфигурация загружена успешно")
        logger.info(f"📋 Сводка конфигурации:")
        
        summary = config.get_summary()
        for key, value in summary.items():
            logger.info(f"   • {key}: {value}")
        
        # Проверяем админские настройки
        logger.info(f"\n👑 Админские настройки:")
        logger.info(f"   • Админов настроено: {len(config.ADMIN_TELEGRAM_IDS)}")
        if config.ADMIN_TELEGRAM_IDS:
            logger.info(f"   • ID админов: {config.ADMIN_TELEGRAM_IDS}")
        logger.info(f"   • Таймаут сессий: {config.ADMIN_SESSION_TIMEOUT_MINUTES} мин")
        logger.info(f"   • Режим отладки: {'Включен' if config.DEBUG_MODE else 'Выключен'}")
        
        return config
    except Exception as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        return None

async def check_supabase(config: Config) -> bool:
    """Проверяем подключение к Supabase и новые таблицы"""
    try:
        client = SupabaseClient(config.SUPABASE_URL, config.SUPABASE_KEY)
        await client.initialize()
        
        # Пробуем выполнить простой запрос к основной таблице
        response = client.client.table('sales_users').select('id').limit(1).execute()
        logger.info("✅ Supabase подключение успешно")
        
        # Проверяем новые таблицы админской системы
        admin_tables = [
            'sales_admins',
            'admin_user_conversations', 
            'session_events'
        ]
        
        logger.info("🔍 Проверка админских таблиц:")
        for table in admin_tables:
            try:
                response = client.client.table(table).select('*').limit(1).execute()
                logger.info(f"   ✅ {table}")
            except Exception as e:
                logger.error(f"   ❌ {table}: {e}")
        
        # Проверяем новые колонки
        logger.info("🔍 Проверка новых колонок:")
        try:
            response = client.client.table('sales_chat_sessions').select(
                'current_stage', 'lead_quality_score'
            ).limit(1).execute()
            logger.info("   ✅ sales_chat_sessions: current_stage, lead_quality_score")
        except Exception as e:
            logger.error(f"   ❌ sales_chat_sessions новые колонки: {e}")
        
        try:
            response = client.client.table('sales_messages').select('ai_metadata').limit(1).execute()
            logger.info("   ✅ sales_messages: ai_metadata")
        except Exception as e:
            logger.error(f"   ❌ sales_messages.ai_metadata: {e}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка Supabase: {e}")
        return False

async def check_openai(config: Config) -> bool:
    """Проверяем OpenAI API"""
    try:
        client = OpenAIClient(
            config.OPENAI_API_KEY,
            config.OPENAI_MODEL,
            config.OPENAI_MAX_TOKENS,
            config.OPENAI_TEMPERATURE
        )
        
        health = await client.check_api_health()
        
        if health:
            logger.info("✅ OpenAI API доступен")
            
            # Получаем список доступных моделей
            models = await client.get_available_models()
            if config.OPENAI_MODEL in models:
                logger.info(f"✅ Модель {config.OPENAI_MODEL} доступна")
            else:
                logger.warning(f"⚠️ Модель {config.OPENAI_MODEL} не найдена в доступных")
                logger.info(f"   Доступные модели: {models[:5]}...")
        
        return health
    except Exception as e:
        logger.error(f"❌ Ошибка OpenAI: {e}")
        return False

async def check_prompts(config: Config) -> bool:
    """Проверяем промпты с новыми JSON инструкциями"""
    try:
        loader = PromptLoader(
            prompts_dir=config.PROMT_FILES_DIR,
            prompt_files=config.PROMPT_FILES
        )
        
        # Проверяем доступность файлов
        validation = await loader.validate_prompts()
        
        logger.info(f"📝 Статус промптов:")
        for filename, status in validation.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"   {status_icon} {filename}")
        
        # Пробуем загрузить системный промпт
        if any(validation.values()):
            system_prompt = await loader.load_system_prompt()
            logger.info(f"✅ Системный промпт загружен ({len(system_prompt)} символов)")
            
            # Проверяем наличие JSON инструкций
            if "JSON МЕТАДАННЫМ" in system_prompt:
                logger.info("✅ JSON инструкции включены в системный промпт")
            else:
                logger.warning("⚠️ JSON инструкции не найдены в системном промпте")
            
            if '"этап":' in system_prompt:
                logger.info("✅ Примеры JSON найдены в промпте")
            else:
                logger.warning("⚠️ Примеры JSON не найдены в промпте")
            
            # Проверяем приветственное сообщение
            welcome_message = await loader.load_welcome_message()
            logger.info(f"✅ Приветственное сообщение загружено ({len(welcome_message)} символов)")
            
            # Проверяем справочное сообщение
            help_message = await loader.load_help_message()
            logger.info(f"✅ Справочное сообщение загружено ({len(help_message)} символов)")
            
            return True
        else:
            logger.error("❌ Не удалось загрузить ни одного промпта")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки промптов: {e}")
        return False

async def check_admin_system(config: Config) -> bool:
    """Проверяем админскую систему"""
    try:
        logger.info("👑 Проверка админской системы...")
        
        if not config.ADMIN_TELEGRAM_IDS:
            logger.warning("⚠️ Админы не настроены (ADMIN_TELEGRAM_IDS пуст)")
            return False
        
        # Проверяем AdminManager
        supabase_client = SupabaseClient(config.SUPABASE_URL, config.SUPABASE_KEY)
        await supabase_client.initialize()
        
        admin_manager = AdminManager(config, supabase_client)
        logger.info(f"✅ AdminManager инициализирован ({len(admin_manager.admin_ids)} админов)")
        
        # Проверяем ConversationManager
        conversation_manager = ConversationManager(supabase_client, admin_manager)
        logger.info("✅ ConversationManager инициализирован")
        
        # Проверяем AnalyticsManager
        analytics_manager = AnalyticsManager(supabase_client)
        
        # Тестируем получение статистики
        funnel_stats = await analytics_manager.get_funnel_stats(1)
        logger.info("✅ AnalyticsManager работает")
        
        logger.info("✅ Админская система готова к работе")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка админской системы: {e}")
        return False

async def check_json_parsing() -> bool:
    """Проверяем парсинг JSON метаданных"""
    try:
        logger.info("🧪 Проверка парсинга JSON...")
        
        # Тестовые случаи
        test_response = '''Отлично! Записал ваш номер телефона.

{
  "этап": "contacts",
  "качество": 9,
  "события": [
    {
      "тип": "телефон",
      "инфо": "Иван Петров +79219603144"
    }
  ]
}'''
        
        response_text, metadata = parse_ai_response(test_response)
        
        if metadata:
            logger.info("✅ JSON успешно распарсен")
            logger.info(f"   Этап: {metadata.get('этап')}")
            logger.info(f"   Качество: {metadata.get('качество')}")
            logger.info(f"   События: {len(metadata.get('события', []))}")
            return True
        else:
            logger.error("❌ Не удалось распарсить JSON")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка парсинга JSON: {e}")
        return False

async def check_database_structure() -> bool:
    """Проверяем структуру базы данных"""
    try:
        logger.info("📊 Проверка структуры БД...")
        
        # Проверяем наличие SQL файлов
        root_dir = Path(os.getcwd())
        sql_files = [
            ("database_structure.sql", "smart_bot_factory/database/database_structure.sql"),
            ("admin_migration.sql", "smart_bot_factory/admin/admin_migration.sql")
        ]
        
        for sql_name, sql_path in sql_files:
            full_path = root_dir / sql_path
            if full_path.exists():
                logger.info(f"✅ {sql_name} найден: {sql_path}")
            else:
                logger.error(f"❌ {sql_name} не найден: {sql_path}")
        
        logger.info("ℹ️ Для проверки таблиц в БД запустите SQL скрипты в Supabase")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки БД: {e}")
        return False

async def check_environment() -> None:
    """Проверяем окружение"""
    logger.info("🔧 Проверка окружения...")
    
    # Проверяем Python зависимости
    dependencies = [
        ('aiogram', 'aiogram'),
        ('supabase', 'supabase'), 
        ('openai', 'openai'),
        ('python-dotenv', 'dotenv'),
        ('aiofiles', 'aiofiles')
    ]
    
    for dep_name, import_name in dependencies:
        try:
            if import_name == 'aiogram':
                import aiogram
                logger.info(f"✅ {dep_name} {aiogram.__version__}")
            elif import_name == 'openai':
                import openai
                logger.info(f"✅ {dep_name} {openai.version.VERSION}")
            else:
                __import__(import_name)
                logger.info(f"✅ {dep_name} установлен")
        except ImportError:
            logger.error(f"❌ {dep_name} не установлен")

async def run_quick_test() -> bool:
    """Быстрый тест основного функционала"""
    try:
        logger.info("⚡ Быстрый тест компонентов...")
        
        config = Config()
        
        if config.ADMIN_TELEGRAM_IDS:
            logger.info(f"✅ {len(config.ADMIN_TELEGRAM_IDS)} админов настроено")
        else:
            logger.warning("⚠️ Админы не настроены")
        
        # Тест парсинга JSON
        await check_json_parsing()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка быстрого теста: {e}")
        return False

async def check_setup(bot_name: str = "growthmed-october-24") -> bool:
    """
    Проверяет настройку бота
    
    Args:
        bot_name: Имя бота для проверки
        
    Returns:
        bool: True если все критические проверки пройдены, False если есть критические ошибки
    """
    logger.info(f"🚀 Проверка настройки Telegram Sales Bot v2.0: {bot_name}")
    logger.info(f"🤖 Bot ID будет автоопределен как: {bot_name}\n")
    
    # Настраиваем окружение для бота (автоматически устанавливает BOT_ID)
    config_dir = setup_bot_environment(bot_name)
    if not config_dir:
        return False
        
    # Проверяем окружение
    await check_environment()
    logger.info("")
    
    # Проверяем конфигурацию
    config = await check_config()
    if not config:
        logger.error("\n❌ Невозможно продолжить без правильной конфигурации")
        return False
    logger.info("")
    
    # Основные проверки
    checks: List[Tuple[str, bool]] = []
    for name, check_coro in [
        ("База данных", check_database_structure()),
        ("Supabase", check_supabase(config)),
        ("OpenAI", check_openai(config)),
        ("Промпты", check_prompts(config)),
        ("Админская система", check_admin_system(config)),
        ("JSON парсинг", check_json_parsing()),
        ("Быстрый тест", run_quick_test())
    ]:
        logger.info(f"\n🔍 Проверка: {name}")
        result = await check_coro
        checks.append((name, result))
    
    # Итоговый результат
    logger.info(f"\n{'='*60}")
    logger.info(f"📋 ИТОГОВЫЙ ОТЧЕТ для {bot_name}:")
    
    all_passed = True
    critical_failed = False
    
    # Критические компоненты
    critical_checks = ["Supabase", "OpenAI", "Промпты"]
    
    for name, passed in checks:
        if name in critical_checks:
            status = "✅ ПРОЙДЕНА" if passed else "❌ КРИТИЧЕСКАЯ ОШИБКА"
            if not passed:
                critical_failed = True
        else:
            status = "✅ ПРОЙДЕНА" if passed else "⚠️ ПРЕДУПРЕЖДЕНИЕ"
        
        logger.info(f"   {name}: {status}")
        if not passed:
            all_passed = False
    
    passed_count = sum(1 for _, passed in checks if passed)
    logger.info(f"\n📊 Результат: {passed_count}/{len(checks)} проверок пройдено")
    
    if critical_failed:
        logger.error("\n🚨 КРИТИЧЕСКИЕ ОШИБКИ! Бот не может быть запущен.")
        logger.error("   Исправьте критические ошибки перед запуском.")
    elif all_passed:
        logger.info("\n🎉 Все проверки пройдены! Бот готов к запуску.")
        logger.info(f"   Запустите: python {bot_name}.py")
        if config.ADMIN_TELEGRAM_IDS:
            logger.info(f"   👑 Админский доступ настроен для: {config.ADMIN_TELEGRAM_IDS}")
    else:
        logger.warning("\n⚠️ Есть предупреждения, но бот может работать.")
        logger.warning("   Рекомендуется исправить предупреждения для полного функционала.")
    
    if config and config.DEBUG_MODE:
        logger.warning("\n🐛 РЕЖИМ ОТЛАДКИ ВКЛЮЧЕН - JSON будет показываться пользователям")
    
    logger.info(f"{'='*60}")
    
    return not critical_failed

def main():
    """Точка входа для запуска из командной строки"""
    # Настройка логирования
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    logger.info("🔍 Утилита проверки настройки бота")
    logger.info("Использование:")
    logger.info("  python -m smart_bot_factory.setup_checker [bot_name]")
    logger.info("  python -m smart_bot_factory.setup_checker growthmed-october-24")
    logger.info("")
    
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        return
    
    # Определяем какого бота проверять
    bot_name = "growthmed-october-24"  # по умолчанию
    if len(sys.argv) > 1:
        bot_name = sys.argv[1]
    
    try:
        success = asyncio.run(check_setup(bot_name))
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Прервано пользователем")
    except Exception as e:
        logger.error(f"\n💥 Критическая ошибка: {e}")
        logger.exception("Стек ошибки:")
        sys.exit(1)

if __name__ == "__main__":
    main()
