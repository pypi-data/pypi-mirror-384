#!/usr/bin/env python3
"""
Генератор UTM-ссылок для Telegram ботов
Создает ссылки в формате: @https://t.me/bot?start=source-vk_campaign-summer2025
"""

def get_user_input():
    """Получает данные от пользователя через консоль"""
    print("🔗 Генератор UTM-ссылок для Telegram")
    print("=" * 50)
    
    # Основные параметры
    bot_username = input("Введите username бота (без @): ").strip()
    if not bot_username:
        print("❌ Username бота обязателен!")
        return None
    
    print("\n📊 Введите UTM-метки (нажмите Enter для пропуска):")
    
    # UTM параметры (соответствуют полям в базе данных)
    utm_source = input("utm_source (источник): ").strip()
    utm_medium = input("utm_medium (канал): ").strip()
    utm_campaign = input("utm_campaign (кампания): ").strip()
    utm_content = input("utm_content (контент): ").strip()
    utm_term = input("utm_term (ключевое слово): ").strip()
    
    print("\n🎯 Сегментация (нажмите Enter для пропуска):")
    segment = input("seg (сегмент): ").strip()
    
    return {
        'bot_username': bot_username,
        'utm_source': utm_source,
        'utm_medium': utm_medium,
        'utm_campaign': utm_campaign,
        'utm_content': utm_content,
        'utm_term': utm_term,
        'segment': segment
    }

def create_utm_string(utm_data):
    """Создает строку UTM параметров в формате source-vk_campaign-summer2025_seg-premium"""
    utm_parts = []
    
    # Маппинг полей базы данных на формат без префикса utm
    field_mapping = {
        'utm_source': 'source',
        'utm_medium': 'medium', 
        'utm_campaign': 'campaign',
        'utm_content': 'content',
        'utm_term': 'term'
    }
    
    for db_field, utm_field in field_mapping.items():
        value = utm_data.get(db_field)
        if value:
            utm_parts.append(f"{utm_field}-{value}")
    
    # Добавляем сегмент, если указан
    segment = utm_data.get('segment')
    if segment:
        utm_parts.append(f"seg-{segment}")
    
    return "_".join(utm_parts)

def generate_telegram_link(bot_username, utm_string):
    """Генерирует полную ссылку на Telegram бота"""
    return f"https://t.me/{bot_username}?start={utm_string}"

def check_size_and_validate(utm_string):
    """Проверяет размер строки после start= и валидирует"""
    MAX_SIZE = 64
    
    if len(utm_string) > MAX_SIZE:
        return False, f"Строка слишком большая: {len(utm_string)} символов (максимум {MAX_SIZE})"
    
    return True, f"Размер OK: {len(utm_string)} символов"


def main():
    """Основная функция"""
    try:
        # Получаем данные от пользователя
        data = get_user_input()
        if not data:
            return
        
        # Создаем UTM строку
        utm_string = create_utm_string(data)
        
        if not utm_string:
            print("❌ Не указано ни одной UTM-метки!")
            return
        
        # Проверяем размер
        is_valid, size_message = check_size_and_validate(utm_string)
        
        print(f"\n📏 {size_message}")
        
        if not is_valid:
            print("❌ Ссылка превышает максимальный размер!")
            print("💡 Сократите значения UTM-меток или уберите менее важные")
            return
        
        # Генерируем и выводим ссылку
        telegram_link = generate_telegram_link(data['bot_username'], utm_string)
        
        print(f"\n✅ Сгенерированная ссылка:")
        print(f"🔗 {telegram_link}")
    except KeyboardInterrupt:
        print("\n\n👋 Отменено пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    main()

