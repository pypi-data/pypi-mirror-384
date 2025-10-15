import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

from ..core.bot_utils import parse_ai_response

logger = logging.getLogger(__name__)

class AnalyticsManager:
    """Управление аналитикой и статистикой бота"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    async def get_funnel_stats(self, days: int = 7) -> Dict[str, Any]:
        """Получает статистику воронки продаж"""
        try:
            # Основная статистика
            stats = await self.supabase.get_funnel_stats(days)
            
            # Добавляем новых пользователей
            
            # Добавляем новых пользователей
            cutoff_date = datetime.now() - timedelta(days=days)

            # Запрос на новых пользователей С УЧЕТОМ bot_id
            query = self.supabase.client.table('sales_users').select('id').gte(
                'created_at', cutoff_date.isoformat()
            )
            
            # Фильтруем по bot_id если он указан
            if self.supabase.bot_id:
                query = query.eq('bot_id', self.supabase.bot_id)
                logger.info(f"📊 Фильтр новых пользователей по bot_id: {self.supabase.bot_id}")
            
            # Исключаем тестовых пользователей
            query = query.neq('username', 'test_user')
            
            response = query.execute()

            new_users = len(response.data) if response.data else 0

            logger.info(f"🆕 Новых пользователей за {days} дней: {new_users}")
            
            # Обогащаем статистику
            stats['new_users'] = new_users
            stats['period_days'] = days
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики воронки: {e}")
            return {
                'total_sessions': 0,
                'new_users': 0,
                'stages': {},
                'avg_quality': 0,
                'period_days': days
            }
    
    async def get_events_stats(self, days: int = 7) -> Dict[str, int]:
        """Получает статистику событий"""
        try:
            return await self.supabase.get_events_stats(days)
        except Exception as e:
            logger.error(f"Ошибка получения статистики событий: {e}")
            return {}
    
    async def get_user_journey(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает ВСЕ СООБЩЕНИЯ для активной сессии пользователя"""
        try:
            # 1. Получаем ОДНУ активную сессию
            session_info = await self.supabase.get_active_session(user_id)
            
            if not session_info:
                logger.warning(f"У пользователя {user_id} нет активной сессии")
                return []
            
            session_id = session_info['id']
            logger.info(f"Загружаем ВСЕ сообщения для активной сессии {session_id}")
            
            # 2. Получаем ВСЕ сообщения этой сессии (кроме системных)
            messages_response = self.supabase.client.table('sales_messages').select(
                'role', 'content', 'created_at', 'message_type'
            ).eq('session_id', str(session_id)).neq('role', 'system').order('created_at').execute()
            
            messages = messages_response.data if messages_response.data else []
            logger.info(f"Найдено {len(messages)} сообщений для сессии {session_id}")
            
            # 3. Получаем события для этой сессии
            events_response = self.supabase.client.table('session_events').select(
                'event_type', 'event_info', 'created_at'
            ).eq('session_id', str(session_id)).order('created_at').execute()
            
            events = events_response.data if events_response.data else []
            logger.info(f"Найдено {len(events)} событий для сессии {session_id}")
            
            # 4. Формируем ОДИН объект сессии со ВСЕМИ сообщениями
            session_with_messages = {
                'id': session_id,
                'current_stage': session_info.get('current_stage', 'unknown'),
                'lead_quality_score': session_info.get('lead_quality_score', 0),
                'created_at': session_info['created_at'],
                'status': 'active',
                'messages': messages,  # ВСЕ сообщения сессии
                'events': events
            }
            
            return [session_with_messages]
            
        except Exception as e:
            logger.error(f"Ошибка получения сообщений активной сессии пользователя {user_id}: {e}")
            return []

    def _truncate_message_for_history(self, text: str, max_length: int = 150) -> str:
        """Сокращает сообщения для истории"""
        if not text:
            return ""
        
        # Убираем переносы строк для компактности
        text = text.replace('\n', ' ').strip()
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length-3] + "..."

    def format_funnel_stats(self, stats: Dict[str, Any]) -> str:
        """Форматирует статистику воронки для отображения"""
        if not stats or stats['total_sessions'] == 0:
            return "📊 Нет данных за указанный период"
        
        # Эмодзи для этапов
        stage_emojis = {
            'introduction': '👋',
            'consult': '💬',
            'offer': '💼',
            'contacts': '📱'
        }
        
        # Названия этапов
        stage_names = {
            'introduction': 'Знакомство',
            'consult': 'Консультация', 
            'offer': 'Предложение',
            'contacts': 'Контакты'
        }
        
        lines = [
            f"📊 ВОРОНКА ЗА {stats['period_days']} ДНЕЙ",
            "",
            f"👥 Всего пользователей: {stats.get('total_unique_users', 0)}",
            f"🆕 Новых: {stats.get('new_users', 0)}",
            "",
            "📈 ЭТАПЫ ВОРОНКИ:"
        ]
        
        # Добавляем этапы
        stages = stats.get('stages', {})
        total = stats['total_sessions']
        
        for stage, count in stages.items():
            emoji = stage_emojis.get(stage, '📌')
            name = stage_names.get(stage, stage)
            percentage = (count / total * 100) if total > 0 else 0
            lines.append(f"{emoji} {name}: {count} чел ({percentage:.1f}%)")
        
        # Средняя оценка качества
        avg_quality = stats.get('avg_quality', 0)
        if avg_quality > 0:
            lines.extend([
                "",
                f"⭐ Средний скоринг: {avg_quality:.1f}"
            ])
        
        return "\n".join(lines)
    
    def format_events_stats(self, events: Dict[str, int]) -> str:
        """Форматирует статистику событий для отображения"""
        if not events:
            return "🔥 События: нет данных"
        
        # Эмодзи для событий
        event_emojis = {
            'телефон': '📱',
            'консультация': '💬',
            'покупка': '💰',
            'отказ': '❌'
        }
        
        lines = ["🔥 СОБЫТИЯ:"]
        
        for event_type, count in events.items():
            emoji = event_emojis.get(event_type, '🔔')
            # Экранируем потенциально проблемные символы
            safe_event_type = event_type.replace('_', ' ').title()
            lines.append(f"{emoji} {safe_event_type}: {count}")
        
        return "\n".join(lines)
    
    def format_events_stats(self, events: Dict[str, int]) -> str:
        """Форматирует статистику событий для отображения"""
        if not events:
            return "🔥 События: нет данных"
        
        # Эмодзи для событий
        event_emojis = {
            'телефон': '📱',
            'консультация': '💬',
            'покупка': '💰',
            'отказ': '❌'
        }
        
        lines = ["🔥 СОБЫТИЯ:"]
        
        for event_type, count in events.items():
            emoji = event_emojis.get(event_type, '🔔')
            lines.append(f"{emoji} {event_type.title()}: {count}")
        
        return "\n".join(lines)
    
    def format_user_journey(self, user_id: int, journey: List[Dict[str, Any]]) -> str:
        """Форматирует детальную историю пользователя с сообщениями"""
        if not journey:
            return f"👤 Пользователь {user_id}\nИстория не найдена"
        
        session = journey[0]
        messages = session.get('messages', [])
        events = session.get('events', [])
        
        # Заголовок
        created_at = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00'))
        date_str = created_at.strftime('%d.%m %H:%M')
        stage = session.get('current_stage', 'unknown')
        quality = session.get('lead_quality_score', 0)
        
        lines = [
            f"👤 Пользователь {user_id}",
            f"📅 {date_str} | {stage} | ⭐{quality}",
            f"📊 {len(messages)} сообщений, {len(events)} событий"
        ]
        
        # События в сессии
        if events:
            lines.append("")
            lines.append("🔥 События:")
            for event in events:
                event_time = datetime.fromisoformat(event['created_at'].replace('Z', '+00:00'))
                time_str = event_time.strftime('%H:%M')
                emoji = {'телефон': '📱', 'консультация': '💬', 'покупка': '💰', 'отказ': '❌'}.get(event['event_type'], '🔔')
                lines.append(f"   {emoji} {time_str} {event['event_type']}: {event['event_info']}")
        
        lines.append(f"\n{'━' * 40}")
        lines.append("💬 ДИАЛОГ:")
        
        # Сообщения
        for i, msg in enumerate(messages, 1):
            msg_time = datetime.fromisoformat(msg['created_at'].replace('Z', '+00:00'))
            time_str = msg_time.strftime('%H:%M')
            
            role = "👤 Пользователь" if msg['role'] == 'user' else "🤖 Бот"
            
            # Очищаем JSON из ответов бота
            content = msg['content']
            if msg['role'] == 'assistant' and content.strip().startswith('{'):
                try:
                    clean_content, _ = parse_ai_response(content)
                    content = clean_content if clean_content else content
                except:
                    pass
            
            # Сокращаем длинные сообщения
            if len(content) > 200:
                content = content[:197] + "..."
            
            lines.append(f"\n{i}. {role} в {time_str}:")
            lines.append(f"   {content}")
        
        return "\n".join(lines)
        
    async def get_daily_summary(self) -> str:
        """Получает сводку за сегодня"""
        try:
            today_stats = await self.get_funnel_stats(1)
            today_events = await self.get_events_stats(1)
            
            lines = [
                "📈 СВОДКА ЗА СЕГОДНЯ",
                "",
                f"👥 Новых сессий: {today_stats['total_sessions']}",
                f"🆕 Новых пользователей: {today_stats.get('new_users', 0)}"
            ]
            
            if today_events:
                lines.append("")
                lines.append("🔥 События:")
                for event_type, count in today_events.items():
                    emoji = {'телефон': '📱', 'консультация': '💬', 'покупка': '💰', 'отказ': '❌'}.get(event_type, '🔔')
                    lines.append(f"   {emoji} {event_type}: {count}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Ошибка получения сводки за сегодня: {e}")
            return "❌ Ошибка получения сводки"
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Получает метрики производительности"""
        try:
            # Конверсия по этапам воронки
            stats_7d = await self.get_funnel_stats(7)
            stages = stats_7d.get('stages', {})
            total = stats_7d['total_sessions']
            
            metrics = {
                'total_sessions_7d': total,
                'conversion_rates': {},
                'avg_quality': stats_7d.get('avg_quality', 0)
            }
            
            if total > 0:
                # Рассчитываем конверсии
                intro_count = stages.get('introduction', 0)
                consult_count = stages.get('consult', 0)  
                offer_count = stages.get('offer', 0)
                contacts_count = stages.get('contacts', 0)
                
                metrics['conversion_rates'] = {
                    'intro_to_consult': (consult_count / intro_count * 100) if intro_count > 0 else 0,
                    'consult_to_offer': (offer_count / consult_count * 100) if consult_count > 0 else 0,
                    'offer_to_contacts': (contacts_count / offer_count * 100) if offer_count > 0 else 0,
                    'intro_to_contacts': (contacts_count / intro_count * 100) if intro_count > 0 else 0
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Ошибка получения метрик производительности: {e}")
            return {}
    
    def format_performance_metrics(self, metrics: Dict[str, Any]) -> str:
        """Форматирует метрики производительности"""
        if not metrics:
            return "📊 Метрики недоступны"
        
        lines = [
            "📊 МЕТРИКИ ЭФФЕКТИВНОСТИ",
            "",
            f"👥 Сессий за 7 дней: {metrics.get('total_sessions_7d', 0)}",
            f"⭐ Средняя оценка: {metrics.get('avg_quality', 0):.1f}",
            ""
        ]
        
        conversions = metrics.get('conversion_rates', {})
        if conversions:
            lines.append("🎯 КОНВЕРСИИ:")
            lines.append(f"👋➡️💬 {conversions.get('intro_to_consult', 0):.1f}%")
            lines.append(f"💬➡️💼 {conversions.get('consult_to_offer', 0):.1f}%")
            lines.append(f"💼➡️📱 {conversions.get('offer_to_contacts', 0):.1f}%")
            lines.append(f"👋➡️📱 {conversions.get('intro_to_contacts', 0):.1f}%")
        
        return "\n".join(lines)
    
    async def get_top_performing_hours(self) -> List[int]:
        """Получает часы с наибольшей активностью"""
        try:
            # Запрос на получение активности по часам за последние 7 дней
            cutoff_date = datetime.now() - timedelta(days=7)
            
            response = self.supabase.client.table('sales_messages').select(
                'created_at'
            ).gte('created_at', cutoff_date.isoformat()).eq('role', 'user').execute()
            
            if not response.data:
                return []
            
            # Группируем по часам
            hour_counts = {}
            for message in response.data:
                created_at = datetime.fromisoformat(message['created_at'].replace('Z', '+00:00'))
                hour = created_at.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            # Сортируем по количеству сообщений
            sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Возвращаем топ-5 часов
            return [hour for hour, count in sorted_hours[:5]]
            
        except Exception as e:
            logger.error(f"Ошибка получения топ часов: {e}")
            return []
