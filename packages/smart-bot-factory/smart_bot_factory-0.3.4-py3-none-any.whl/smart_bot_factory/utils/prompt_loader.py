# Обновленный prompt_loader.py с поддержкой финальных инструкций

import logging
import aiofiles
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

class PromptLoader:
    """Класс для загрузки промптов из локального каталога"""
    
    def __init__(self, prompts_dir: str):
            self.prompts_dir = Path(prompts_dir)
            self.welcome_file = self.prompts_dir / 'welcome_message.txt'
            self.help_file = self.prompts_dir / 'help_message.txt'
            self.final_instructions_file = self.prompts_dir / 'final_instructions.txt'
            
            # Автоматически находим все .txt файлы промптов (кроме специальных)
            all_txt_files = list(self.prompts_dir.glob('*.txt'))
            special_files = {'welcome_message.txt', 'help_message.txt', 'final_instructions.txt'}
            self.prompt_files = [f.name for f in all_txt_files if f.name not in special_files]
            
            logger.info(f"Инициализирован загрузчик промптов: {self.prompts_dir}")
            logger.info(f"Найдено файлов промптов: {len(self.prompt_files)}")
            logger.info(f"Файлы промптов: {self.prompt_files}")

    async def load_system_prompt(self) -> str:
        """
        Загружает и объединяет все файлы промптов в один системный промпт
        
        Returns:
            Объединенный системный промпт с инструкциями по JSON
        """
        try:
            prompt_parts = []
            
            for filename in self.prompt_files:
                logger.debug(f"Загружаем промпт из {filename}")
                content = await self._load_file(filename)
                
                if content:
                    # Добавляем заголовок секции
                    section_name = self._get_section_name(filename)
                    prompt_parts.append(f"\n### {section_name} ###\n")
                    prompt_parts.append(content.strip())
                    prompt_parts.append("\n")
                else:
                    logger.warning(f"Файл {filename} пуст")
            
            if not prompt_parts:
                error_msg = "Не удалось загрузить ни одного промпт файла"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Добавляем инструкции по JSON метаданным
            json_instructions = self._get_json_instructions()
            prompt_parts.append("\n")
            prompt_parts.append(json_instructions)
            
            # Объединяем все части
            full_prompt = "".join(prompt_parts).strip()
            
            logger.info(f"Системный промпт загружен успешно ({len(full_prompt)} символов)")
            return full_prompt
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке системного промпта: {e}")
            raise

    async def load_final_instructions(self) -> str:
        """
        Загружает финальные инструкции из final_instructions.txt
        
        Returns:
            Финальные инструкции или пустая строка если файла нет
        """
        try:
            logger.debug(f"Загружаем финальные инструкции из {self.final_instructions_file.name}")
            
            if not self.final_instructions_file.exists():
                logger.debug(f"Файл {self.final_instructions_file.name} не найден - пропускаем")
                return ""
            
            async with aiofiles.open(self.final_instructions_file, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            if not content.strip():
                logger.debug(f"Файл {self.final_instructions_file.name} пуст - пропускаем")
                return ""
            
            logger.info(f"Финальные инструкции загружены ({len(content)} символов)")
            return content.strip()
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке финальных инструкций: {e}")
            # Не прерываем работу - финальные инструкции опциональны
            return ""
    
    def _get_json_instructions(self) -> str:
        """Возвращает инструкции по JSON метаданным для ИИ"""
        return """
### КРИТИЧЕСКИ ВАЖНЫЕ ИНСТРУКЦИИ ПО JSON МЕТАДАННЫМ ###

В КОНЦЕ КАЖДОГО своего ответа ОБЯЗАТЕЛЬНО добавляй служебную информацию в JSON формате:

{
  "этап": "introduction|consult|offer|contacts",
  "качество": 1-10,
  "события": [
    {
      "тип": "телефон|консультация|покупка|отказ",
      "инфо": "детали события"
    }
  ],
  "файлы": ["file1.pdf", "file2.mp4"],
  "каталоги": ["каталог1", "каталог2"]
}

ОПИСАНИЕ ЭТАПОВ:
- introduction: знакомство, сбор базовой информации о клиенте
- consult: консультирование, ответы на вопросы о конференции
- offer: предложение тарифов, обработка возражений
- contacts: получение контактов, завершение сделки

СИСТЕМА ОЦЕНКИ КАЧЕСТВА (1-10):
1-3: низкий интерес, много возражений, скептически настроен
4-6: средний интерес, есть вопросы, обдумывает
7-8: высокий интерес, готов к покупке, активно интересуется  
9-10: горячий лид, предоставил контакты или готов к действию

СОБЫТИЯ - добавляй ТОЛЬКО когда происходит что-то из этого:
- "телефон": пользователь предоставил номер телефона
- "консультация": пользователь просит живую консультацию по телефону
- "покупка": пользователь готов купить/записаться на конференцию
- "отказ": пользователь явно отказывается участвовать

ВАЖНО:
- Добавляй файлы и катологи только в том случае, если они относятся к этому этапу. (Прописаны в самом этапе) Если не относятся - отсылай пустой массив []

ПРИМЕРЫ ПРАВИЛЬНОГО ИСПОЛЬЗОВАНИЯ:

Пример 1 - обычный диалог:
"Расскажу подробнее о конференции GrowthMED. Она пройдет 24-25 октября..."

{
  "этап": "consult",
  "качество": 6,
  "события": [],
  "файлы": [],
  "каталоги": []
}

Пример 2 - получен телефон:
"Отлично! Записал ваш номер. Мы перезвоним в течение 10 минут!"

{
  "этап": "contacts", 
  "качество": 9,
  "события": [
    {
      "тип": "телефон",
      "инфо": "Иван Петров +79219603144"
    }
  ],
  "файлы": [],
  "каталоги": []
}

Пример 3 - отправка презентации:
"Отправляю вам презентацию о нашей компании и прайс-лист с актуальными ценами."

{
  "этап": "offer",
  "качество": 7,
  "события": [
    {
      "тип": "консультация", 
      "инфо": "Запросил материалы"
    }
  ],
  "файлы": ["презентация.pdf", "прайс.pdf"],
  "каталоги": []
}

Пример 4 - отправка файлов из каталога:
"В каталоге 'примеры_работ' вы можете посмотреть наши последние проекты."

{
  "этап": "presentation",
  "качество": 8,
  "события": [],
  "файлы": [],
  "каталоги": ["примеры_работ"]
}

Пример 5 - комбинированная отправка:
"Отправляю вам коммерческое предложение и примеры похожих проектов из нашего портфолио."

{
  "этап": "offer",
  "качество": 9,
  "события": [
    {
      "тип": "предложение",
      "инфо": "Отправлено КП"
    }
  ],
  "файлы": ["коммерческое_предложение.pdf"],
  "каталоги": ["портфолио_2023"]
}

ТРЕБОВАНИЯ К JSON:
- JSON должен быть валидным и находиться в самом конце ответа
- Всегда используй кавычки для строк
- Массив "события" может быть пустым []
- Если событий нет - не добавляй их в массив
- Качество должно быть числом от 1 до 10

ПОМНИ: Этот JSON критически важен для работы системы администрирования и аналитики!
"""
    
    async def load_welcome_message(self) -> str:
        """
        Загружает приветственное сообщение из welcome_message.txt
        
        Returns:
            Текст приветственного сообщения
        """
        try:
            logger.debug(f"Загружаем приветственное сообщение из {self.welcome_file.name}")
            
            if not self.welcome_file.exists():
                error_msg = f"Файл приветствия не найден: {self.welcome_file}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            async with aiofiles.open(self.welcome_file, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            if not content.strip():
                error_msg = f"Файл приветствия пуст: {self.welcome_file}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"Приветственное сообщение загружено ({len(content)} символов)")
            return content.strip()
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке приветственного сообщения: {e}")
            raise
            
    async def load_help_message(self) -> str:
        """
        Загружает справочное сообщение из help_message.txt
        
        Returns:
            Текст справочного сообщения
        """
        try:
            logger.debug(f"Загружаем справочное сообщение из {self.help_file.name}")
            
            if self.help_file.exists():
                async with aiofiles.open(self.help_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                
                if content.strip():
                    logger.info(f"Справочное сообщение загружено ({len(content)} символов)")
                    return content.strip()
            
            # Fallback если файл не найден или пуст
            logger.warning("Файл help_message.txt не найден или пуст, используем дефолтную справку")
            return "🤖 **Ваш помощник готов к работе!**\n\n**Команды:**\n/start - Начать диалог\n/help - Показать справку\n/status - Проверить статус"
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке справочного сообщения: {e}")
            # Возвращаем простую справку в случае ошибки
            return "🤖 Ваш помощник готов к работе! Напишите /start для начала диалога."

    async def _load_file(self, filename: str) -> str:
        """Загружает содержимое файла из каталога промптов"""
        file_path = self.prompts_dir / filename
        
        try:
            if not file_path.exists():
                error_msg = f"Файл промпта не найден: {file_path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            if not content.strip():
                logger.warning(f"Файл {filename} пуст")
                return ""
            
            logger.debug(f"Загружен файл {filename} ({len(content)} символов)")
            return content
            
        except Exception as e:
            logger.error(f"Ошибка чтения файла {file_path}: {e}")
            raise
    
    def _get_section_name(self, filename: str) -> str:
        """Получает название секции по имени файла"""
        name_mapping = {
            'system_prompt.txt': 'СИСТЕМНЫЙ ПРОМПТ',
            'sales_context.txt': 'КОНТЕКСТ ПРОДАЖ', 
            'product_info.txt': 'ИНФОРМАЦИЯ О ПРОДУКТЕ',
            'objection_handling.txt': 'ОБРАБОТКА ВОЗРАЖЕНИЙ',
            '1sales_context.txt': 'КОНТЕКСТ ПРОДАЖ',
            '2product_info.txt': 'ИНФОРМАЦИЯ О ПРОДУКТЕ', 
            '3objection_handling.txt': 'ОБРАБОТКА ВОЗРАЖЕНИЙ',
            'final_instructions.txt': 'ФИНАЛЬНЫЕ ИНСТРУКЦИИ'  # 🆕
        }
        
        return name_mapping.get(filename, filename.replace('.txt', '').upper())
    
    async def reload_prompts(self) -> str:
        """Перезагружает промпты (для обновления без перезапуска бота)"""
        logger.info("Перезагрузка промптов...")
        return await self.load_system_prompt()
    
    async def validate_prompts(self) -> Dict[str, bool]:
        """Проверяет доступность всех файлов промптов и приветственного сообщения"""
        results = {}
        
        # Проверяем файлы промптов
        for filename in self.prompt_files:
            file_path = self.prompts_dir / filename
            try:
                if file_path.exists():
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                    results[filename] = bool(content.strip() and len(content.strip()) > 10)
                else:
                    results[filename] = False
            except Exception:
                results[filename] = False
        
        # Проверяем файл приветственного сообщения
        try:
            if self.welcome_file.exists():
                async with aiofiles.open(self.welcome_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                results['welcome_message.txt'] = bool(content.strip() and len(content.strip()) > 5)
            else:
                results['welcome_message.txt'] = False
        except Exception:
            results['welcome_message.txt'] = False
        
        # Проверяем файл справки (опционально)
        try:
            if self.help_file.exists():
                async with aiofiles.open(self.help_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                results['help_message.txt'] = bool(content.strip() and len(content.strip()) > 5)
            else:
                results['help_message.txt'] = False  # Не критично
        except Exception:
            results['help_message.txt'] = False
        
        # 🆕 Проверяем финальные инструкции (опционально)
        try:
            if self.final_instructions_file.exists():
                async with aiofiles.open(self.final_instructions_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                results['final_instructions.txt'] = bool(content.strip() and len(content.strip()) > 5)
            else:
                results['final_instructions.txt'] = False  # Не критично - опциональный файл
        except Exception:
            results['final_instructions.txt'] = False
        
        return results
    
    def get_prompt_info(self) -> Dict[str, any]:
        """Возвращает информацию о конфигурации промптов"""
        return {
            'prompts_dir': str(self.prompts_dir),
            'prompt_files': self.prompt_files,
            'welcome_file': 'welcome_message.txt',
            'help_file': 'help_message.txt',
            'final_instructions_file': 'final_instructions.txt',  # 🆕
            'total_files': len(self.prompt_files) + 1,  # +1 для welcome message
            'json_instructions_included': True
        }
    
    async def test_json_parsing(self, test_response: str) -> Dict[str, any]:
        """Тестирует парсинг JSON из ответа ИИ (для отладки)"""
        import json
        import re
        
        try:
            # Используем тот же алгоритм что и в main.py
            json_pattern = r'\{[^{}]*"этап"[^{}]*\}$'
            match = re.search(json_pattern, test_response.strip())
            
            if match:
                json_str = match.group(0)
                response_text = test_response[:match.start()].strip()
                
                try:
                    metadata = json.loads(json_str)
                    return {
                        'success': True,
                        'response_text': response_text,
                        'metadata': metadata,
                        'json_str': json_str
                    }
                except json.JSONDecodeError as e:
                    return {
                        'success': False,
                        'error': f"JSON decode error: {e}",
                        'json_str': json_str
                    }
            else:
                return {
                    'success': False,
                    'error': "JSON pattern not found",
                    'response_text': test_response
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Parse error: {e}"
            }