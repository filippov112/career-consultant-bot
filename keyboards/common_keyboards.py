from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard():
    """
    Создает инлайн-клавиатуру для выбора основного режима работы бота.
    """
    keyboard = [
        [InlineKeyboardButton("💰 Увеличить доход", callback_data="mode_income")],
        [InlineKeyboardButton("🚀 Карьерный рост / Новая работа", callback_data="mode_position")],
        [InlineKeyboardButton("🧭 Профориентация", callback_data="mode_orientation")],
        [InlineKeyboardButton("📊 Оценить мои факторы", callback_data="start_factor_survey")] # <-- Добавляем эту кнопку
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_to_main_menu_keyboard():
    """
    Создает инлайн-клавиатуру с кнопкой "↩️ Назад в главное меню".
    """
    keyboard = [
        [InlineKeyboardButton("↩️ Назад в главное меню", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)