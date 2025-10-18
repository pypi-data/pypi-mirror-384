import logging
from typing import List, Dict, Set
from aiogram.types import User

logger = logging.getLogger(__name__)

class AdminManager:
    """Управление администраторами бота"""
    
    def __init__(self, config, supabase_client):
        self.config = config
        self.supabase = supabase_client
        self.admin_ids: Set[int] = set(config.ADMIN_TELEGRAM_IDS)
        self.admin_modes: Dict[int, bool] = {}  # admin_id -> is_in_admin_mode
        
        logger.info(f"Инициализирован менеджер админов: {len(self.admin_ids)} админов")
    
    async def sync_admins_from_config(self):
        """Синхронизирует админов из конфига с базой данных"""
        if not self.admin_ids:
            logger.warning("Нет админов в конфигурации")
            return
        
        try:
            for admin_id in self.admin_ids:
                await self.supabase.sync_admin({
                    'telegram_id': admin_id,
                    'username': None,  # будет обновлено при первом сообщении
                    'first_name': None,
                    'last_name': None
                })
                
                # Устанавливаем режим администратора по умолчанию
                if admin_id not in self.admin_modes:
                    self.admin_modes[admin_id] = True
            
            logger.info(f"Синхронизированы админы: {self.admin_ids}")
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации админов: {e}")
            raise
    
    async def update_admin_info(self, user: User):
        """Обновляет информацию об админе"""
        if not self.is_admin(user.id):
            return
        
        try:
            await self.supabase.sync_admin({
                'telegram_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            })
            
        except Exception as e:
            logger.error(f"Ошибка обновления информации админа {user.id}: {e}")
    
    def is_admin(self, telegram_id: int) -> bool:
        """Проверяет, является ли пользователь админом"""
        return telegram_id in self.admin_ids
    
    def is_in_admin_mode(self, telegram_id: int) -> bool:
        """Проверяет, находится ли админ в режиме администратора"""
        if not self.is_admin(telegram_id):
            return False
        return self.admin_modes.get(telegram_id, True)
    
    def toggle_admin_mode(self, telegram_id: int) -> bool:
        """Переключает режим админа. Возвращает новое состояние"""
        if not self.is_admin(telegram_id):
            return False
        
        current_mode = self.admin_modes.get(telegram_id, True)
        new_mode = not current_mode
        self.admin_modes[telegram_id] = new_mode
        
        logger.info(f"Админ {telegram_id} переключен в режим: {'администратор' if new_mode else 'пользователь'}")
        return new_mode
    
    def set_admin_mode(self, telegram_id: int, is_admin_mode: bool):
        """Устанавливает режим админа"""
        if not self.is_admin(telegram_id):
            return
        
        self.admin_modes[telegram_id] = is_admin_mode
        logger.info(f"Режим админа {telegram_id} установлен: {'администратор' if is_admin_mode else 'пользователь'}")
    
    async def get_active_admins(self) -> List[int]:
        """Возвращает список активных админов в режиме администратора"""
        return [admin_id for admin_id in self.admin_ids if self.is_in_admin_mode(admin_id)]
    
    def get_admin_mode_text(self, telegram_id: int) -> str:
        """Возвращает текстовое описание режима админа"""
        if not self.is_admin(telegram_id):
            return "Не администратор"
        
        if self.is_in_admin_mode(telegram_id):
            return "👑 Режим администратора"
        else:
            return "👤 Режим пользователя"
    
    def format_admin_status(self, telegram_id: int) -> str:
        """Форматирует статус админа для отображения"""
        if not self.is_admin(telegram_id):
            return ""
        
        mode = "👑 АДМИН" if self.is_in_admin_mode(telegram_id) else "👤 ПОЛЬЗ"
        return f"[{mode}]"
    
    async def notify_admins(self, message: str, exclude_admin: int = None):
        """Отправляет уведомление всем активным админам"""
        from main import bot  # Импорт здесь чтобы избежать циклических импортов
        
        active_admins = await self.get_active_admins()
        
        if exclude_admin:
            active_admins = [aid for aid in active_admins if aid != exclude_admin]
        
        sent_count = 0
        for admin_id in active_admins:
            try:
                await bot.send_message(admin_id, message, parse_mode='Markdown')
                sent_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления админу {admin_id}: {e}")
        
        logger.info(f"Уведомление отправлено {sent_count} админам")
        return sent_count
    
    def get_stats(self) -> Dict[str, any]:
        """Возвращает статистику по админам"""
        total_admins = len(self.admin_ids)
        active_admins = len([aid for aid in self.admin_ids if self.is_in_admin_mode(aid)])
        
        return {
            'total_admins': total_admins,
            'active_admins': active_admins,
            'admin_ids': list(self.admin_ids),
            'modes': dict(self.admin_modes)
        }