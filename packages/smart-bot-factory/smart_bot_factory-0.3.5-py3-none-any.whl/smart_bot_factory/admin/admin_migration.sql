-- ФИНАЛЬНАЯ МИГРАЦИЯ АДМИНСКОЙ СИСТЕМЫ
-- Выполните ПОСЛЕ исправления уникальности telegram_id

-- 1. Расширяем существующие таблицы
ALTER TABLE sales_chat_sessions 
ADD COLUMN IF NOT EXISTS current_stage TEXT,
ADD COLUMN IF NOT EXISTS lead_quality_score INTEGER;

ALTER TABLE sales_messages 
ADD COLUMN IF NOT EXISTS ai_metadata JSONB DEFAULT '{}'::jsonb;

-- 2. Создаем функцию обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. Таблица администраторов
CREATE TABLE IF NOT EXISTS sales_admins (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    role TEXT DEFAULT 'admin',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Диалоги админов с пользователями
CREATE TABLE IF NOT EXISTS admin_user_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id BIGINT REFERENCES sales_admins(telegram_id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES sales_users(telegram_id) ON DELETE CASCADE,
    session_id UUID REFERENCES sales_chat_sessions(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    auto_end_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '30 minutes'
);

-- 5. События из ответов ИИ
CREATE TABLE IF NOT EXISTS session_events (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES sales_chat_sessions(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_info TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notified_admins BIGINT[] DEFAULT '{}'
);

-- 6. Индексы
CREATE INDEX IF NOT EXISTS idx_sales_admins_telegram_id ON sales_admins(telegram_id);
CREATE INDEX IF NOT EXISTS idx_admin_conversations_status ON admin_user_conversations(status);
CREATE INDEX IF NOT EXISTS idx_admin_conversations_admin ON admin_user_conversations(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_conversations_user ON admin_user_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_session_events_type ON session_events(event_type);
CREATE INDEX IF NOT EXISTS idx_session_events_session ON session_events(session_id);
CREATE INDEX IF NOT EXISTS idx_sales_chat_sessions_stage ON sales_chat_sessions(current_stage);
CREATE INDEX IF NOT EXISTS idx_sales_messages_metadata ON sales_messages USING gin(ai_metadata);

-- 7. Триггер для sales_admins
DROP TRIGGER IF EXISTS update_sales_admins_updated_at ON sales_admins;
CREATE TRIGGER update_sales_admins_updated_at 
    BEFORE UPDATE ON sales_admins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 8. Функция завершения просроченных диалогов
CREATE OR REPLACE FUNCTION end_expired_admin_conversations()
RETURNS INTEGER AS $$
DECLARE
    ended_count INTEGER;
BEGIN
    UPDATE admin_user_conversations 
    SET status = 'completed', ended_at = NOW()
    WHERE status = 'active' AND auto_end_at < NOW();
    
    GET DIAGNOSTICS ended_count = ROW_COUNT;
    RETURN ended_count;
END;
$$ LANGUAGE plpgsql;

-- 9. Представления для аналитики
CREATE OR REPLACE VIEW funnel_stats AS
SELECT 
    current_stage,
    COUNT(*) as count,
    AVG(lead_quality_score) as avg_quality,
    ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER(), 0), 1) as percentage
FROM sales_chat_sessions 
WHERE created_at > NOW() - INTERVAL '7 days'
AND current_stage IS NOT NULL
GROUP BY current_stage;

CREATE OR REPLACE VIEW daily_events AS
SELECT 
    DATE(created_at) as event_date,
    event_type,
    COUNT(*) as count
FROM session_events 
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at), event_type
ORDER BY event_date DESC, event_type;

-- 10. RLS политики
ALTER TABLE sales_admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_user_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role can manage all admins" ON sales_admins;
DROP POLICY IF EXISTS "Service role can manage all conversations" ON admin_user_conversations;
DROP POLICY IF EXISTS "Service role can manage all events" ON session_events;

CREATE POLICY "Service role can manage all admins" ON sales_admins
    FOR ALL USING (current_setting('role') = 'service_role');

CREATE POLICY "Service role can manage all conversations" ON admin_user_conversations
    FOR ALL USING (current_setting('role') = 'service_role');

CREATE POLICY "Service role can manage all events" ON session_events
    FOR ALL USING (current_setting('role') = 'service_role');

-- 11. Комментарии
COMMENT ON TABLE sales_admins IS 'Администраторы бота';
COMMENT ON TABLE admin_user_conversations IS 'Активные диалоги админов с пользователями';
COMMENT ON TABLE session_events IS 'События из ответов ИИ для уведомлений';

-- Финальная проверка
SELECT 
    'АДМИНСКАЯ СИСТЕМА СОЗДАНА!' AS status,
    (SELECT COUNT(*) FROM information_schema.tables 
     WHERE table_name IN ('sales_admins', 'admin_user_conversations', 'session_events')) AS tables_created;