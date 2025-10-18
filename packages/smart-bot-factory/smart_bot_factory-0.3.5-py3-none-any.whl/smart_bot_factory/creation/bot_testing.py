#!/usr/bin/env python3
"""
Система тестирования ботов

ИСПОЛЬЗОВАНИЕ:
    python bot_testing.py valera                    # Тестировать бота valera (все сценарии)
    python bot_testing.py valera final_scenarios    # Тестировать только файл final_scenarios.yaml
    python bot_testing.py valera -v                 # Подробный вывод
    python bot_testing.py valera --max-concurrent 10  # Увеличить количество потоков до 10 (По умолчанию 5)
    
ФАЙЛЫ СЦЕНАРИЕВ:
    bots/BOT_ID/tests/*.yaml - тестовые сценарии
    
ОТЧЕТЫ:
    bots/BOT_ID/reports/test_YYYYMMDD_HHMMSS.txt - подробные отчеты

ФОРМАТ СЦЕНАРИЕВ:
    expected_keywords поддерживает синонимы:
    - Одно слово: ["привет"] - проверяется только это слово
    - Синонимы: [["привет", "здравствуйте", "добро пожаловать"]] - достаточно найти любое из слов
    - Смешанный формат: ["привет", ["здравствуйте", "добро пожаловать"]] - комбинация одиночных слов и синонимов
"""

import asyncio
import yaml
import os
import sys
import argparse
import logging
import glob
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List
from dotenv import load_dotenv


from project_root_finder import root
from pathlib import Path
# Глобальная переменная для корневой директории проекта
PROJECT_ROOT = root  # smart_bot_factory/creation/ -> project_root

def set_project_root(new_root: Path):
    """Устанавливает новую корневую директорию проекта"""
    global PROJECT_ROOT
    PROJECT_ROOT = Path(new_root).resolve()
    logging.info(f"Корневая директория проекта изменена на: {PROJECT_ROOT}")

def get_project_root() -> Path:
    """Возвращает текущую корневую директорию проекта"""
    # Проверяем переменную окружения PROJECT_ROOT
    env_project_root = os.getenv('PROJECT_ROOT')
    if env_project_root:
        return Path(env_project_root).resolve()
    return PROJECT_ROOT

# Импорты для работы с ботом
try:
    # Попробуем относительные импорты (если запускается как модуль)
    from ..integrations.openai_client import OpenAIClient
    from ..utils.prompt_loader import PromptLoader
    from ..integrations.supabase_client import SupabaseClient
    from ..core.bot_utils import parse_ai_response
except ImportError:
    # Если не работает, используем абсолютные импорты (если запускается как скрипт)
    from smart_bot_factory.integrations.openai_client import OpenAIClient
    from smart_bot_factory.utils.prompt_loader import PromptLoader
    from smart_bot_factory.integrations.supabase_client import SupabaseClient
    from smart_bot_factory.core.bot_utils import parse_ai_response


logger = logging.getLogger(__name__)


class TestStep:
    """Класс для представления одного шага в сценарии"""
    
    def __init__(self, user_input: str, expected_keywords: List[str], 
                 forbidden_keywords: List[str] = None):
        self.user_input = user_input
        # Поддержка синонимов: если элемент списка - список, то это синонимы
        self.expected_keywords = self._process_keywords(expected_keywords)
        self.forbidden_keywords = [kw.lower() for kw in (forbidden_keywords or [])]
    
    def _process_keywords(self, keywords: List) -> List:
        """Обрабатывает ключевые слова, поддерживая синонимы"""
        processed = []
        for kw in keywords:
            if isinstance(kw, list):
                # Это группа синонимов
                synonyms = [s.lower() for s in kw if isinstance(s, str)]
                processed.append(synonyms)
            elif isinstance(kw, str):
                # Одно слово
                processed.append([kw.lower()])
            else:
                # Игнорируем неверные типы
                continue
        return processed


class TestScenario:
    """Класс для представления тестового сценария с последовательными шагами"""
    
    def __init__(self, name: str, steps: List[TestStep]):
        self.name = name
        self.steps = steps


class StepResult:
    """Класс для представления результата одного шага"""
    
    def __init__(self, step: TestStep, bot_response: str, 
                 passed: bool, missing_keywords: List[str] = None,
                 found_forbidden: List[str] = None):
        self.step = step
        self.bot_response = bot_response
        self.passed = passed
        self.missing_keywords = missing_keywords or []
        self.found_forbidden = found_forbidden or []


class TestResult:
    """Класс для представления результата тестирования сценария"""
    
    def __init__(self, scenario: TestScenario, step_results: List[StepResult]):
        self.scenario = scenario
        self.step_results = step_results
        self.passed = all(step.passed for step in step_results)
        self.total_steps = len(step_results)
        self.passed_steps = sum(1 for step in step_results if step.passed)
        self.failed_steps = self.total_steps - self.passed_steps


class ScenarioLoader:
    """Загрузчик тестовых сценариев из YAML файлов"""
    
    @staticmethod
    def load_scenarios_from_file(file_path: str) -> List[TestScenario]:
        """Загружает сценарии из YAML файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                
            scenarios = []
            file_name = Path(file_path).stem
            
            for i, scenario_data in enumerate(data.get('scenarios', [])):
                # Проверяем новый формат со steps
                if 'steps' in scenario_data:
                    # Новый формат: сценарий с шагами
                    name = scenario_data.get('name', f"[{file_name}-{i+1}]")
                    steps = []
                    
                    for step_data in scenario_data['steps']:
                        step = TestStep(
                            user_input=step_data.get('user_input', ''),
                            expected_keywords=step_data.get('expected_keywords', []),
                            forbidden_keywords=step_data.get('forbidden_keywords', [])
                        )
                        steps.append(step)
                    
                    scenario = TestScenario(name=name, steps=steps)
                    
                else:
                    # Старый формат: одиночный вопрос -> превращаем в сценарий с одним шагом
                    name = scenario_data.get('name', f"[{file_name}-{i+1}]")
                    step = TestStep(
                        user_input=scenario_data.get('user_input', ''),
                        expected_keywords=scenario_data.get('expected_keywords', []),
                        forbidden_keywords=scenario_data.get('forbidden_keywords', [])
                    )
                    scenario = TestScenario(name=name, steps=[step])
                
                # Добавляем информацию о файле для отчетности
                scenario.source_file = file_name
                scenario.scenario_number = i + 1
                
                scenarios.append(scenario)
                
            return scenarios
            
        except Exception as e:
            logging.error(f"Ошибка загрузки сценариев из {file_path}: {e}")
            return []
    
    @staticmethod
    def load_all_scenarios_for_bot(bot_id: str, project_root: Path = None) -> List[TestScenario]:
        """Загружает все сценарии для указанного бота"""
        # Используем переданную корневую директорию или глобальную
        user_root_dir = project_root or get_project_root()
        
        # Проверяем наличие папки bots/{bot_id}
        bots_dir = user_root_dir / "bots" / bot_id
        if not bots_dir.exists():
            logging.warning(f"Папка bots/{bot_id} не найдена в проекте: {bots_dir}")
            return []
        
        # Путь к папке tests в корневой директории пользователя
        tests_dir = user_root_dir / "bots" / bot_id / "tests"
        
        if not tests_dir.exists():
            logging.warning(f"Каталог тестов не найден: {tests_dir}")
            return []
        
        all_scenarios = []
        for yaml_file in tests_dir.glob("*.yaml"):
            scenarios = ScenarioLoader.load_scenarios_from_file(str(yaml_file))
            all_scenarios.extend(scenarios)
            
        return all_scenarios


class BotTester:
    """Основной класс для тестирования ботов"""
    
    def __init__(self, bot_id: str, project_root: Path = None):
        self.bot_id = bot_id
        self.project_root = project_root or get_project_root()
        self.openai_client = None
        self.prompt_loader = None
        self.supabase_client = None
        self.config_dir = None
        self._initialize_bot()
    
    def _initialize_bot(self):
        """Инициализация компонентов бота, используя готовую логику из запускалки"""
        try:
            logging.info(f"")
            logging.info(f"══════════════════════════════════════════════════════════")
            logging.info(f"ИНИЦИАЛИЗАЦИЯ ТЕСТЕРА БОТА: {self.bot_id}")
            logging.info(f"══════════════════════════════════════════════════════════")
            
            # Используем корневую директорию проекта
            user_root_dir = self.project_root
            logging.info(f"Корневая директория проекта: {user_root_dir}")
            
            # Добавляем корневую директорию в sys.path для импорта библиотеки
            sys.path.insert(0, str(user_root_dir))
            logging.info(f"Добавлен путь в sys.path: {user_root_dir}")
            
            # Путь к конфигурации бота в корневой директории проекта
            self.config_dir = user_root_dir / 'bots' / self.bot_id
            logging.info(f"Каталог конфигурации: {self.config_dir}")
            
            if not self.config_dir.exists():
                raise ValueError(f"Папка конфигурации не найдена: {self.config_dir}")
            logging.info(f"Каталог конфигурации найден")
            
            # Устанавливаем BOT_ID как в оригинальном файле
            os.environ['BOT_ID'] = self.bot_id
            logging.info(f"BOT_ID установлен: {self.bot_id}")
            
            # Загружаем .env из папки бота
            env_file = self.config_dir / '.env'
            logging.info(f"Загрузка .env файла: {env_file}")
            if env_file.exists():
                load_dotenv(env_file)
                logging.info(f".env файл загружен")
            else:
                raise ValueError(f"Файл .env не найден: {env_file}")
            
            # Путь к папке промптов (абсолютный путь)
            prompts_dir = self.config_dir / 'prompts'
            if not prompts_dir.exists():
                raise ValueError(f"Папка с промптами не найдена: {prompts_dir}")
            
            logging.info(f"Каталог промптов: {prompts_dir}")
            
            # Читаем переменные напрямую из .env файла
            logging.info(f"⚙️ Чтение конфигурации из .env...")
            
            # OpenAI настройки
            openai_api_key = os.getenv('OPENAI_API_KEY')
            openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            openai_max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '4000'))
            openai_temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
            
            # Supabase настройки
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            # Проверяем обязательные переменные
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY не найден в .env файле")
            if not supabase_url:
                raise ValueError("SUPABASE_URL не найден в .env файле")
            if not supabase_key:
                raise ValueError("SUPABASE_KEY не найден в .env файле")
            
            logging.info(f"Конфигурация загружена (модель: {openai_model})")
            
            logging.info(f"Инициализация OpenAI клиента...")
            self.openai_client = OpenAIClient(
                api_key=openai_api_key,
                model=openai_model,
                max_tokens=openai_max_tokens,
                temperature=openai_temperature
            )
            logging.info(f"OpenAI клиент создан (модель: {openai_model})")
            
            logging.info(f"Инициализация загрузчика промптов...")
            # PromptLoader автоматически найдет все .txt файлы в папке промптов
            self.prompt_loader = PromptLoader(prompts_dir=prompts_dir)
            logging.info(f"Загрузчик промптов создан")
            
            # Инициализируем Supabase клиент
            logging.info(f"Инициализация Supabase клиента...")
            self.supabase_client = SupabaseClient(
                url=supabase_url,
                key=supabase_key,
                bot_id=self.bot_id
            )
            logging.info(f"Supabase клиент создан")
            
            logging.info(f"Бот {self.bot_id} инициализирован успешно!")
            logging.info(f"══════════════════════════════════════════════════════════")
            
        except Exception as e:
            logging.error(f"══════════════════════════════════════════════════════════")
            logging.error(f"ОШИБКА ИНИЦИАЛИЗАЦИИ БОТА: {self.bot_id}")
            logging.error(f"Описание: {e}")
            logging.error(f"══════════════════════════════════════════════════════════")
            raise
    
    async def test_scenario(self, scenario: TestScenario) -> TestResult:
        """Тестирует сценарий с последовательными шагами"""
        try:
            # Инициализируем Supabase клиент перед тестом
            if not self.supabase_client.client:
                await self.supabase_client.initialize()
                logging.info(f"🔌 Supabase клиент инициализирован для бота {self.bot_id}")
            
            step_results = []
            
            # Генерируем уникальный тестовый telegram_id (только цифры)
            # Формат: 999 + timestamp + случайные цифры -> гарантированно уникальный
            timestamp_part = str(int(time.time()))[-6:]  # Последние 6 цифр timestamp
            random_part = str(uuid.uuid4().int)[:3]      # Первые 3 цифры из UUID
            unique_test_telegram_id = int(f"999{timestamp_part}{random_part}")
            
            user_data = {
                'telegram_id': unique_test_telegram_id,
                'username': 'test_user',
                'first_name': 'Test',
                'last_name': 'User',
                'language_code': 'ru'
            }
            
            logging.info(f"")
            logging.info(f"🧪 ═══════════════════════════════════════════════════════════")
            logging.info(f"🎯 НАЧИНАЕМ ТЕСТ СЦЕНАРИЯ: {scenario.name}")
            logging.info(f"🤖 Бот: {self.bot_id}")
            logging.info(f"👤 Тестовый пользователь: {unique_test_telegram_id}")
            logging.info(f"📝 Количество шагов: {len(scenario.steps)}")
            logging.info(f"═══════════════════════════════════════════════════════════")
            
            session_id, system_prompt = await self.create_test_session(user_data)
            logging.info(f"🆔 Создана тестовая сессия: {session_id}")
            
            for i, step in enumerate(scenario.steps):
                step_num = i + 1
                logging.info(f"")
                logging.info(f"🔄 ─────────────── ШАГ {step_num}/{len(scenario.steps)} ───────────────")
                logging.info(f"💬 Ввод пользователя: '{step.user_input}'")
                
                if step.expected_keywords:
                    # Форматируем ожидаемые ключевые слова для логов
                    expected_display = []
                    for group in step.expected_keywords:
                        if len(group) == 1:
                            expected_display.append(group[0])
                        else:
                            expected_display.append(f"[{'/'.join(group)}]")
                    logging.info(f"🎯 Ожидаемые слова: {expected_display}")
                if step.forbidden_keywords:
                    logging.info(f"🚫 Запрещенные слова: {step.forbidden_keywords}")
                
                # Анализируем ответ на этом шаге
                start_time = time.time()
                clean_response = await self.process_user_message_test(step.user_input, session_id, system_prompt)
                step_duration = int((time.time() - start_time) * 1000)
                
                # Показываем ответ бота (обрезанный)
                response_preview = clean_response[:150] + "..." if len(clean_response) > 150 else clean_response
                response_preview = response_preview.replace('\n', ' ')
                logging.info(f"🤖 Ответ бота: '{response_preview}'")
                logging.info(f"⏱️ Время обработки: {step_duration}мс")
                
                # Проверяем ожидаемые ключевые слова (с поддержкой синонимов)
                missing_keyword_groups = []
                found_expected = []
                for keyword_group in step.expected_keywords:
                    # keyword_group - это либо список синонимов, либо список с одним словом
                    found_in_group = False
                    found_synonym = None
                    
                    for synonym in keyword_group:
                        if synonym in clean_response.lower():
                            found_in_group = True
                            found_synonym = synonym
                            break
                    
                    if found_in_group:
                        found_expected.append(found_synonym)
                    else:
                        # Если группа синонимов не найдена, добавляем всю группу в missing
                        missing_keyword_groups.append(keyword_group)
                
                # Проверяем запрещенные ключевые слова
                found_forbidden = []
                for keyword in step.forbidden_keywords:
                    if keyword.lower() in clean_response.lower():
                        found_forbidden.append(keyword)
                
                # Выводим результаты проверки
                if found_expected:
                    logging.info(f"✅ Найденные ожидаемые: {found_expected}")
                if missing_keyword_groups:
                    # Показываем пропущенные группы синонимов в удобном формате
                    missing_display = []
                    for group in missing_keyword_groups:
                        if len(group) == 1:
                            missing_display.append(group[0])
                        else:
                            missing_display.append(f"[{'/'.join(group)}]")
                    logging.info(f"❌ НЕ найденные ожидаемые: {missing_display}")
                if found_forbidden:
                    logging.info(f"🚫 Найденные запрещенные: {found_forbidden}")
                
                # Определяем результат шага
                passed = len(missing_keyword_groups) == 0 and len(found_forbidden) == 0
                status_icon = "✅" if passed else "❌"
                status_text = "ПРОЙДЕН" if passed else "ПРОВАЛЕН"
                logging.info(f"🎯 Результат шага {step_num}: {status_icon} {status_text}")
                
                # Преобразуем missing_keyword_groups в плоский список для обратной совместимости
                missing_keywords_flat = []
                for group in missing_keyword_groups:
                    missing_keywords_flat.extend(group)
                
                step_result = StepResult(
                    step=step,
                    bot_response=clean_response,
                    passed=passed,
                    missing_keywords=missing_keywords_flat,
                    found_forbidden=found_forbidden
                )
                
                step_results.append(step_result)
                
                # Короткая пауза между шагами
                await asyncio.sleep(0.1)
            
            # Финальная статистика сценария
            passed_steps = sum(1 for step in step_results if step.passed)
            total_steps = len(step_results)
            success_rate = (passed_steps / total_steps) * 100 if total_steps > 0 else 0
            
            logging.info(f"")
            logging.info(f"🏁 ─────────────── ИТОГ СЦЕНАРИЯ ───────────────")
            logging.info(f"📊 Пройдено шагов: {passed_steps}/{total_steps} ({success_rate:.1f}%)")
            overall_status = "✅ СЦЕНАРИЙ ПРОЙДЕН" if passed_steps == total_steps else "❌ СЦЕНАРИЙ ПРОВАЛЕН"
            logging.info(f"🎯 {overall_status}")
            logging.info(f"═══════════════════════════════════════════════════════════")
            
            return TestResult(scenario=scenario, step_results=step_results)
            
        except Exception as e:
            logging.error(f"")
            logging.error(f"💥 ═══════════════════════════════════════════════════════════")
            logging.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА В СЦЕНАРИИ: {scenario.name}")
            logging.error(f"🐛 Ошибка: {str(e)}")
            logging.error(f"═══════════════════════════════════════════════════════════")
            logging.exception("📋 Полный стек ошибки:")
            
            # Создаем результат с ошибкой для всех шагов
            step_results = []
            for step in scenario.steps:
                step_result = StepResult(
                    step=step,
                    bot_response=f"ОШИБКА: {str(e)}",
                    passed=False,
                    missing_keywords=step.expected_keywords,
                    found_forbidden=[]
                )
                step_results.append(step_result)
            
            return TestResult(scenario=scenario, step_results=step_results)
    
    async def get_welcome_file_caption_test(self) -> str:
        """
        Тестовая версия получения подписи к приветственному файлу.
        Возвращает только текст из файла welcome_file_msg.txt без взаимодействия с ботом.
        
        Returns:
            str: текст подписи из файла или пустая строка
        """
        try:
            # Путь к папке welcome_files (абсолютный путь)
            folder = self.config_dir / 'welcome_files'
            if not folder.exists() or not folder.is_dir():
                logger.info(f"Директория приветственных файлов не найдена: {folder}")
                return ""

            # Ищем файл welcome_file_msg.txt в директории
            msg_path = folder / 'welcome_file_msg.txt'
            if not msg_path.is_file():
                logger.info(f"Файл подписи не найден: {msg_path}")
                return ""
                
            # Читаем содержимое файла
            try:
                with open(msg_path, 'r', encoding='utf-8') as f:
                    caption = f.read().strip()
                    logger.info(f"Подпись загружена из файла: {msg_path}")
                    return caption
            except Exception as e:
                logger.error(f"Ошибка при чтении файла подписи {msg_path}: {e}")
                return ""
            
        except Exception as e:
            logger.error(f"Ошибка при получении подписи к приветственному файлу: {e}")
            return ""
        
    async def create_test_session(self, user_data: dict) -> tuple[str, str]:
        """
        Создает тестовую сессию без взаимодействия с ботом.
        
        Args:
            user_data: словарь с данными пользователя (telegram_id, username, first_name, last_name, language_code)
            
        Returns:
            tuple[str, str, str]: (session_id, system_prompt, welcome_message)
            - session_id: ID созданной сессии
            - system_prompt: системный промпт
            - welcome_message: приветственное сообщение (включая подпись к файлу, если есть)
        """

        try:
            logging.info(f"🔄 Создание тестовой сессии...")
            
            # 1. ЗАГРУЖАЕМ ПРОМПТЫ
            logging.info(f"📋 Загрузка промптов...")
            system_prompt = await self.prompt_loader.load_system_prompt()
            welcome_message = await self.prompt_loader.load_welcome_message()
            logging.info(f"✅ Промпты загружены: система ({len(system_prompt)} симв.), приветствие ({len(welcome_message)} симв.)")
            
            # 2. СОЗДАЕМ НОВУЮ СЕССИЮ
            logging.info(f"🗄️ Создание сессии в Supabase...")
            session_id = await self.supabase_client.create_chat_session(user_data, system_prompt)
            logging.info(f"✅ Сессия создана с ID: {session_id}")
            
            # 3. ПРОВЕРЯЕМ НАЛИЧИЕ ПРИВЕТСТВЕННОГО ФАЙЛА И ЕГО ПОДПИСИ
            logging.info(f"📎 Проверка приветственного файла...")
            caption = await self.get_welcome_file_caption_test()
            
            # 4. ОБЪЕДИНЯЕМ ПРИВЕТСТВЕННОЕ СООБЩЕНИЕ С ПОДПИСЬЮ К ФАЙЛУ
            if caption:
                welcome_message = f"{welcome_message}\n\nПодпись к файлу:\n\n{caption}"
                logging.info(f"📎 Добавлена подпись к файлу ({len(caption)} симв.)")
            else:
                logging.info(f"📎 Приветственный файл не найден или пуст")
                
            # 5. СОХРАНЯЕМ ПРИВЕТСТВЕННОЕ СООБЩЕНИЕ В БД
            logging.info(f"💾 Сохранение приветственного сообщения в БД...")
            await self.supabase_client.add_message(
                session_id=session_id,
                role='assistant',
                content=welcome_message,
                message_type='text'
            )
            logging.info(f"✅ Приветственное сообщение сохранено")
            
            return session_id, system_prompt

        except Exception as e:
            logging.error(f"💥 Ошибка в create_test_session: {e}")
            logging.exception("📋 Полный стек ошибки:")
            raise

    async def process_user_message_test(self, user_message: str, session_id: str, system_prompt: str):
        """
        Тестовая версия обработки сообщений пользователя без взаимодействия с ботом.
        Возвращает только текст ответа от нейросети и сохраняет данные в БД.
        """

        from datetime import datetime
        import pytz
        import time
        
        # Читаем настройки напрямую из .env
        max_context_messages = int(os.getenv('MAX_CONTEXT_MESSAGES', '20'))

        try:
            logging.info(f"📨 Обработка сообщения пользователя...")
            
            # Сохраняем сообщение пользователя
            logging.info(f"💾 Сохранение сообщения пользователя в БД...")
            await self.supabase_client.add_message(
                session_id=session_id,
                role='user',
                content=user_message,
                message_type='text'
            )
            logging.info(f"✅ Сообщение пользователя сохранено")
            
            # Получаем историю сообщений
            logging.info(f"📚 Получение истории сообщений (лимит: {max_context_messages})...")
            chat_history = await self.supabase_client.get_chat_history(session_id, limit=max_context_messages)
            logging.info(f"✅ Получено {len(chat_history)} сообщений из истории")
            
            # Добавляем время
            moscow_tz = pytz.timezone('Europe/Moscow')
            current_time = datetime.now(moscow_tz)
            time_info = current_time.strftime('%H:%M, %d.%m.%Y, %A')
            logging.info(f"🕐 Текущее время: {time_info}")
            
            # Модифицируем системный промпт с временем
            system_prompt_with_time = f"""
    {system_prompt}

    ТЕКУЩЕЕ ВРЕМЯ: {time_info} (московское время)
    """
            
            # Формируем контекст для OpenAI
            messages = [{"role": "system", "content": system_prompt_with_time}]
            
            for msg in chat_history[-max_context_messages:]:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
            
            # Добавляем финальные инструкции
            logging.info(f"📋 Загрузка финальных инструкций...")
            final_instructions = await self.prompt_loader.load_final_instructions()
            if final_instructions:
                messages.append({"role": "system", "content": final_instructions})
                logging.info(f"✅ Финальные инструкции добавлены ({len(final_instructions)} симв.)")
            else:
                logging.info(f"📋 Финальные инструкции отсутствуют")
            
            logging.info(f"🧠 Отправка запроса к OpenAI (сообщений в контексте: {len(messages)})...")
            
            # Получаем ответ от OpenAI
            start_time = time.time()
            ai_response = await self.openai_client.get_completion(messages)
            processing_time = int((time.time() - start_time) * 1000)
            
            logging.info(f"✅ Ответ получен от OpenAI за {processing_time}мс")

            # Инициализируем переменные
            tokens_used = 0
            ai_metadata = {}
            response_text = ""

            # Проверяем ответ
            if not ai_response or not ai_response.strip():
                response_text = "Извините, произошла техническая ошибка. Попробуйте переформулировать вопрос."
                tokens_used = 0
                ai_metadata = {}
                logging.warning(f"⚠️ Пустой ответ от OpenAI")
            else:
                tokens_used = self.openai_client.estimate_tokens(ai_response)
                logging.info(f"🔢 Оценка токенов: {tokens_used}")
                
                logging.info(f"🔍 Парсинг AI-ответа на метаданные...")
                response_text, ai_metadata = parse_ai_response(ai_response)

                if not ai_metadata:
                    response_text = ai_response
                    ai_metadata = {}
                    logging.info(f"📝 Метаданные не найдены, используем исходный ответ")
                elif not response_text.strip():
                    response_text = ai_response
                    logging.info(f"📝 Пустой текст после парсинга, используем исходный ответ")
                else:
                    logging.info(f"📝 Найдены метаданные: {list(ai_metadata.keys())}")

                # Обновляем этап сессии и качество лида если есть метаданные
                if ai_metadata:
                    stage = ai_metadata.get('этап')
                    quality = ai_metadata.get('качество')
                    if stage or quality is not None:
                        logging.info(f"🎯 Обновление этапа сессии: этап={stage}, качество={quality}")
                        await self.supabase_client.update_session_stage(session_id, stage, quality)

            # Сохраняем ответ ассистента
            logging.info(f"💾 Сохранение ответа ассистента в БД...")
            await self.supabase_client.add_message(
                session_id=session_id,
                role='assistant',
                content=response_text,
                message_type='text',
                tokens_used=tokens_used,
                processing_time_ms=processing_time,
                ai_metadata=ai_metadata
            )
            logging.info(f"✅ Ответ ассистента сохранен")

            return response_text

        except Exception as e:
            logging.error(f"💥 Ошибка в process_user_message_test: {e}")
            logging.exception("📋 Полный стек ошибки:")
            return "Произошла ошибка при обработке сообщения."


class TestRunner:
    """Запускатель тестов с асинхронным выполнением"""
    
    def __init__(self, bot_id: str, max_concurrent: int = 5, project_root: Path = None):
        self.bot_id = bot_id
        self.max_concurrent = max_concurrent
        self.project_root = project_root or get_project_root()
        self.bot_tester = BotTester(bot_id, self.project_root)
    
    async def run_tests(self, scenarios: List[TestScenario]) -> List[TestResult]:
        """Запускает тесты асинхронно"""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def run_single_test(scenario: TestScenario) -> TestResult:
            async with semaphore:
                logging.info(f"🧪 Выполнение теста: {scenario.name}")
                result = await self.bot_tester.test_scenario(scenario)
                status = "✅" if result.passed else "❌"
                logging.info(f"   {status} {scenario.name}")
                return result
        
        # Запускаем все тесты параллельно
        tasks = [run_single_test(scenario) for scenario in scenarios]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем исключения
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logging.error(f"Исключение в тесте {scenarios[i].name}: {result}")
                # Создаем результат с ошибкой для всех шагов
                step_results = []
                for step in scenarios[i].steps:
                    step_result = StepResult(
                        step=step,
                        bot_response=f"ИСКЛЮЧЕНИЕ: {str(result)}",
                        passed=False,
                        missing_keywords=step.expected_keywords,
                        found_forbidden=[]
                    )
                    step_results.append(step_result)
                
                processed_results.append(TestResult(
                    scenario=scenarios[i],
                    step_results=step_results
                ))
            else:
                processed_results.append(result)
        
        return processed_results


class ReportGenerator:
    """Генератор отчетов о тестировании"""
    
    @staticmethod
    def cleanup_old_reports(reports_dir: str, max_reports: int = 10):
        """Удаляет старые отчеты, оставляя только max_reports самых новых"""
        if not os.path.exists(reports_dir):
            return
        
        # Находим все файлы отчетов
        report_pattern = os.path.join(reports_dir, "test_*.txt")
        report_files = glob.glob(report_pattern)
        
        if len(report_files) <= max_reports:
            return  # Количество файлов в пределах лимита
        
        # Сортируем по времени модификации (старые первыми)
        report_files.sort(key=lambda x: os.path.getmtime(x))
        
        # Удаляем старые файлы, оставляя только max_reports-1 (место для нового)
        files_to_delete = report_files[:-(max_reports-1)]
        
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                filename = os.path.basename(file_path)
                logging.info(f"🗑️ Удален старый отчет: {filename}")
            except Exception as e:
                logging.warning(f"Не удалось удалить отчет {file_path}: {e}")
    
    @staticmethod
    def generate_console_report(bot_id: str, results: List[TestResult]):
        """Генерирует отчет в консоль"""
        passed_count = sum(1 for r in results if r.passed)
        failed_count = len(results) - passed_count
        total_steps = sum(r.total_steps for r in results)
        passed_steps = sum(r.passed_steps for r in results)
        success_rate = (passed_count / len(results)) * 100 if results else 0
        step_success_rate = (passed_steps / total_steps) * 100 if total_steps else 0
        
        print(f"\n📊 РЕЗУЛЬТАТЫ: {bot_id.upper()}")
        print(f"✅ Сценариев пройдено: {passed_count}/{len(results)} ({success_rate:.1f}%)")
        print(f"📝 Шагов пройдено: {passed_steps}/{total_steps} ({step_success_rate:.1f}%)")
        
        # Определяем уровень качества по сценариям
        if success_rate >= 90:
            print("🎉 ОТЛИЧНО — бот готов к продакшену")
        elif success_rate >= 80:
            print("✅ ХОРОШО — небольшие улучшения")
        elif success_rate >= 60:
            print("⚠️ УДОВЛЕТВОРИТЕЛЬНО — требуются улучшения")
        else:
            print("🚨 ПЛОХО — критические проблемы с промптами")
    
    @staticmethod
    def generate_detailed_report(bot_id: str, results: List[TestResult]) -> str:
        """Генерирует подробный отчет"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report_lines = [
            f"ОТЧЕТ ТЕСТИРОВАНИЯ: {bot_id.upper()}",
            f"Время: {timestamp}",
            f"Сценариев: {len(results)}",
            ""
        ]
        
        # Статистика
        passed_count = sum(1 for r in results if r.passed)
        total_steps = sum(r.total_steps for r in results)
        passed_steps = sum(r.passed_steps for r in results)
        success_rate = (passed_count / len(results)) * 100 if results else 0
        step_success_rate = (passed_steps / total_steps) * 100 if total_steps else 0
        
        report_lines.extend([
            f"УСПЕШНОСТЬ СЦЕНАРИЕВ: {success_rate:.1f}% ({passed_count}/{len(results)})",
            f"УСПЕШНОСТЬ ШАГОВ: {step_success_rate:.1f}% ({passed_steps}/{total_steps})",
            ""
        ])
        
        # Список ошибок в требуемом формате
        failed_tests = [r for r in results if not r.passed]
        if failed_tests:
            report_lines.extend([
                "═══════════════════════════════════════════════════════════════",
                "СПИСОК ОШИБОК:",
                "═══════════════════════════════════════════════════════════════"
            ])
            
            for result in failed_tests:
                scenario = result.scenario
                source_file = getattr(scenario, 'source_file', 'unknown')
                scenario_number = getattr(scenario, 'scenario_number', '?')
                
                # Правильное отображение имени сценария
                display_name = scenario.name if not scenario.name.startswith('[') else f"[{source_file}-{scenario_number}]"
                report_lines.extend([
                    f"ФАЙЛ: {source_file}.yaml | СЦЕНАРИЙ: {display_name}",
                    f"СТАТУС: {result.passed_steps}/{result.total_steps} шагов пройдено",
                    ""
                ])
                
                # Детальная информация о каждом шаге
                for i, step_result in enumerate(result.step_results):
                    step_num = i + 1
                    status = "✅" if step_result.passed else "❌"
                    
                    # Форматируем ожидаемые ключевые слова с учетом синонимов
                    expected_display = []
                    for group in step_result.step.expected_keywords:
                        if len(group) == 1:
                            expected_display.append(group[0])
                        else:
                            expected_display.append(f"[{'/'.join(group)}]")
                    
                    report_lines.extend([
                        f"ШАГ {step_num} {status}:",
                        f"  Ввод: \"{step_result.step.user_input}\"",
                        f"  Ожидаемые: {expected_display}",
                        f"  Запрещенные: {step_result.step.forbidden_keywords}",
                        ""
                    ])
                    
                    # Полный ответ бота для всех шагов (и успешных, и провальных)
                    bot_response = step_result.bot_response.strip()
                    # Заменяем переносы строк на символы для лучшей читаемости в отчете
                    bot_response_formatted = bot_response.replace('\n', '\\n')
                    
                    report_lines.extend([
                        f"  Полный ответ бота:",
                        f"  \"{bot_response_formatted}\"",
                        ""
                    ])
                    
                    # Конкретные ошибки для неуспешных шагов
                    if not step_result.passed:
                        if step_result.missing_keywords:
                            report_lines.append(f"    ❌ НЕ НАЙДЕНЫ: {', '.join(step_result.missing_keywords)}")
                        
                        if step_result.found_forbidden:
                            report_lines.append(f"    ❌ НАЙДЕНЫ ЗАПРЕЩЕННЫЕ: {', '.join(step_result.found_forbidden)}")
                        
                        report_lines.append("")
                
                report_lines.extend([
                    "-" * 67,
                    ""
                ])
        
        # Краткая сводка по пройденным тестам
        passed_tests = [r for r in results if r.passed]
        if passed_tests:
            report_lines.extend([
                "ПРОЙДЕННЫЕ СЦЕНАРИИ:",
                ""
            ])
            for result in passed_tests:
                scenario = result.scenario
                source_file = getattr(scenario, 'source_file', 'unknown')
                scenario_number = getattr(scenario, 'scenario_number', '?')
                
                # Правильное отображение имени сценария для пройденных тестов (сокращенный формат)
                display_name = scenario.name if not scenario.name.startswith('[') else f"[{source_file}-{scenario_number}]"
                report_lines.append(f"✅ {source_file}.yaml | {display_name}")
        
        return "\n".join(report_lines)
    
    @staticmethod
    def save_report(bot_id: str, results: List[TestResult], project_root: Path = None) -> str:
        """Сохраняет отчет в файл"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Используем переданную корневую директорию или глобальную
        user_root_dir = project_root or get_project_root()
        
        # Проверяем наличие папки bots/{bot_id}
        bots_dir = user_root_dir / "bots" / bot_id
        if not bots_dir.exists():
            logging.warning(f"Папка bots/{bot_id} не найдена в проекте: {bots_dir}")
            return ""
        
        # Создаем папку отчетов в папке бота
        reports_dir = user_root_dir / "bots" / bot_id / "reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        # Очищаем старые отчеты перед созданием нового
        ReportGenerator.cleanup_old_reports(str(reports_dir), max_reports=10)
        
        # Лаконичное название файла
        report_filename = reports_dir / f"test_{timestamp}.txt"
        
        report_content = ReportGenerator.generate_detailed_report(bot_id, results)
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(report_filename)


async def main():
    """Главная функция CLI"""
    parser = argparse.ArgumentParser(description="Система тестирования ботов")
    parser.add_argument("bot_id", nargs="?", default="growthmed-october-24", 
                       help="ID бота для тестирования")
    parser.add_argument("scenario_file", nargs="?", default=None,
                       help="Название файла сценариев (без расширения или с .yaml)")
    parser.add_argument("--scenario-file", dest="scenario_file_legacy", 
                       help="Конкретный файл сценариев (устаревший параметр)")
    parser.add_argument("--max-concurrent", type=int, default=5, 
                       help="Максимальное количество параллельных тестов")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Подробный вывод")
    
    args = parser.parse_args()
    
    # Настройка логирования
    log_level = logging.INFO if args.verbose else logging.INFO  # Всегда показываем INFO
    logging.basicConfig(level=log_level, format='%(message)s')
    
    try:
        # Определяем какой файл сценариев использовать
        scenario_file = args.scenario_file or args.scenario_file_legacy
        
        # Получаем корневую директорию проекта
        project_root = get_project_root()
        
        # Загружаем сценарии
        if scenario_file:
            # Обрабатываем название файла
            if not scenario_file.endswith('.yaml'):
                scenario_file += '.yaml'
            
            # Проверяем наличие папки bots/{bot_id}
            bots_dir = project_root / "bots" / args.bot_id
            if not bots_dir.exists():
                print(f"Папка bots/{args.bot_id} не найдена в проекте: {bots_dir}")
                return 1
            
            # Путь к файлу сценариев в корневой директории проекта
            scenario_path = project_root / "bots" / args.bot_id / "tests" / scenario_file
            scenarios = ScenarioLoader.load_scenarios_from_file(str(scenario_path))
            
            if not scenarios:
                print(f"Файл сценариев '{scenario_file}' не найден или пуст")
                return 1
        else:
            scenarios = ScenarioLoader.load_all_scenarios_for_bot(args.bot_id, project_root)
            
            if not scenarios:
                print(f"Сценарии для бота '{args.bot_id}' не найдены")
                return 1
        
        print(f"🚀 Запуск тестирования бота: {args.bot_id}")
        if scenario_file:
            print(f"📋 Тестируется файл: {scenario_file}")
        else:
            print(f"📋 Тестируются все файлы сценариев")
        print(f"📋 Найдено сценариев: {len(scenarios)}")
        
        # Запускаем тесты
        test_runner = TestRunner(args.bot_id, args.max_concurrent, project_root)
        results = await test_runner.run_tests(scenarios)
        
        # Генерируем отчеты
        ReportGenerator.generate_console_report(args.bot_id, results)
        report_file = ReportGenerator.save_report(args.bot_id, results, project_root)
        
        print(f"\n📄 Подробный отчет сохранен: {report_file}")
        
        # Возвращаем код выхода
        failed_count = sum(1 for r in results if not r.passed)
        return 0 if failed_count == 0 else 1
        
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(130)
        
