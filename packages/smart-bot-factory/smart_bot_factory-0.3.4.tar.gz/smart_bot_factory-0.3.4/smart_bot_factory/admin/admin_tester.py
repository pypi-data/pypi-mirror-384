"""
Утилита для тестирования системы администрирования бота
"""

import asyncio
import logging
import json
import re
import sys
import os

from ..config import Config
from ..integrations.supabase_client import SupabaseClient
from .admin_manager import AdminManager
from ..core.conversation_manager import ConversationManager
from ..analytics.analytics_manager import AnalyticsManager
from .timeout_checker import setup_bot_environment

logger = logging.getLogger(__name__)

async def test_admin_system(bot_name: str = "growthmed-october-24") -> bool:
    """
    Тестирует систему администрирования бота
    
    Args:
        bot_name: Имя бота для тестирования
        
    Returns:
        bool: True если все тесты пройдены, False если найдены проблемы
    """
    logger.info(f"🚀 Тестирование системы администрирования: {bot_name}")
    logger.info(f"🤖 Bot ID будет автоопределен как: {bot_name}\n")
    
    # Настраиваем окружение для бота (автоматически устанавливает BOT_ID)
    config_dir = setup_bot_environment(bot_name)
    if not config_dir:
        return False
    
    # Инициализируем конфигурацию
    config = Config()
    logger.info(f"📋 Конфигурация:")
    logger.info(f"   BOT_ID: {config.BOT_ID}")
    logger.info(f"   ADMIN_SESSION_TIMEOUT_MINUTES: {config.ADMIN_SESSION_TIMEOUT_MINUTES}")
    logger.info(f"   PROMT_FILES_DIR: {config.PROMT_FILES_DIR}")
    logger.info(f"   Найдено промпт-файлов: {len(config.PROMPT_FILES)}")
    logger.info("")
    
    # Проверяем админов
    if not config.ADMIN_TELEGRAM_IDS:
        logger.warning("⚠️ Админы не настроены (ADMIN_TELEGRAM_IDS пуст)")
        return False
    
    logger.info(f"👑 Админы: {config.ADMIN_TELEGRAM_IDS}")
    logger.info("")
    
    # Проверяем подключение к БД
    try:
        supabase_client = SupabaseClient(config.SUPABASE_URL, config.SUPABASE_KEY)
        await supabase_client.initialize()
        logger.info("✅ Подключение к Supabase успешно")
        
        # Проверяем таблицы
        tables = [
            'sales_admins',
            'admin_user_conversations',
            'session_events',
            'sales_chat_sessions',
            'sales_messages'
        ]
        
        logger.info("\n📊 Проверка таблиц:")
        for table in tables:
            try:
                response = supabase_client.client.table(table).select('*').limit(1).execute()
                logger.info(f"   ✅ {table}")
            except Exception as e:
                logger.error(f"   ❌ {table}: {e}")
                return False
        
        # Проверяем AdminManager
        admin_manager = AdminManager(config, supabase_client)
        logger.info(f"\n👑 AdminManager инициализирован ({len(admin_manager.admin_ids)} админов)")
        
        # Проверяем ConversationManager
        conversation_manager = ConversationManager(supabase_client, admin_manager)
        logger.info("✅ ConversationManager инициализирован")
        
        # Проверяем AnalyticsManager
        analytics_manager = AnalyticsManager(supabase_client)
        
        # Тестируем получение статистики
        funnel_stats = await analytics_manager.get_funnel_stats(1)
        logger.info("✅ AnalyticsManager работает")
        
        # Проверяем активные диалоги
        conversations = await conversation_manager.get_active_conversations()
        logger.info(f"\n💬 Активные диалоги: {len(conversations)}")
        
        if conversations:
            for conv in conversations:
                logger.info(f"   • Диалог {conv['id']}: админ {conv['admin_id']} с пользователем {conv['user_id']}")
        else:
            logger.info("   Нет активных диалогов")
            logger.info("   💡 Создайте диалог командой /чат USER_ID для тестирования")
        
        # Проверяем форматирование диалогов
        if conversations:
            formatted = conversation_manager.format_active_conversations(conversations)
            logger.info("\n📝 Форматирование диалогов:")
            logger.info(formatted)
        
        logger.info("\n✅ Админская система готова к работе")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")
        logger.exception("Стек ошибки:")
        return False

def main():
    """Точка входа для запуска из командной строки"""
    # Настройка логирования
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    logger.info("🔍 Утилита тестирования админской системы")
    logger.info("Использование:")
    logger.info("  python -m smart_bot_factory.admin_tester [bot_name]")
    logger.info("  python -m smart_bot_factory.admin_tester growthmed-october-24")
    logger.info("")
    
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        return
    
    # Определяем какого бота тестировать
    bot_name = "growthmed-october-24"  # по умолчанию
    if len(sys.argv) > 1:
        bot_name = sys.argv[1]
    
    try:
        success = asyncio.run(test_admin_system(bot_name))
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
