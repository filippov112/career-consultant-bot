# keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from quizzes_data import get_all_quizzes_info # get_all_quizzes_info теперь возвращает и max_score

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для главного меню.
    """
    keyboard = [
        [InlineKeyboardButton("📚 Пройти тест", callback_data='select_quiz')],
        [InlineKeyboardButton("ℹ️ Получить информацию", callback_data='get_info')],
        # [InlineKeyboardButton("🏆 Мои результаты", callback_data='my_results')], # Можно добавить
    ]
    return InlineKeyboardMarkup(keyboard)

def select_quiz_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора теста.
    Теперь также может отображать максимальный балл за тест.
    """
    quizzes = get_all_quizzes_info()
    keyboard = []
    for quiz_info in quizzes:
        button_text = f"{quiz_info['name']} (макс. {quiz_info['max_score']} баллов)"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'start_quiz_{quiz_info["id"]}')])

    if not keyboard:
        keyboard.append([InlineKeyboardButton("Нет доступных тестов", callback_data='no_quizzes_available')])

    keyboard.append([InlineKeyboardButton("⬅️ Назад в меню", callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)


def quiz_question_keyboard(options: list, question_index: int, quiz_id: str) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с вариантами ответов для вопроса теста.
    'options' теперь список словарей: [{'text': '...', 'score': X}, ...]

    :param options: Список словарей с вариантами ответов и их баллами.
    :param question_index: Индекс текущего вопроса (начиная с 0).
    :param quiz_id: Идентификатор текущего теста.
    :return: InlineKeyboardMarkup.
    """
    keyboard = []
    for i, option_data in enumerate(options):
        option_text = option_data.get("text", f"Вариант {i+1}")
        # Баллы не показываем на кнопке, чтобы не подсказывать, если не задумано
        # Если нужно показывать баллы: option_text = f"{option_data.get('text')} ({option_data.get('score', 0)}б)"
        callback_data = f'ans_{quiz_id}_{question_index}_{i}'
        keyboard.append([InlineKeyboardButton(option_text, callback_data=callback_data)])
    return InlineKeyboardMarkup(keyboard)

def back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопкой "Назад в меню".
    """
    keyboard = [[InlineKeyboardButton("⬅️ Назад в меню", callback_data='main_menu')]]
    return InlineKeyboardMarkup(keyboard)