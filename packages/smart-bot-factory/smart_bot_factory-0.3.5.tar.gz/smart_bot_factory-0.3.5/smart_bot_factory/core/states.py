"""
Состояния FSM для бота
"""

from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    waiting_for_message = State()
    admin_chat = State()  # пользователь в диалоге с админом
    
    voice_confirmation = State()  # ожидание подтверждения распознанного текста
    voice_editing = State()  # редактирование распознанного текста

class AdminStates(StatesGroup):
    admin_mode = State()
    in_conversation = State()
    
    # Состояния для создания события
    create_event_name = State()
    create_event_date = State()
    create_event_time = State()
    create_event_segment = State()
    create_event_message = State()
    create_event_files = State()
    create_event_confirm = State()

