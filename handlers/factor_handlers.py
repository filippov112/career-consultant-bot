import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from db.database import get_db
from db import crud
from keyboards.common_keyboards import get_main_menu_keyboard

# Путь к файлам с диалогами
DIALOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dialogs')
FACTOR_DIALOG_PATH = os.path.join(DIALOGS_DIR, 'factor_dialog.json')
COMMON_PHRASES_PATH = os.path.join(DIALOGS_DIR, 'common_phrases.json')

# Состояния для ConversationHandler опроса факторов
(
    ASK_F1_MOTIVATION, ASK_F2_LIFE_EXPERIENCE, ASK_F3_PERSISTENCE,
    ASK_F4_FLEXIBILITY, ASK_F5_EMOTIONAL_INTELLIGENCE, ASK_F6_HEALTH_ENERGY,
    ASK_F7_SELF_PERCEPTION, ASK_F8_ENVIRONMENT_SUPPORT, ASK_F9_RESOURCE_ACCESS,
    ASK_F10_GEOGRAPHICAL_FACTOR,  # F10 будет отдельным шагом, возможно, с выбором региона
    FACTOR_RATING_COMPLETE
) = range(11)  # 10 состояний для 10 факторов

FACTOR_QUESTIONS = [
    {'state': ASK_F1_MOTIVATION, 'factor_name': 'f1_motivation', 'text_key': 'q_f1_motivation'},
    {'state': ASK_F2_LIFE_EXPERIENCE, 'factor_name': 'f2_life_experience', 'text_key': 'q_f2_life_experience'},
    {'state': ASK_F3_PERSISTENCE, 'factor_name': 'f3_persistence', 'text_key': 'q_f3_persistence'},
    {'state': ASK_F4_FLEXIBILITY, 'factor_name': 'f4_flexibility', 'text_key': 'q_f4_flexibility'},
    {'state': ASK_F5_EMOTIONAL_INTELLIGENCE, 'factor_name': 'f5_emotional_intelligence',
     'text_key': 'q_f5_emotional_intelligence'},
    {'state': ASK_F6_HEALTH_ENERGY, 'factor_name': 'f6_health_energy', 'text_key': 'q_f6_health_energy'},
    {'state': ASK_F7_SELF_PERCEPTION, 'factor_name': 'f7_self_perception', 'text_key': 'q_f7_self_perception'},
    {'state': ASK_F8_ENVIRONMENT_SUPPORT, 'factor_name': 'f8_environment_support',
     'text_key': 'q_f8_environment_support'},
    {'state': ASK_F9_RESOURCE_ACCESS, 'factor_name': 'f9_resource_access', 'text_key': 'q_f9_resource_access'},
    # F10 будет обрабатываться отдельно, так как он зависит от региона, а не от прямой оценки
    # {'state': ASK_F10_GEOGRAPHICAL_FACTOR, 'factor_name': 'f10_cultural_economic_environment', 'text_key': 'q_f10_cultural_economic_environment'}
]


def load_dialog_phrases(filepath: str) -> dict:
    """
    Загружает фразы диалога из JSON-файла.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл диалога не найден по пути {filepath}")
        return {}
    except json.JSONDecodeError:
        print(f"Ошибка: Некорректный JSON-формат в файле {filepath}")
        return {}


def get_rating_keyboard():
    keyboard_buttons = [
        [InlineKeyboardButton(str(i), callback_data=f"rating_{i}") for i in range(6)], # 0-5
        [InlineKeyboardButton(str(i), callback_data=f"rating_{i}") for i in range(6, 11)], # 6-10
    ]
    keyboard_buttons.append([InlineKeyboardButton("❌ Отмена опроса", callback_data="cancel_factor_dialog")])
    return InlineKeyboardMarkup(keyboard_buttons)


async def start_factor_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает опрос факторов контекста."""
    query = update.callback_query
    if query:
        await query.answer()
        # Редактируем сообщение, из которого пришел запрос
        message_editor = query.edit_message_text
    else:
        # Если это команда или что-то другое
        message_editor = update.message.reply_text

    dialog_phrases = load_dialog_phrases(FACTOR_DIALOG_PATH)
    await message_editor(
        dialog_phrases.get("factor_survey_intro",
                           "Давай оценим твои личные факторы контекста. Отвечай честно от 0 (никогда/нет) до 10 (всегда/да).") +
        "\n\n" + dialog_phrases.get(FACTOR_QUESTIONS[0]['text_key'], "Нет вопроса."),
        reply_markup=get_rating_keyboard(),
        parse_mode='Markdown'
    )
    context.user_data['current_factor_index'] = 0  # Индекс текущего вопроса
    context.user_data['factors_data'] = {}  # Словарь для сбора ответов
    return FACTOR_QUESTIONS[0]['state']


async def handle_factor_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает оценку фактора и переходит к следующему вопросу."""
    query = update.callback_query
    await query.answer()

    dialog_phrases = load_dialog_phrases(FACTOR_DIALOG_PATH)
    common_phrases = load_dialog_phrases(COMMON_PHRASES_PATH)

    rating = int(query.data.split('_')[1])
    current_index = context.user_data.get('current_factor_index', 0)

    if current_index >= len(FACTOR_QUESTIONS):
        # Этого не должно произойти, если логика корректна
        await query.edit_message_text(
            common_phrases.get("something_went_wrong", "Что-то пошло не так."),
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END

    current_question = FACTOR_QUESTIONS[current_index]
    context.user_data['factors_data'][current_question['factor_name']] = float(rating)

    next_index = current_index + 1
    context.user_data['current_factor_index'] = next_index

    if next_index < len(FACTOR_QUESTIONS):
        # Переходим к следующему вопросу
        next_question = FACTOR_QUESTIONS[next_index]
        await query.edit_message_text(
            dialog_phrases.get(next_question['text_key'], "Нет вопроса."),
            reply_markup=get_rating_keyboard(),
            parse_mode='Markdown'
        )
        return next_question['state']
    else:
        # Все вопросы заданы (кроме F10, который будет отдельной логикой)
        user_telegram_id = update.effective_user.id
        db_gen = get_db()
        db = next(db_gen)
        try:
            # Сохраняем собранные факторы в БД
            # ИСПОЛЬЗУЕМ УЖЕ СУЩЕСТВУЮЩУЮ ФУНКЦИЮ
            user_db_id = crud.get_user_by_telegram_id(db, user_telegram_id).id  # Получаем внутренний ID пользователя
            crud.update_user_context_factors(db, user_db_id, context.user_data['factors_data'])  # <-- ИСПРАВЛЕНО ЗДЕСЬ
            print(f"Факторы пользователя {user_telegram_id} обновлены: {context.user_data['factors_data']}")

            await query.edit_message_text(
                dialog_phrases.get("factor_survey_complete",
                                   "Отлично! Мы собрали информацию о твоих факторах контекста. Теперь рекомендации будут более точными.") +
                "\n\n",  # Просто пустая строка, если далее сразу идет клавиатура главного меню
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            # Очищаем временные данные
            context.user_data.pop('current_factor_index', None)
            context.user_data.pop('factors_data', None)
            return ConversationHandler.END  # Завершаем ConversationHandler
        finally:
            db_gen.close()


async def cancel_factor_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет опрос факторов контекста."""
    query = update.callback_query
    if query:
        await query.answer()
        message_obj = query.message
    else:  # Если отмена произошла через команду /cancel
        message_obj = update.message

    dialog_phrases = load_dialog_phrases(FACTOR_DIALOG_PATH)
    message_text = dialog_phrases.get("factor_survey_cancelled", "Опрос факторов отменен. Возвращаемся в главное меню.")

    # Очищаем временные данные, если они были
    context.user_data.pop('current_factor_index', None)
    context.user_data.pop('factors_data', None)

    await message_obj.reply_text(
        message_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )
    return ConversationHandler.END