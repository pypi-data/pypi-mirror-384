"""
UserPromptLoader - упрощенный PromptLoader для пользователей библиотеки
с автоматическим поиском prompts_dir от корня проекта
"""

import logging
from pathlib import Path
from .prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class UserPromptLoader(PromptLoader):
    """
    PromptLoader для пользователей библиотеки с автоматическим поиском prompts_dir
    
    Автоматически находит папку prompts для указанного бота от корня проекта
    Наследуется от базового PromptLoader - все методы доступны
    """
    
    def __init__(self, bot_id: str, prompts_subdir: str = "prompts"):
        """
        Инициализация загрузчика промптов с автоматическим поиском
        
        Args:
            bot_id: Идентификатор бота
            prompts_subdir: Подпапка с промптами (по умолчанию "prompts")
            
        Example:
            # Автоматически найдет bots/my-bot/prompts
            loader = UserPromptLoader("my-bot")
            
            # Или кастомную подпапку
            loader = UserPromptLoader("my-bot", "custom_prompts")
            
            # Наследование для кастомизации
            class MyLoader(UserPromptLoader):
                def __init__(self, bot_id):
                    super().__init__(bot_id)
                    # Добавить свою логику
                    self.extra_file = self.prompts_dir / 'extra.txt'
        """
        from project_root_finder import root
        
        # Автоматически определяем путь к промптам
        prompts_dir = root / "bots" / bot_id / prompts_subdir
        
        if not prompts_dir.exists():
            logger.warning(f"⚠️ Папка промптов не найдена: {prompts_dir}")
            logger.warning(f"   Создайте папку или проверьте bot_id")
        
        # Вызываем базовую инициализацию
        super().__init__(str(prompts_dir))
        
        logger.info(f"✅ UserPromptLoader создан для bot_id '{bot_id}': {prompts_dir}")

