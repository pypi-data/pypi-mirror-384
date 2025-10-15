# Исправленный conversation_manager.py после обновления из GitHub - фикс расчета времени до автозавершения

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from aiogram.types import Message, User
from aiogram.fsm.context import FSMContext

from .bot_utils import get_global_var

logger = logging.getLogger(__name__)

class ConversationManager:
    """Управление диалогами между админами и пользователями"""
    
    def __init__(self, supabase_client, admin_manager, parse_mode, admin_session_timeout_minutes):
        self.supabase = supabase_client
        self.admin_manager = admin_manager
        self.parse_mode = parse_mode
        self.admin_session_timeout_minutes = admin_session_timeout_minutes
        
    async def start_admin_conversation(self, admin_id: int, user_id: int) -> bool:
        """Начинает диалог админа с пользователем"""
        try:
            from ..utils.debug_routing import debug_admin_conversation_creation
            await debug_admin_conversation_creation(admin_id, user_id)
            
            # Проверяем, что это действительно админ
            if not self.admin_manager.is_admin(admin_id):
                logger.warning(f"Попытка начать диалог не-админом {admin_id}")
                return False
            
            # Получаем активную сессию пользователя
            session_info = await self.supabase.get_active_session(user_id)
            if not session_info:
                logger.warning(f"У пользователя {user_id} нет активной сессии")
                return False
            
            session_id = session_info['id']
            logger.info(f"✅ Найдена активная сессия: {session_id}")
            
            # Создаем запись о диалоге в БД
            logger.info(f"🔧 Создаем запись о диалоге в БД...")
            conversation_id = await self.supabase.start_admin_conversation(
                admin_id, user_id, session_id
            )
            logger.info(f"✅ Диалог создан с ID: {conversation_id}")
            
            # Показываем последние 5 сообщений
            await self._show_recent_messages(admin_id, user_id, session_id)
            
            logger.info(f"🎉 Диалог успешно начат: админ {admin_id} -> пользователь {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка начала диалога админа {admin_id} с пользователем {user_id}: {e}")
            logger.exception("Полный стек ошибки:")
            return False

    async def _show_recent_messages(self, admin_id: int, user_id: int, session_id: str):
        """Показывает последние сообщения пользователя"""
        from .message_sender import send_message_by_human
        
        try:
            # Получаем последние 5 сообщений (сортируем по убыванию и берем первые 5)
            response = self.supabase.client.table('sales_messages').select(
                'role', 'content', 'created_at'
            ).eq('session_id', session_id).order('created_at', desc=True).limit(5).execute()
            
            recent_messages = response.data if response.data else []
            
            if not recent_messages:
                await send_message_by_human(admin_id, "📭 Нет сообщений в текущей сессии")
                return
                
            # Получаем красивое имя пользователя
            user_display = await self.get_user_display_name(user_id)
            
            header = f"📜 Последние сообщения с {user_display}\n{'━' * 40}"
            await send_message_by_human(admin_id, header)
            
            # Разворачиваем чтобы показать в хронологическом порядке (старые -> новые)
            for msg in reversed(recent_messages):
                role_emoji = "👤" if msg['role'] == 'user' else "🤖"
                timestamp = datetime.fromisoformat(msg['created_at'].replace('Z', '+00:00'))
                time_str = timestamp.strftime('%H:%M')
                
                # Сокращаем длинные сообщения
                content = self._truncate_message(msg['content'])
                
                message_text = f"{role_emoji} {time_str} | {content}"
                
                await send_message_by_human(admin_id, message_text)
                
            # Разделитель
            await send_message_by_human(admin_id, f"{'━' * 40}\n💬 Диалог начат. Ваши сообщения будут переданы пользователю.")
            
        except Exception as e:
            logger.error(f"Ошибка показа последних сообщений: {e}")

    async def get_user_display_name(self, user_id: int) -> str:
        """Получает красивое отображение пользователя с username"""
        try:
            response = self.supabase.client.table('sales_users').select(
                'first_name', 'last_name', 'username'
            ).eq('telegram_id', user_id).execute()
            
            if response.data:
                user_info = response.data[0]
                name_parts = []
                if user_info.get('first_name'):
                    name_parts.append(user_info['first_name'])
                if user_info.get('last_name'):
                    name_parts.append(user_info['last_name'])
                
                name = " ".join(name_parts) if name_parts else ""
                
                if user_info.get('username'):
                    if name:
                        return f"{name} (@{user_info['username']})"
                    else:
                        return f"@{user_info['username']}"
                elif name:
                    return name
                else:
                    return f"ID {user_id}"
            else:
                return f"ID {user_id}"
                
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе {user_id}: {e}")
            return f"ID {user_id}"

    def _truncate_message(self, text: str, max_lines: int = 6) -> str:
        """Сокращает длинные сообщения"""
        if not text:
            return ""
            
        lines = text.split('\n')
        
        if len(lines) <= max_lines:
            return text
        
        # Берем первые 3 и последние 3 строки
        first_lines = lines[:3]
        last_lines = lines[-3:]
        
        truncated = '\n'.join(first_lines) + '\n...\n' + '\n'.join(last_lines)
        return truncated
    
    async def end_admin_conversation(self, admin_id: int) -> bool:
        """Завершает текущий диалог админа"""
        try:
            await self.supabase.end_admin_conversations(admin_id)
            logger.info(f"Завершен диалог админа {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка завершения диалога админа {admin_id}: {e}")
            return False
            
    async def is_user_in_admin_chat(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Проверяет, ведется ли диалог с пользователем"""
        try:
            logger.debug(f"🔍 Проверяем диалог с пользователем {user_id}")
            
            conversation = await self.supabase.get_user_admin_conversation(user_id)
            
            if conversation:
                logger.debug(f"✅ Найден активный диалог: админ {conversation['admin_id']}, ID: {conversation['id']}")
            else:
                logger.debug(f"❌ Активный диалог не найден для пользователя {user_id}")
                
            return conversation
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки диалога пользователя {user_id}: {e}")
            return None
                            
    async def get_admin_active_conversation(self, admin_id: int) -> Optional[Dict[str, Any]]:
        """Получает активный диалог админа"""
        try:
            return await self.supabase.get_admin_active_conversation(admin_id)
            
        except Exception as e:
            logger.error(f"Ошибка получения активного диалога админа {admin_id}: {e}")
            return None

    async def forward_message_to_admin(self, message: Message, conversation: Dict[str, Any]):
        """Пересылает сообщение пользователя админу"""
        from .message_sender import send_message_by_human
        
        admin_id = conversation['admin_id']
        user_id = message.from_user.id
        
        logger.info(f"📤 Пересылаем сообщение от {user_id} админу {admin_id}")
        
        # Форматируем сообщение для админа
        user_info = self._format_user_info(message.from_user)
        
        # Время с начала диалога
        try:
            start_time = datetime.fromisoformat(conversation['started_at'].replace('Z', '+00:00'))
            duration = datetime.now(start_time.tzinfo) - start_time
            minutes = int(duration.total_seconds() / 60)
        except Exception as e:
            logger.error(f"Ошибка расчета времени диалога: {e}")
            minutes = 0
        
        # ✅ ИСПРАВЛЕНИЕ: Убираем символы, которые могут вызвать ошибки парсинга
        safe_user_info = self._escape_markdown(user_info)
        safe_message_text = self._escape_markdown(message.text or "")
        
        header = f"👤 {safe_user_info} | ⏱️ {minutes} мин"
        separator = "━" * 20
        
        full_message = f"{header}\n{separator}\n{safe_message_text}"
        
        try:
            logger.info(f"📨 Отправляем сообщение админу {admin_id}")
            
            # ✅ ИСПРАВЛЕНИЕ: Убираем parse_mode='Markdown' чтобы избежать ошибок парсинга
            await send_message_by_human(admin_id, full_message)
            
            logger.info(f"✅ Сообщение успешно отправлено админу {admin_id}")
            
            # Добавляем кнопки управления
            await self._send_admin_controls(admin_id, user_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка пересылки сообщения админу {admin_id}: {e}")
            
            # ✅ ДОБАВЛЯЕМ: Fallback отправка без форматирования
            try:
                simple_message = f"Сообщение от пользователя {user_id}:\n{message.text}"
                await send_message_by_human(admin_id, simple_message)
                logger.info(f"✅ Простое сообщение отправлено админу {admin_id}")
            except Exception as e2:
                logger.error(f"❌ Даже простое сообщение не отправилось: {e2}")
                raise

    def _escape_markdown(self, text: str) -> str:
        """Экранирует специальные символы Markdown"""
        if not text:
            return ""
        
        # Символы, которые нужно экранировать в Markdown
        markdown_chars = ['*', '_', '`', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        escaped_text = text
        for char in markdown_chars:
            escaped_text = escaped_text.replace(char, f'\\{char}')
        
        return escaped_text
            
    async def forward_message_to_user(self, message: Message, conversation: Dict[str, Any]):
        """Пересылает сообщение админа пользователю"""
        from .message_sender import send_message_by_human
        supabase_client = get_global_var('supabase_client')
        
        user_id = conversation['user_id']
        
        try:
            # Отправляем сообщение как от бота
            parse_mode = self.parse_mode if self.parse_mode != 'None' else None
            await send_message_by_human(user_id, message.text, parse_mode=parse_mode)
            
            # Сохраняем в БД как сообщение ассистента
            session_info = await supabase_client.get_active_session(user_id)
            if session_info:
                await supabase_client.add_message(
                    session_id=session_info['id'],
                    role='assistant',
                    content=message.text,
                    message_type='text',
                    metadata={'from_admin': message.from_user.id}
                )
            
        except Exception as e:
            logger.error(f"Ошибка пересылки сообщения пользователю {user_id}: {e}")
    
    async def _send_admin_controls(self, admin_id: int, user_id: int):
        """Отправляет кнопки управления диалогом"""
        from .message_sender import send_message_by_human
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 История", callback_data=f"admin_history_{user_id}"),
                InlineKeyboardButton(text="✅ Завершить", callback_data=f"admin_end_{user_id}")
            ]
        ])
        
        try:
            await send_message_by_human(
                admin_id,
                "🎛️ Управление диалогом:",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Ошибка отправки кнопок управления: {e}")
    
    def _format_user_info(self, user: User) -> str:
        """Форматирует информацию о пользователе"""
        name_parts = []
        if user.first_name:
            name_parts.append(user.first_name)
        if user.last_name:
            name_parts.append(user.last_name)
        
        name = " ".join(name_parts) if name_parts else "Без имени"
        
        if user.username:
            return f"{name} (@{user.username})"
        else:
            return f"{name} (ID: {user.id})"
    
    async def cleanup_expired_conversations(self):
        """Очищает просроченные диалоги"""
        try:
            ended_count = await self.supabase.end_expired_conversations()
            if ended_count > 0:
                logger.info(f"Очищено {ended_count} просроченных диалогов")
            return ended_count
            
        except Exception as e:
            logger.error(f"Ошибка очистки просроченных диалогов: {e}")
            return 0
    
    async def get_conversation_stats(self) -> Dict[str, int]:
        """Возвращает статистику диалогов"""
        try:
            # Здесь можно добавить запросы к БД для получения статистики
            # Пока возвращаем заглушку
            return {
                'active_conversations': 0,
                'completed_today': 0,
                'total_admin_messages': 0
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики диалогов: {e}")
            return {}

    async def get_active_conversations(self) -> List[Dict[str, Any]]:
        """Получает все активные диалоги админов"""
        try:
            logger.info(f"🔍 Ищем активные диалоги админов...")
            
            # Получаем все активные диалоги
            response = self.supabase.client.table('admin_user_conversations').select(
                'id', 'admin_id', 'user_id', 'started_at', 'auto_end_at'
            ).eq('status', 'active').order('started_at', desc=True).execute()
            
            logger.info(f"📊 Найдено {len(response.data)} активных диалогов в БД")
            
            conversations = []
            for conv in response.data:
                # Получаем информацию о пользователе
                try:
                    user_response = self.supabase.client.table('sales_users').select(
                        'first_name', 'last_name', 'username'
                    ).eq('telegram_id', conv['user_id']).execute()
                    
                    user_info = user_response.data[0] if user_response.data else {}
                except Exception as e:
                    logger.error(f"Ошибка получения данных пользователя {conv['user_id']}: {e}")
                    user_info = {}
                
                # Получаем информацию об админе
                try:
                    admin_response = self.supabase.client.table('sales_admins').select(
                        'first_name', 'last_name', 'username'
                    ).eq('telegram_id', conv['admin_id']).execute()
                    
                    admin_info = admin_response.data[0] if admin_response.data else {}
                except Exception as e:
                    logger.error(f"Ошибка получения данных админа {conv['admin_id']}: {e}")
                    admin_info = {}
                
                conv['user_info'] = user_info
                conv['admin_info'] = admin_info
                conversations.append(conv)
            
            logger.info(f"✅ Получено {len(conversations)} активных диалогов с дополнительной информацией")
            return conversations
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения активных диалогов: {e}")
            return []

    def format_active_conversations(self, conversations: List[Dict[str, Any]]) -> str:
        """Форматирует список активных диалогов - ИСПРАВЛЕН РАСЧЕТ ВРЕМЕНИ АВТОЗАВЕРШЕНИЯ"""
        if not conversations:
            return "💬 Нет активных диалогов"
        
        lines = ["💬 АКТИВНЫЕ ДИАЛОГИ:", ""]
        
        for i, conv in enumerate(conversations, 1):
            # Информация о пользователе
            user_info = conv.get('user_info', {})
            user_name = []
            if user_info.get('first_name'):
                user_name.append(user_info['first_name'])
            if user_info.get('last_name'):
                user_name.append(user_info['last_name'])
            
            user_display = " ".join(user_name) if user_name else f"ID {conv['user_id']}"
            if user_info.get('username'):
                user_display += f" (@{user_info['username']})"
            
            # Информация об админе
            admin_info = conv.get('admin_info', {})
            admin_name = []
            if admin_info.get('first_name'):
                admin_name.append(admin_info['first_name'])
            if admin_info.get('last_name'):
                admin_name.append(admin_info['last_name'])
            
            admin_display = " ".join(admin_name) if admin_name else f"ID {conv['admin_id']}"
            
            # 🔧 ИСПРАВЛЕНИЕ: Правильный расчет времени с учетом timezone
            try:
                started_at_str = conv['started_at']
                logger.debug(f"🕐 Диалог {i}: started_at = '{started_at_str}'")
                
                # Парсим время начала с правильной обработкой timezone
                if started_at_str.endswith('Z'):
                    start_time = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
                elif '+' in started_at_str or started_at_str.count(':') >= 3:
                    # Уже есть timezone info
                    start_time = datetime.fromisoformat(started_at_str)
                else:
                    # Если нет timezone info, считаем что это UTC
                    naive_time = datetime.fromisoformat(started_at_str)
                    start_time = naive_time.replace(tzinfo=timezone.utc)
                
                logger.debug(f"✅ Парсед start_time: {start_time}")
                
                # Получаем текущее время в UTC
                now_utc = datetime.now(timezone.utc)
                logger.debug(f"🕐 now_utc: {now_utc}")
                
                # Приводим start_time к UTC если нужно
                if start_time.tzinfo != timezone.utc:
                    start_time_utc = start_time.astimezone(timezone.utc)
                else:
                    start_time_utc = start_time
                
                # Длительность диалога
                duration = now_utc - start_time_utc
                minutes = max(0, int(duration.total_seconds() / 60))
                logger.debug(f"⏱️ Длительность: {minutes} минут")
                
            except Exception as e:
                logger.error(f"❌ Ошибка расчета времени диалога {i}: {e}")
                logger.error(f"   started_at_str: '{started_at_str}'")
                minutes = 0
            
            # 🔧 ИСПРАВЛЕНИЕ: Время до автозавершения с правильной обработкой timezone
            try:
                auto_end_str = conv['auto_end_at']
                logger.debug(f"🕐 Диалог {i}: auto_end_at = '{auto_end_str}'")
                
                # Парсим время автозавершения с правильной обработкой timezone
                if auto_end_str.endswith('Z'):
                    auto_end = datetime.fromisoformat(auto_end_str.replace('Z', '+00:00'))
                elif '+' in auto_end_str or auto_end_str.count(':') >= 3:
                    # Уже есть timezone info
                    auto_end = datetime.fromisoformat(auto_end_str)
                else:
                    # Если нет timezone info, считаем что это UTC
                    naive_time = datetime.fromisoformat(auto_end_str)
                    auto_end = naive_time.replace(tzinfo=timezone.utc)
                
                logger.debug(f"✅ Парсед auto_end: {auto_end}")
                
                # Получаем текущее время в UTC
                now_utc = datetime.now(timezone.utc)
                logger.debug(f"🕐 now_utc для auto_end: {now_utc}")
                
                # Приводим auto_end к UTC если нужно
                if auto_end.tzinfo != timezone.utc:
                    auto_end_utc = auto_end.astimezone(timezone.utc)
                else:
                    auto_end_utc = auto_end
                
                # Оставшееся время
                remaining = auto_end_utc - now_utc
                remaining_minutes = max(0, int(remaining.total_seconds() / 60))
                logger.debug(f"⏰ Remaining: {remaining_minutes} минут")
                
                # 🔧 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: вычисляем планируемую длительность
                if start_time.tzinfo != timezone.utc:
                    start_time_utc = start_time.astimezone(timezone.utc) 
                else:
                    start_time_utc = start_time
                    
                planned_duration = auto_end_utc - start_time_utc
                planned_minutes = int(planned_duration.total_seconds() / 60)
                logger.debug(f"📏 Планируемая длительность: {planned_minutes} минут")
                
                # Проверяем корректность
                expected_timeout = self.admin_session_timeout_minutes
                
                logger.debug(f"🕐 expected_timeout: {expected_timeout}")
                
                if abs(planned_minutes - expected_timeout) > 2:  # допускаем погрешность в 2 минуты
                    logger.warning(f"⚠️ Диалог {i}: планируемая длительность {planned_minutes} мин не соответствует конфигу {expected_timeout} мин")
                
            except Exception as e:
                logger.error(f"❌ Ошибка расчета времени автозавершения диалога {i}: {e}")
                logger.error(f"   auto_end_str: '{auto_end_str}'")
                remaining_minutes = 0
            
            lines.append(f"{i}. 👤 {user_display}")
            lines.append(f"   👑 Админ: {admin_display}")
            lines.append(f"   ⏱️ Длительность: {minutes} мин")
            lines.append(f"   ⏰ Автозавершение через: {remaining_minutes} мин")
            lines.append(f"   🎛️ /чат {conv['user_id']}")
            lines.append("")
        
        return "\n".join(lines)

    async def route_admin_message(self, message: Message, state: FSMContext) -> bool:
        """
        Маршрутизирует сообщение админа
        Возвращает True если сообщение обработано как админское
        """
        admin_id = message.from_user.id
        
        # Проверяем админские команды
        if message.text and message.text.startswith('/'):
            return False  # Команды обрабатываются отдельно
        
        # Проверяем, ведется ли диалог с пользователем
        conversation = await self.get_admin_active_conversation(admin_id)
        
        if conversation:
            # Пересылаем сообщение пользователю
            await self.forward_message_to_user(message, conversation)
            return True
        
        return False