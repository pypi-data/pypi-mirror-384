"""
Менеджер роутеров для Smart Bot Factory
"""

from typing import Dict, List, Any, Optional
import logging
from .router import EventRouter

logger = logging.getLogger(__name__)

class RouterManager:
    """
    Менеджер для управления роутерами событий и их обработчиками
    """
    
    def __init__(self):
        self._routers: List[EventRouter] = []
        self._combined_handlers: Dict[str, Dict[str, Any]] = {
            'event_handlers': {},
            'scheduled_tasks': {},
            'global_handlers': {}
        }
        
        logger.info("🔄 Создан менеджер роутеров")
    
    def register_router(self, router: EventRouter):
        """
        Регистрирует роутер событий в менеджере
        
        Args:
            router: EventRouter для регистрации
        """
        if router not in self._routers:
            self._routers.append(router)
            self._update_combined_handlers()
            logger.info(f"✅ Зарегистрирован роутер: {router.name}")
        else:
            logger.warning(f"⚠️ Роутер {router.name} уже зарегистрирован")
    
    def unregister_router(self, router: EventRouter):
        """
        Отменяет регистрацию роутера событий
        
        Args:
            router: EventRouter для отмены регистрации
        """
        if router in self._routers:
            self._routers.remove(router)
            self._update_combined_handlers()
            logger.info(f"❌ Отменена регистрация роутера: {router.name}")
        else:
            logger.warning(f"⚠️ Роутер {router.name} не найден в зарегистрированных")
    
    def _update_combined_handlers(self):
        """Обновляет объединенные обработчики всех роутеров"""
        # Очищаем текущие обработчики
        self._combined_handlers = {
            'event_handlers': {},
            'scheduled_tasks': {},
            'global_handlers': {}
        }
        
        logger.debug(f"🔍 RouterManager._update_combined_handlers(): обновляем обработчики для {len(self._routers)} роутеров")
        
        # Собираем обработчики из всех роутеров
        for router in self._routers:
            logger.debug(f"🔍 Обрабатываем роутер: {router.name}")
            
            # Обработчики событий
            event_handlers = router.get_event_handlers()
            logger.debug(f"🔍 Роутер {router.name}: {len(event_handlers)} обработчиков событий")
            for event_type, handler_info in event_handlers.items():
                if event_type in self._combined_handlers['event_handlers']:
                    existing_router = self._combined_handlers['event_handlers'][event_type]['router']
                    logger.warning(f"⚠️ Конфликт обработчиков событий '{event_type}' между роутерами {existing_router} и {router.name}")
                self._combined_handlers['event_handlers'][event_type] = handler_info
            
            # Запланированные задачи
            scheduled_tasks = router.get_scheduled_tasks()
            logger.debug(f"🔍 Роутер {router.name}: {len(scheduled_tasks)} запланированных задач: {list(scheduled_tasks.keys())}")
            for task_name, task_info in scheduled_tasks.items():
                if task_name in self._combined_handlers['scheduled_tasks']:
                    existing_router = self._combined_handlers['scheduled_tasks'][task_name]['router']
                    logger.warning(f"⚠️ Конфликт задач '{task_name}' между роутерами {existing_router} и {router.name}")
                self._combined_handlers['scheduled_tasks'][task_name] = task_info
            
            # Глобальные обработчики
            global_handlers = router.get_global_handlers()
            logger.debug(f"🔍 Роутер {router.name}: {len(global_handlers)} глобальных обработчиков")
            for handler_type, handler_info in global_handlers.items():
                if handler_type in self._combined_handlers['global_handlers']:
                    existing_router = self._combined_handlers['global_handlers'][handler_type]['router']
                    logger.warning(f"⚠️ Конфликт глобальных обработчиков '{handler_type}' между роутерами {existing_router} и {router.name}")
                self._combined_handlers['global_handlers'][handler_type] = handler_info
        
        logger.debug(f"🔍 RouterManager._update_combined_handlers(): итого - {len(self._combined_handlers['scheduled_tasks'])} задач: {list(self._combined_handlers['scheduled_tasks'].keys())}")
        
        total_handlers = (len(self._combined_handlers['event_handlers']) + 
                         len(self._combined_handlers['scheduled_tasks']) + 
                         len(self._combined_handlers['global_handlers']))
        
        logger.info(f"📊 Обновлены объединенные обработчики: {total_handlers} обработчиков из {len(self._routers)} роутеров")
    
    def get_event_handlers(self) -> Dict[str, Dict[str, Any]]:
        """Получает все обработчики событий"""
        return self._combined_handlers['event_handlers'].copy()
    
    def get_scheduled_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Получает все запланированные задачи"""
        tasks = self._combined_handlers['scheduled_tasks'].copy()
        logger.debug(f"🔍 RouterManager.get_scheduled_tasks(): возвращаем {len(tasks)} задач: {list(tasks.keys())}")
        return tasks
    
    def get_global_handlers(self) -> Dict[str, Dict[str, Any]]:
        """Получает все глобальные обработчики"""
        return self._combined_handlers['global_handlers'].copy()
    
    def get_all_handlers(self) -> Dict[str, Dict[str, Any]]:
        """Получает все обработчики всех типов"""
        all_handlers = {}
        all_handlers.update(self._combined_handlers['event_handlers'])
        all_handlers.update(self._combined_handlers['scheduled_tasks'])
        all_handlers.update(self._combined_handlers['global_handlers'])
        return all_handlers
    
    def get_handlers_for_prompt(self) -> str:
        """Возвращает описание всех обработчиков для добавления в промпт ИИ"""
        prompt_parts: List[str] = []
        
        if not any(self._combined_handlers.values()):
            return ""
        
        if self._combined_handlers['event_handlers']:
            prompt_parts.append("ДОСТУПНЫЕ ОБРАБОТЧИКИ СОБЫТИЙ:")
            for event_type, handler_info in self._combined_handlers['event_handlers'].items():
                router_name = handler_info.get('router', 'unknown')
                prompt_parts.append(f"- {event_type}: {handler_info['name']} (роутер: {router_name})")
        
        if self._combined_handlers['scheduled_tasks']:
            prompt_parts.append("\nДОСТУПНЫЕ ЗАДАЧИ ДЛЯ ПЛАНИРОВАНИЯ:")
            for task_name, task_info in self._combined_handlers['scheduled_tasks'].items():
                router_name = task_info.get('router', 'unknown')
                prompt_parts.append(f"- {task_name}: {task_info['name']} (роутер: {router_name})")
        
        if self._combined_handlers['global_handlers']:
            prompt_parts.append("\nДОСТУПНЫЕ ГЛОБАЛЬНЫЕ ОБРАБОТЧИКИ:")
            for handler_type, handler_info in self._combined_handlers['global_handlers'].items():
                router_name = handler_info.get('router', 'unknown')
                prompt_parts.append(f"- {handler_type}: {handler_info['name']} (роутер: {router_name})")
        
        return "\n".join(prompt_parts)
    
    def get_router_by_name(self, name: str) -> Optional[EventRouter]:
        """Получает роутер событий по имени"""
        for router in self._routers:
            if router.name == name:
                return router
        return None
    
    def get_router_stats(self) -> Dict[str, Any]:
        """Получает статистику по роутерам"""
        stats = {
            "total_routers": len(self._routers),
            "routers": []
        }
        
        for router in self._routers:
            router_stats = {
                "name": router.name,
                "event_handlers": len(router.get_event_handlers()),
                "scheduled_tasks": len(router.get_scheduled_tasks()),
                "global_handlers": len(router.get_global_handlers())
            }
            stats["routers"].append(router_stats)
        
        return stats
    
    def __repr__(self):
        return f"RouterManager(routers={len(self._routers)}, handlers={len(self.get_all_handlers())})"

