"""
Supabase клиент с автоматической загрузкой настроек из .env файла
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from postgrest.exceptions import APIError

from project_root_finder import root

PROJECT_ROOT = root

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Клиент для работы с Supabase с автоматической загрузкой настроек из .env"""
    
    def __init__(self, bot_id: str):
        """
        Инициализация клиента Supabase с автоматической загрузкой настроек
        
        Args:
            bot_id: Идентификатор бота (обязательно) - код сам найдет все настройки
        """
        self.bot_id = bot_id
        
        # Автоматически загружаем настройки из .env
        self._load_env_config()
        
        # Инициализируем клиент СИНХРОННО прямо в __init__
        self.client = create_client(self.url, self.key)
        
        logger.info(f"✅ SupabaseClient инициализирован для bot_id: {self.bot_id}")
    
    def _load_env_config(self):
        """Загружает конфигурацию из .env файла"""
        try:
            # Автоматический поиск .env файла
            env_path = self._find_env_file()
            
            if not env_path or not env_path.exists():
                raise FileNotFoundError(f".env файл не найден: {env_path}")
            
            # Загружаем переменные окружения
            load_dotenv(env_path)
            
            # Получаем настройки Supabase
            self.url = os.getenv('SUPABASE_URL')
            self.key = os.getenv('SUPABASE_KEY')
            
            if not self.url or not self.key:
                missing_vars = []
                if not self.url:
                    missing_vars.append('SUPABASE_URL')
                if not self.key:
                    missing_vars.append('SUPABASE_KEY')
                raise ValueError(f"Отсутствуют обязательные переменные в .env: {', '.join(missing_vars)}")
            
            logger.info(f"✅ Настройки Supabase загружены из {env_path}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки конфигурации Supabase: {e}")
            raise
    
    def _find_env_file(self) -> Optional[Path]:
        """Автоматически находит .env файл для указанного бота"""
        # Ищем .env файл в папке конкретного бота
        bot_env_path = PROJECT_ROOT / "bots" / self.bot_id / ".env"
        
        if bot_env_path.exists():
            logger.info(f"🔍 Найден .env файл для бота {self.bot_id}: {bot_env_path}")
            return bot_env_path
        
        logger.error(f"❌ .env файл не найден для бота {self.bot_id}")
        logger.error(f"   Искали в: {bot_env_path}")
        return None
    
    # =============================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ
    # =============================================================================
    
    async def create_or_get_user(self, user_data: Dict[str, Any]) -> int:
        """Создает или получает пользователя с учетом bot_id (если указан)"""
        try:
            # Если bot_id указан, фильтруем по нему
            query = self.client.table('sales_users').select('telegram_id').eq(
                'telegram_id', user_data['telegram_id']
            )
            if self.bot_id:
                query = query.eq('bot_id', self.bot_id)
            
            response = query.execute()
            
            if response.data:
                # Обновляем данные существующего пользователя
                update_query = self.client.table('sales_users').update({
                    'username': user_data.get('username'),
                    'first_name': user_data.get('first_name'),
                    'last_name': user_data.get('last_name'),
                    'language_code': user_data.get('language_code'),
                    'updated_at': datetime.now().isoformat(),
                    'is_active': True
                }).eq('telegram_id', user_data['telegram_id'])
                
                if self.bot_id:
                    update_query = update_query.eq('bot_id', self.bot_id)
                
                update_query.execute()
                
                logger.info(f"✅ Обновлен пользователь {user_data['telegram_id']}{f' для bot_id {self.bot_id}' if self.bot_id else ''}")
                return user_data['telegram_id']
            else:
                # Создаем нового пользователя с bot_id (если указан)
                user_insert_data = {
                    'telegram_id': user_data['telegram_id'],
                    'username': user_data.get('username'),
                    'first_name': user_data.get('first_name'),
                    'last_name': user_data.get('last_name'),
                    'language_code': user_data.get('language_code'),
                    'is_active': True,
                    'source': user_data.get('source'),
                    'medium': user_data.get('medium'),
                    'campaign': user_data.get('campaign'),
                    'content': user_data.get('content'),
                    'term': user_data.get('term'),
                }
                if self.bot_id:
                    user_insert_data['bot_id'] = self.bot_id
                
                response = self.client.table('sales_users').insert(user_insert_data).execute()
                
                logger.info(f"✅ Создан новый пользователь {user_data['telegram_id']}{f' для bot_id {self.bot_id}' if self.bot_id else ''}")
                return user_data['telegram_id']
                
        except APIError as e:
            logger.error(f"❌ Ошибка при работе с пользователем: {e}")
            raise
    
    # =============================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С СЕССИЯМИ
    # =============================================================================
    
    async def create_chat_session(self, user_data: Dict[str, Any], system_prompt: str) -> str:
        """Создает новую сессию чата с учетом bot_id (если указан)"""
        try:
            # Создаем или обновляем пользователя
            user_id = await self.create_or_get_user(user_data)
            
            # Завершаем активные сессии пользователя (с учетом bot_id)
            await self.close_active_sessions(user_id)
            
            # Создаем новую сессию с bot_id (если указан)
            session_data = {
                'user_id': user_id,
                'system_prompt': system_prompt,
                'status': 'active',
                'current_stage': 'introduction',
                'lead_quality_score': 5,
                'metadata': {
                    'user_agent': user_data.get('user_agent', ''),
                    'start_timestamp': datetime.now().isoformat()
                }
            }
            if self.bot_id:
                session_data['bot_id'] = self.bot_id
                session_data['metadata']['bot_id'] = self.bot_id
            
            response = self.client.table('sales_chat_sessions').insert(session_data).execute()
            
            session_id = response.data[0]['id']
            
            # Создаем запись аналитики
            await self.create_session_analytics(session_id)
            
            logger.info(f"✅ Создана новая сессия {session_id} для пользователя {user_id}{f', bot_id {self.bot_id}' if self.bot_id else ''}")
            return session_id
            
        except APIError as e:
            logger.error(f"❌ Ошибка при создании сессии: {e}")
            raise
    
    async def close_active_sessions(self, user_id: int):
        """Закрывает активные сессии пользователя с учетом bot_id (если указан)"""
        try:
            # Закрываем только сессии этого бота (если bot_id указан)
            query = self.client.table('sales_chat_sessions').update({
                'status': 'completed',
                'updated_at': datetime.now().isoformat()
            }).eq('user_id', user_id).eq('status', 'active')
            
            if self.bot_id:
                query = query.eq('bot_id', self.bot_id)
            
            query.execute()
            
            logger.info(f"✅ Закрыты активные сессии для пользователя {user_id}{f', bot_id {self.bot_id}' if self.bot_id else ''}")
            
        except APIError as e:
            logger.error(f"❌ Ошибка при закрытии сессий: {e}")
            raise
    
    async def get_active_session(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получает активную сессию пользователя с учетом bot_id (если указан)"""
        try:
            # Ищем активную сессию с учетом bot_id (если указан)
            query = self.client.table('sales_chat_sessions').select(
                'id', 'system_prompt', 'created_at', 'current_stage', 'lead_quality_score'
            ).eq('user_id', telegram_id).eq('status', 'active')
            
            if self.bot_id:
                query = query.eq('bot_id', self.bot_id)
            
            response = query.execute()
            
            if response.data:
                session_info = response.data[0]
                logger.info(f"✅ Найдена активная сессия {session_info['id']} для пользователя {telegram_id}{f', bot_id {self.bot_id}' if self.bot_id else ''}")
                return session_info
            
            return None
            
        except APIError as e:
            logger.error(f"❌ Ошибка при поиске активной сессии: {e}")
            return None
    
    # =============================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С СООБЩЕНИЯМИ
    # =============================================================================
    
    async def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        message_type: str = 'text',
        tokens_used: int = 0,
        processing_time_ms: int = 0,
        metadata: Dict[str, Any] = None,
        ai_metadata: Dict[str, Any] = None
    ) -> int:
        """Добавляет сообщение в базу данных"""
        try:
            response = self.client.table('sales_messages').insert({
                'session_id': session_id,
                'role': role,
                'content': content,
                'message_type': message_type,
                'tokens_used': tokens_used,
                'processing_time_ms': processing_time_ms,
                'metadata': metadata or {},
                'ai_metadata': ai_metadata or {}
            }).execute()
            
            message_id = response.data[0]['id']
            
            # Обновляем аналитику сессии
            await self.update_session_analytics(session_id, tokens_used, processing_time_ms)
            
            logger.debug(f"✅ Добавлено сообщение {message_id} в сессию {session_id}")
            return message_id
            
        except APIError as e:
            logger.error(f"❌ Ошибка при добавлении сообщения: {e}")
            raise
    
    async def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает историю сообщений для сессии"""
        try:
            response = self.client.table('sales_messages').select(
                'id', 'role', 'content', 'message_type', 'created_at', 'metadata', 'ai_metadata'
            ).eq('session_id', session_id).order('created_at', desc=True).limit(limit).execute()
            
            # Фильтруем системные сообщения из истории
            messages = [msg for msg in response.data if msg['role'] != 'system']
            
            # Переворачиваем в хронологический порядок (старые -> новые)
            messages.reverse()
            
            logger.debug(f"✅ Получено {len(messages)} сообщений для сессии {session_id}")
            return messages
            
        except APIError as e:
            logger.error(f"❌ Ошибка при получении истории: {e}")
            raise
    
    # =============================================================================
    # МЕТОДЫ ДЛЯ АНАЛИТИКИ
    # =============================================================================
    
    async def create_session_analytics(self, session_id: str):
        """Создает запись аналитики для сессии"""
        try:
            self.client.table('sales_session_analytics').insert({
                'session_id': session_id,
                'total_messages': 0,
                'total_tokens': 0,
                'average_response_time_ms': 0,
                'conversion_stage': 'initial',
                'lead_quality_score': 5
            }).execute()
            
            logger.debug(f"✅ Создана аналитика для сессии {session_id}")
            
        except APIError as e:
            logger.error(f"❌ Ошибка при создании аналитики: {e}")
            raise
    
    async def update_session_analytics(
        self, 
        session_id: str, 
        tokens_used: int = 0, 
        processing_time_ms: int = 0
    ):
        """Обновляет аналитику сессии"""
        try:
            # Получаем текущую аналитику
            response = self.client.table('sales_session_analytics').select(
                'total_messages', 'total_tokens', 'average_response_time_ms'
            ).eq('session_id', session_id).execute()
            
            if response.data:
                current = response.data[0]
                new_total_messages = current['total_messages'] + 1
                new_total_tokens = current['total_tokens'] + tokens_used
                
                # Вычисляем среднее время ответа
                if processing_time_ms > 0:
                    current_avg = current['average_response_time_ms']
                    new_avg = ((current_avg * (new_total_messages - 1)) + processing_time_ms) / new_total_messages
                else:
                    new_avg = current['average_response_time_ms']
                
                # Обновляем аналитику
                self.client.table('sales_session_analytics').update({
                    'total_messages': new_total_messages,
                    'total_tokens': new_total_tokens,
                    'average_response_time_ms': int(new_avg),
                    'updated_at': datetime.now().isoformat()
                }).eq('session_id', session_id).execute()
                
        except APIError as e:
            logger.error(f"❌ Ошибка при обновлении аналитики: {e}")
            # Не прерываем выполнение, аналитика не критична
    
    async def update_session_stage(self, session_id: str, stage: str = None, quality_score: int = None):
        """Обновляет этап сессии и качество лида"""
        try:
            update_data = {'updated_at': datetime.now().isoformat()}
            
            if stage:
                update_data['current_stage'] = stage
            if quality_score is not None:
                update_data['lead_quality_score'] = quality_score
            
            # Дополнительная проверка bot_id при обновлении (если указан)
            if self.bot_id:
                response = self.client.table('sales_chat_sessions').select('bot_id').eq('id', session_id).execute()
                if response.data and response.data[0].get('bot_id') != self.bot_id:
                    logger.warning(f"⚠️ Попытка обновления сессии {session_id} другого бота")
                    return
                
            self.client.table('sales_chat_sessions').update(update_data).eq(
                'id', session_id
            ).execute()
            
            logger.debug(f"✅ Обновлен этап сессии {session_id}: stage={stage}, quality={quality_score}")
            
        except APIError as e:
            logger.error(f"❌ Ошибка при обновлении этапа сессии: {e}")
            raise
    
    # =============================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С ФАЙЛАМИ
    # =============================================================================
    
    async def get_sent_files(self, user_id: int) -> List[str]:
        """Получает список отправленных файлов для пользователя"""
        try:
            query = self.client.table('sales_users').select('files').eq('telegram_id', user_id)
            
            if self.bot_id:
                query = query.eq('bot_id', self.bot_id)
            
            response = query.execute()
            
            if response.data and response.data[0].get('files'):
                files_str = response.data[0]['files']
                return [f.strip() for f in files_str.split(',') if f.strip()]
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения отправленных файлов для пользователя {user_id}: {e}")
            return []
    
    async def add_sent_files(self, user_id: int, files_list: List[str]):
        """Добавляет файлы в список отправленных для пользователя"""
        try:
            logger.info(f"📁 Добавление файлов для пользователя {user_id}: {files_list}")
            
            # Получаем текущий список
            current_files = await self.get_sent_files(user_id)
            logger.info(f"📁 Текущие файлы в БД: {current_files}")
            
            # Объединяем с новыми файлами (без дубликатов)
            all_files = list(set(current_files + files_list))
            logger.info(f"📁 Объединенный список файлов: {all_files}")
            
            # Сохраняем обратно
            files_str = ', '.join(all_files)
            logger.info(f"📁 Сохраняем строку: {files_str}")
            
            query = self.client.table('sales_users').update({
                'files': files_str
            }).eq('telegram_id', user_id)
            
            if self.bot_id:
                query = query.eq('bot_id', self.bot_id)
                logger.info(f"📁 Фильтр по bot_id: {self.bot_id}")
            
            response = query.execute()
            logger.info(f"📁 Ответ от БД: {response.data}")
            
            logger.info(f"✅ Добавлено {len(files_list)} файлов для пользователя {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления отправленных файлов для пользователя {user_id}: {e}")
            logger.exception("Полный стек ошибки:")
    
    # =============================================================================
    # МЕТОДЫ ДЛЯ АНАЛИТИКИ И СТАТИСТИКИ
    # =============================================================================
    
    async def get_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """Получает сводку аналитики за последние дни с учетом bot_id (если указан)"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Получаем сессии с учетом bot_id (если указан)
            query = self.client.table('sales_chat_sessions').select(
                'id', 'current_stage', 'lead_quality_score', 'created_at'
            ).gte('created_at', cutoff_date.isoformat())
            
            if self.bot_id:
                query = query.eq('bot_id', self.bot_id)
            
            sessions_response = query.execute()
            
            sessions = sessions_response.data
            total_sessions = len(sessions)
            
            # Группировка по этапам
            stages = {}
            quality_scores = []
            
            for session in sessions:
                stage = session.get('current_stage', 'unknown')
                stages[stage] = stages.get(stage, 0) + 1
                
                score = session.get('lead_quality_score', 5)
                if score:
                    quality_scores.append(score)
            
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 5
            
            return {
                'bot_id': self.bot_id,
                'period_days': days,
                'total_sessions': total_sessions,
                'stages': stages,
                'average_lead_quality': round(avg_quality, 1),
                'generated_at': datetime.now().isoformat()
            }
            
        except APIError as e:
            logger.error(f"❌ Ошибка при получении аналитики: {e}")
            return {
                'bot_id': self.bot_id,
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    # =============================================================================
    # МЕТОДЫ СОВМЕСТИМОСТИ
    # =============================================================================
    
    async def update_conversion_stage(self, session_id: str, stage: str, quality_score: int = None):
        """Обновляет этап конверсии и качество лида (для совместимости)"""
        await self.update_session_stage(session_id, stage, quality_score)
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о сессии с проверкой bot_id (если указан)"""
        try:
            response = self.client.table('sales_chat_sessions').select(
                'id', 'user_id', 'bot_id', 'system_prompt', 'status', 'created_at', 
                'metadata', 'current_stage', 'lead_quality_score'
            ).eq('id', session_id).execute()
            
            if response.data:
                session = response.data[0]
                # Дополнительная проверка bot_id для безопасности (если указан)
                if self.bot_id and session.get('bot_id') != self.bot_id:
                    logger.warning(f"⚠️ Попытка доступа к сессии {session_id} другого бота: {session.get('bot_id')} != {self.bot_id}")
                    return None
                return session
            return None
            
        except APIError as e:
            logger.error(f"❌ Ошибка при получении информации о сессии: {e}")
            raise
