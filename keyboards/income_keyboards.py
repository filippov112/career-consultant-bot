from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_cancel_keyboard():
    """
    Создает инлайн-клавиатуру с кнопкой "Отмена" для отмены текущего диалога.
    """
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_income_dialog")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_income_analysis_keyboard():
    """
    Создает инлайн-клавиатуру после ввода дохода, предлагая перейти к анализу.
    (Пока заглушка, будет расширено).
    """
    keyboard = [
        [InlineKeyboardButton("📊 Перейти к анализу", callback_data="start_income_analysis")],
        [InlineKeyboardButton("↩️ Назад в главное меню", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_recommended_methods_keyboard(recommended_methods: list[tuple]):
    """
    Создает инлайн-клавиатуру для рекомендованных способов дохода,
    с кнопками "Подробнее" для каждого и кнопкой "Назад в главное меню".
    """
    keyboard = []
    for i, (method, score) in enumerate(recommended_methods):
        # Добавляем кнопку "Подробнее" для каждого метода
        keyboard.append([InlineKeyboardButton(f"{method.name} (Балл: {score:.1f}) 📚",
                                              callback_data=f"income_method_details_{method.id}")])

    keyboard.append([InlineKeyboardButton("↩️ Назад в главное меню", callback_data="back_to_main_menu")])

    return InlineKeyboardMarkup(keyboard)