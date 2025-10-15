"""
Модуль для проверки корректности таймаутов диалогов админов
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
import sys
import os
from typing import Optional

from ..config import Config
from ..integrations.supabase_client import SupabaseClient
from ..core.conversation_manager import ConversationManager
from ..admin.admin_manager import AdminManager

logger = logging.getLogger(__name__)

def setup_bot_environment(bot_name: str = "growthmed-october-24") -> Optional[Path]:
    """Настраивает окружение для указанного бота с автоопределением BOT_ID"""
    root_dir = Path(os.getcwd())  # Используем текущую директорию как корневую
    config_dir = root_dir / 'bots' / bot_name
    
    logger.info(f"🔍 Ищем конфигурацию бота в: {config_dir}")
    
    # Сохраняем оригинальный путь для возврата
    original_cwd = os.getcwd()
    
    if not config_dir.exists():
        logger.error(f"❌ Папка конфигурации не найдена: {config_dir}")
        logger.info(f"   Доступные боты:")
        bots_dir = root_dir / 'bots'
        if bots_dir.exists():
            for bot_dir in bots_dir.iterdir():
                if bot_dir.is_dir():
                    logger.info(f"     - {bot_dir.name}")
        return None
    
    # Проверяем наличие промптов
    prompts_dir = config_dir / 'prompts'
    if not prompts_dir.exists():
        logger.error(f"❌ Папка с промптами не найдена: {prompts_dir}")
        return None
    
    logger.info(f"✅ Найдена папка промптов: {prompts_dir}")
    
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
    
    # Сохраняем текущую директорию и меняем её
    original_cwd = os.getcwd()
    os.chdir(str(config_dir))
    logger.info(f"📁 Изменена рабочая директория: {os.getcwd()}")
    
    # Проверяем что промпты доступны относительно новой директории
    local_prompts = Path('prompts')
    if local_prompts.exists():
        logger.info(f"✅ Промпты доступны из рабочей директории: {local_prompts.absolute()}")
    else:
        logger.error(f"❌ Промпты не найдены в рабочей директории: {local_prompts.absolute()}")
        os.chdir(original_cwd)  # Восстанавливаем директорию
        return None
    
    return config_dir

async def debug_timeout_issue(bot_name: str = "growthmed-october-24") -> bool:
    """
    Диагностирует проблему с таймаутом диалогов
    
    Args:
        bot_name: Имя бота для диагностики
        
    Returns:
        bool: True если диагностика прошла успешно, False если найдены проблемы
    """
    logger.info("🔍 Диагностика проблемы с таймаутом диалогов\n")
    logger.info(f"🚀 Диагностика для бота: {bot_name}")
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
    
    # Проверяем часовые пояса
    logger.info(f"🕐 Временные зоны:")
    now_naive = datetime.now()
    now_utc = datetime.now(timezone.utc)
    logger.info(f"   datetime.now() (локальное): {now_naive}")
    logger.info(f"   datetime.now(timezone.utc): {now_utc}")
    logger.info(f"   Разница: {(now_naive.replace(tzinfo=timezone.utc) - now_utc).total_seconds() / 3600:.1f} часов")
    logger.info("")
    
    # Проверяем активные диалоги в БД
    try:
        supabase_client = SupabaseClient(config.SUPABASE_URL, config.SUPABASE_KEY)
        await supabase_client.initialize()
        
        response = supabase_client.client.table('admin_user_conversations').select(
            'id', 'admin_id', 'user_id', 'started_at', 'auto_end_at'
        ).eq('status', 'active').execute()
        
        conversations = response.data
        
        logger.info(f"📊 Активные диалоги в БД: {len(conversations)}")
        
        problems_found = 0
        
        for i, conv in enumerate(conversations, 1):
            logger.info(f"\n{i}. Диалог ID: {conv['id']}")
            logger.info(f"   Админ: {conv['admin_id']}, Пользователь: {conv['user_id']}")
            
            # Парсим времена
            started_at = conv['started_at']
            auto_end_at = conv['auto_end_at']
            
            logger.info(f"   started_at (сырое): {started_at}")
            logger.info(f"   auto_end_at (сырое): {auto_end_at}")
            
            try:
                # Парсим как делает код
                if started_at.endswith('Z'):
                    start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                elif '+' in started_at or started_at.count(':') >= 3:
                    start_time = datetime.fromisoformat(started_at)
                else:
                    naive_time = datetime.fromisoformat(started_at)
                    start_time = naive_time.replace(tzinfo=timezone.utc)
                
                if auto_end_at.endswith('Z'):
                    end_time = datetime.fromisoformat(auto_end_at.replace('Z', '+00:00'))
                elif '+' in auto_end_at or auto_end_at.count(':') >= 3:
                    end_time = datetime.fromisoformat(auto_end_at)
                else:
                    naive_time = datetime.fromisoformat(auto_end_at)
                    end_time = naive_time.replace(tzinfo=timezone.utc)
                
                logger.info(f"   start_time (парсед): {start_time}")
                logger.info(f"   end_time (парсед): {end_time}")
                
                # Вычисляем длительность диалога
                planned_duration = end_time - start_time
                planned_minutes = int(planned_duration.total_seconds() / 60)
                logger.info(f"   Запланированная длительность: {planned_minutes} минут")
                
                # Проверяем соответствие конфигу
                expected = config.ADMIN_SESSION_TIMEOUT_MINUTES
                if planned_minutes == expected:
                    logger.info(f"   ✅ Соответствует конфигу ({expected} мин)")
                else:
                    logger.error(f"   ❌ НЕ соответствует конфигу! Ожидалось {expected} мин, получили {planned_minutes} мин")
                    problems_found += 1
                
                # Вычисляем текущее время до автозавершения
                now_utc = datetime.now(timezone.utc)
                
                # Приводим к UTC
                if end_time.tzinfo != timezone.utc:
                    end_time_utc = end_time.astimezone(timezone.utc)
                else:
                    end_time_utc = end_time
                
                remaining = end_time_utc - now_utc
                remaining_minutes = max(0, int(remaining.total_seconds() / 60))
                
                logger.info(f"   now_utc: {now_utc}")
                logger.info(f"   end_time_utc: {end_time_utc}")
                logger.info(f"   Оставшееся время: {remaining_minutes} минут")
                
                # Вычисляем сколько уже прошло
                if start_time.tzinfo != timezone.utc:
                    start_time_utc = start_time.astimezone(timezone.utc)
                else:
                    start_time_utc = start_time
                    
                elapsed = now_utc - start_time_utc
                elapsed_minutes = max(0, int(elapsed.total_seconds() / 60))
                logger.info(f"   Прошло времени: {elapsed_minutes} минут")
                
                # Проверяем математику
                total_check = elapsed_minutes + remaining_minutes
                logger.info(f"   Проверка: {elapsed_minutes} + {remaining_minutes} = {total_check} мин (должно быть ~{planned_minutes})")
                
                if abs(total_check - planned_minutes) > 2:
                    logger.warning(f"   ⚠️ ПРОБЛЕМА: сумма не сходится! Возможная проблема с timezone")
                    problems_found += 1
                
            except Exception as e:
                logger.error(f"   ❌ Ошибка парсинга времени: {e}")
                problems_found += 1
        
        if not conversations:
            logger.info("   Нет активных диалогов для анализа")
            logger.info("   💡 Создайте диалог командой /чат USER_ID для тестирования")
            
        return problems_found == 0
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return False

async def test_conversation_creation(config: Config) -> bool:
    """
    Тестирует создание нового диалога с правильным таймаутом
    
    Args:
        config: Конфигурация бота
        
    Returns:
        bool: True если тест прошел успешно, False если найдены проблемы
    """
    logger.info(f"\n{'='*50}")
    logger.info("🧪 ТЕСТ СОЗДАНИЯ ДИАЛОГА")
    logger.info(f"{'='*50}")
    
    timeout_minutes = config.ADMIN_SESSION_TIMEOUT_MINUTES
    logger.info(f"📋 Конфигурация таймаута: {timeout_minutes} минут")
    
    # Эмулируем создание диалога
    now_utc = datetime.now(timezone.utc)
    auto_end_utc = now_utc + timedelta(minutes=timeout_minutes)
    
    logger.info(f"🕐 now_utc: {now_utc}")
    logger.info(f"⏰ auto_end_utc: {auto_end_utc}")
    logger.info(f"📏 Разница: {int((auto_end_utc - now_utc).total_seconds() / 60)} минут")
    
    # Проверяем ISO формат
    auto_end_iso = auto_end_utc.isoformat()
    logger.info(f"📝 ISO формат: {auto_end_iso}")
    
    # Проверяем парсинг обратно
    try:
        if auto_end_iso.endswith('Z'):
            parsed_back = datetime.fromisoformat(auto_end_iso.replace('Z', '+00:00'))
        elif '+' in auto_end_iso:
            parsed_back = datetime.fromisoformat(auto_end_iso)
        else:
            parsed_back = datetime.fromisoformat(auto_end_iso).replace(tzinfo=timezone.utc)
        
        logger.info(f"🔄 Парсед обратно: {parsed_back}")
        
        # Проверяем что время совпадает
        if abs((parsed_back - auto_end_utc).total_seconds()) < 1:
            logger.info("✅ Парсинг работает корректно")
            return True
        else:
            logger.error("❌ Проблема с парсингом времени")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка парсинга: {e}")
        return False

async def check_timeouts(bot_name: str = "growthmed-october-24") -> bool:
    """
    Проверяет корректность таймаутов диалогов админов
    
    Args:
        bot_name: Имя бота для проверки
        
    Returns:
        bool: True если все таймауты корректны, False если найдены проблемы
    """
    logger.info("🔍 Проверка таймаутов диалогов админов\n")
    logger.info(f"🚀 Проверка для бота: {bot_name}")
    logger.info(f"🤖 Bot ID будет автоопределен как: {bot_name}\n")
    
    # Настраиваем окружение для бота (автоматически устанавливает BOT_ID)
    config_dir = setup_bot_environment(bot_name)
    if not config_dir:
        logger.error("❌ Не удалось настроить окружение бота")
        return False
    
    logger.info(f"📁 Текущая рабочая директория: {os.getcwd()}")
    logger.info(f"📂 Содержимое рабочей директории:")
    for item in Path('.').iterdir():
        if item.is_dir():
            logger.info(f"   📁 {item.name}/")
        else:
            logger.info(f"   📄 {item.name}")
    logger.info("")
    
    # Инициализация
    try:
        logger.info("⚙️ Инициализация конфигурации...")
        config = Config()
        logger.info(f"✅ Конфигурация загружена")
        
        logger.info("🔗 Подключение к Supabase...")
        supabase_client = SupabaseClient(config.SUPABASE_URL, config.SUPABASE_KEY)
        await supabase_client.initialize()
        logger.info(f"✅ Supabase подключен")
        
        logger.info("👑 Инициализация менеджеров...")
        admin_manager = AdminManager(config, supabase_client)
        conversation_manager = ConversationManager(supabase_client, admin_manager)
        logger.info(f"✅ Менеджеры инициализированы\n")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}")
        logger.exception("Стек ошибки:")
        return False
    
    logger.info(f"⚙️ Конфигурация:")
    logger.info(f"   BOT_ID: {config.BOT_ID}")
    logger.info(f"   ADMIN_SESSION_TIMEOUT_MINUTES: {config.ADMIN_SESSION_TIMEOUT_MINUTES}")
    logger.info(f"   PROMT_FILES_DIR: {config.PROMT_FILES_DIR}")
    logger.info(f"   Найдено промпт-файлов: {len(config.PROMPT_FILES)}")
    logger.info(f"   Админов: {len(config.ADMIN_TELEGRAM_IDS)}")
    logger.info(f"   Сейчас UTC: {datetime.now(timezone.utc)}")
    logger.info("")
    
    # Получаем активные диалоги
    try:
        logger.info("📊 Получение активных диалогов...")
        conversations = await conversation_manager.get_active_conversations()
        logger.info(f"✅ Получено {len(conversations)} диалогов")
    except Exception as e:
        logger.error(f"❌ Ошибка получения диалогов: {e}")
        return False
    
    if not conversations:
        logger.info("💬 Нет активных диалогов")
        logger.info("💡 Создайте диалог командой /чат USER_ID для тестирования")
        
        # Показываем пример создания тестового диалога
        logger.info(f"\n🧪 Пример создания тестового диалога:")
        logger.info(f"1. Запустите бота: python {bot_name}.py")
        logger.info(f"2. Как админ выполните: /чат 123456789")
        logger.info(f"3. Затем проверьте: /чаты")
        return True  # Нет диалогов = нет проблем
    
    logger.info(f"📊 Найдено {len(conversations)} активных диалогов:")
    logger.info("")
    
    problems_found = 0
    
    for i, conv in enumerate(conversations, 1):
        logger.info(f"{i}. Диалог ID: {conv['id']}")
        logger.info(f"   👤 Пользователь: {conv['user_id']}")
        logger.info(f"   👑 Админ: {conv['admin_id']}")
        
        # Анализируем времена
        started_at_str = conv['started_at']
        auto_end_str = conv['auto_end_at']
        
        logger.info(f"   🕐 started_at (сырое): {started_at_str}")
        logger.info(f"   ⏰ auto_end_at (сырое): {auto_end_str}")
        
        try:
            # Парсим время начала с правильной обработкой timezone
            if started_at_str.endswith('Z'):
                start_time = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
            elif '+' in started_at_str or started_at_str.count(':') >= 3:
                start_time = datetime.fromisoformat(started_at_str)
            else:
                naive_time = datetime.fromisoformat(started_at_str)
                start_time = naive_time.replace(tzinfo=timezone.utc)
            
            # Парсим время автозавершения с правильной обработкой timezone
            if auto_end_str.endswith('Z'):
                auto_end = datetime.fromisoformat(auto_end_str.replace('Z', '+00:00'))
            elif '+' in auto_end_str or auto_end_str.count(':') >= 3:
                auto_end = datetime.fromisoformat(auto_end_str)
            else:
                naive_time = datetime.fromisoformat(auto_end_str)
                auto_end = naive_time.replace(tzinfo=timezone.utc)
            
            logger.info(f"   📅 start_time (parsed): {start_time}")
            logger.info(f"   ⏰ auto_end (parsed): {auto_end}")
            
            # Планируемая длительность
            planned_duration = auto_end - start_time
            planned_minutes = int(planned_duration.total_seconds() / 60)
            logger.info(f"   📏 Планируемая длительность: {planned_minutes} минут")
            
            # Текущее время в UTC
            now_utc = datetime.now(timezone.utc)
            
            # Приводим все к UTC для корректных расчетов
            if start_time.tzinfo != timezone.utc:
                start_time_utc = start_time.astimezone(timezone.utc)
            else:
                start_time_utc = start_time
                
            if auto_end.tzinfo != timezone.utc:
                auto_end_utc = auto_end.astimezone(timezone.utc)
            else:
                auto_end_utc = auto_end
            
            # Прошло времени
            elapsed = now_utc - start_time_utc
            elapsed_minutes = max(0, int(elapsed.total_seconds() / 60))
            logger.info(f"   ⏱️ Прошло времени: {elapsed_minutes} минут")
            
            # Оставшееся время
            remaining = auto_end_utc - now_utc
            remaining_minutes = max(0, int(remaining.total_seconds() / 60))
            logger.info(f"   ⏰ Осталось времени: {remaining_minutes} минут")
            
            # Проверяем корректность конфигурации
            expected_timeout = config.ADMIN_SESSION_TIMEOUT_MINUTES
            if abs(planned_minutes - expected_timeout) <= 2:  # допускаем погрешность 2 минуты
                logger.info(f"   ✅ Таймаут корректный (ожидался {expected_timeout} мин)")
            else:
                logger.error(f"   ❌ ОШИБКА: ожидался {expected_timeout} мин, получили {planned_minutes} мин")
                problems_found += 1
            
            # Проверяем математику
            total_check = elapsed_minutes + remaining_minutes
            logger.info(f"   🔢 Проверка: {elapsed_minutes} + {remaining_minutes} = {total_check} мин")
            
            if abs(total_check - planned_minutes) > 2:
                logger.warning(f"   ⚠️ ПРОБЛЕМА: сумма не сходится! Возможна проблема с timezone")
                problems_found += 1
            else:
                logger.info(f"   ✅ Математика сходится")
                
        except Exception as e:
            logger.error(f"   ❌ Ошибка парсинга: {e}")
            problems_found += 1
            logger.exception("   Стек ошибки:")
        
        logger.info("")
    
    # Тестируем функцию форматирования
    logger.info("🧪 Тестирование format_active_conversations:")
    try:
        formatted_text = conversation_manager.format_active_conversations(conversations)
        logger.info(formatted_text)
    except Exception as e:
        logger.error(f"❌ Ошибка форматирования: {e}")
        problems_found += 1
    
    # Итоговый результат
    logger.info(f"\n{'='*50}")
    logger.info(f"📊 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    if problems_found == 0:
        logger.info("✅ Все таймауты корректны!")
    else:
        logger.error(f"❌ Найдено {problems_found} проблем")
        logger.info("💡 Запустите fix_existing_timeouts.py для исправления")
    logger.info(f"{'='*50}")
    
    return problems_found == 0

def main():
    """Точка входа для запуска из командной строки"""
    # Убираем лишние логи для чистого вывода
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    logger.info("🔍 Утилита проверки таймаутов диалогов")
    logger.info("Использование:")
    logger.info("  python -m smart_bot_factory.timeout_checker [bot_name]")
    logger.info("  python -m smart_bot_factory.timeout_checker growthmed-october-24")
    logger.info("")
    
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        return
    
    # Определяем какого бота проверять
    bot_name = "growthmed-october-24"  # по умолчанию
    if len(sys.argv) > 1:
        bot_name = sys.argv[1]
    
    try:
        success = asyncio.run(check_timeouts(bot_name))
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
