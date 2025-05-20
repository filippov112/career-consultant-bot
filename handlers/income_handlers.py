import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from db.database import get_db
from db import crud
from keyboards.income_keyboards import get_cancel_keyboard, get_income_analysis_keyboard, \
    get_recommended_methods_keyboard
from keyboards.common_keyboards import get_main_menu_keyboard
from utils.calc_success import get_recommended_income_methods  # Импортируем новую функцию

# Путь к файлу с диалогами
DIALOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dialogs')
INCOME_DIALOG_PATH = os.path.join(DIALOGS_DIR, 'income_dialog.json')
COMMON_PHRASES_PATH = os.path.join(DIALOGS_DIR, 'common_phrases.json')

# Определение состояний для ConversationHandler
GET_INCOME_AMOUNT = 1


async def show_recommended_methods(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Показывает список рекомендованных способов дохода без повторного запроса дохода.
    Используется после просмотра деталей способа или как отдельная точка входа.
    """
    query = update.callback_query
    if query:
        await query.answer()
        message_editor = query.edit_message_text  # Для редактирования текущего сообщения
        message_obj = query.message
        print(
            f"DEBUG (income_handlers): Вызвана show_recommended_methods из callback_data: {query.data}")  # <-- ДОБАВИТЬ ЭТУ СТРОКУ
    else:
        # Если вызывается не из callback_query (например, из ConversationHandler)
        message_editor = update.message.reply_text
        message_obj = update.message
        print(
            f"DEBUG (income_handlers): Вызвана show_recommended_methods не из callback_data.")  # <-- ДОБАВИТЬ ЭТУ СТРОКУ

    dialog_phrases = load_dialog_phrases(INCOME_DIALOG_PATH)
    common_phrases = load_dialog_phrases(COMMON_PHRASES_PATH)

    user_telegram_id = update.effective_user.id
    db_gen = get_db()
    db = next(db_gen)
    try:
        user = crud.get_user_by_telegram_id(db, user_telegram_id)
        if not user or user.current_income is None:
            # Если дохода нет, просим его ввести
            await message_editor(
                dialog_phrases.get("start_income", "Для начала, пожалуйста, укажи свой текущий ежемесячный доход."),
                reply_markup=get_cancel_keyboard(),
                parse_mode='Markdown'
            )
            # Возвращаем в состояние GET_INCOME_AMOUNT, если это возможно в контексте ConversationHandler
            # Но если вызывается напрямую, просто выводим сообщение.
            return  # Не возвращаем состояние, т.к. это не часть ConversationHandler

        # Если доход есть, получаем рекомендации
        await message_obj.reply_text(  # Отдельное сообщение для "обрабатываю"
            dialog_phrases.get("income_processing", "Обрабатываю информацию о доходе и формирую рекомендации...")
        )

        recommended_methods = get_recommended_income_methods(db, user_telegram_id, top_n=3)

        if recommended_methods:
            response_parts = ["Отлично! Вот несколько способов увеличить твой доход, которые могут тебе подойти:\n\n"]
            final_message_text = "".join(response_parts) + "\n\n_Нажми на название способа, чтобы узнать подробнее._"

            await message_editor(  # Редактируем сообщение с "обрабатываю" на список
                final_message_text,
                reply_markup=get_recommended_methods_keyboard(recommended_methods),
                parse_mode='Markdown'
            )
        else:
            await message_editor(
                "К сожалению, пока не удалось найти подходящие способы дохода. Попробуйте позднее или свяжитесь с нами.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
    finally:
        db_gen.close()


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


async def start_income_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ... (код без изменений)
    print("DEBUG: Вызвана start_income_dialog")
    query = update.callback_query
    await query.answer()

    dialog_phrases = load_dialog_phrases(INCOME_DIALOG_PATH)
    message_text = dialog_phrases.get("start_income", "Пожалуйста, укажи свой текущий доход.")

    if query.message:
        await query.edit_message_text(
            text=message_text,
            reply_markup=get_cancel_keyboard(),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=get_cancel_keyboard(),
            parse_mode='Markdown'
        )

    print(f"DEBUG: start_income_dialog возвращает состояние: {GET_INCOME_AMOUNT}")
    return GET_INCOME_AMOUNT


async def handle_income_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает введенный пользователем текущий доход, сохраняет его и предлагает способы.
    """
    print(f"DEBUG: Вызвана handle_income_input. Ввод: {update.message.text}")
    user_input = update.message.text
    dialog_phrases = load_dialog_phrases(INCOME_DIALOG_PATH)
    common_phrases = load_dialog_phrases(COMMON_PHRASES_PATH)

    try:
        income_amount = int(user_input)
        if income_amount < 0:
            raise ValueError

        user_telegram_id = update.effective_user.id
        db_gen = get_db()
        db = next(db_gen)
        try:
            crud.update_user_income(db, user_telegram_id, income_amount)
            context.user_data['current_income'] = income_amount
            print(f"Пользователь {user_telegram_id} ввел и сохранил доход: {income_amount}")

            await update.message.reply_text(
                dialog_phrases.get("income_saved", "Твой доход сохранен."),
                parse_mode='Markdown'
            )

            # Вместо прямого отображения рекомендаций, вызываем новую функцию
            await show_recommended_methods(update, context)  # <-- ВЫЗЫВАЕМ НОВУЮ ФУНКЦИЮ

            return ConversationHandler.END  # Завершаем ConversationHandler по вводу дохода

        finally:
            db_gen.close()

    except ValueError:
        await update.message.reply_text(
            dialog_phrases.get("invalid_income_input", "Пожалуйста, введи число."),
            reply_markup=get_cancel_keyboard(),
            parse_mode='Markdown'
        )
        return GET_INCOME_AMOUNT


async def cancel_income_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ... (код без изменений)
    print("DEBUG: Вызвана cancel_income_dialog")
    query = update.callback_query
    if query:
        await query.answer()
        message_obj = query.message
    else:
        message_obj = update.message

    dialog_phrases = load_dialog_phrases(INCOME_DIALOG_PATH)
    message_text = dialog_phrases.get("income_dialog_cancelled", "Диалог отменен.")

    await message_obj.reply_text(
        message_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )
    return ConversationHandler.END


async def show_income_method_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Показывает детальную информацию о выбранном способе увеличения дохода.
    """
    query = update.callback_query
    await query.answer()

    # Извлекаем ID метода из callback_data (например, "income_method_details_123")
    method_id_str = query.data.replace("income_method_details_", "")
    try:
        method_id = int(method_id_str)
    except ValueError:
        await query.edit_message_text("Ошибка: Неверный ID способа.", reply_markup=get_main_menu_keyboard())
        return

    db_gen = get_db()
    db = next(db_gen)
    try:
        method = crud.get_income_method(db, method_id) # Предполагается, что crud.get_income_method существует
        if not method:
            await query.edit_message_text("Способ не найден.", reply_markup=get_main_menu_keyboard())
            return

        # Формируем детальное сообщение о способе
        details_text = (
            f"*{method.name}*\n\n"
            f"_{method.detailed_description}_\n\n"
            f"**Критерии:**\n"
            f"💰 Потенциал дохода: {method.income_potential}/10\n"
            f"⚡️ Скорость результата: {method.speed_of_result}/10\n"
            f"💸 Финансовые вложения: {method.financial_investment}/10\n"
            f"💪 Сложность: {method.difficulty}/10\n"
            f"⚠️ Риски: {method.risks}/10\n"
            f"🧘‍♀️ Психологический комфорт: {method.psychological_comfort}/10\n"
            f"🗺️ География: {method.geography}/10\n"
            f"📚 Hard Skills: {method.hard_skills}/10\n"
            f"🤝 Soft Skills: {method.soft_skills}/10\n"
            f"🧠 Специальные знания: {method.special_knowledge}/10\n"
            f"💼 Влияние на текущую работу: {method.impact_on_current_job}/10\n"  # <-- ДОБАВЛЕНО
            f"⏳ Вовлеченность: {method.engagement}/10\n"
            f"⏰ Гибкий график: {method.flexible_schedule}/10\n"
            # Можно добавить F11 и F12, если хотим их показать
            # f"Комплексность (F11): {method.f11_complexity:.2f}\n"
            # f"Необходимое время (F12): {method.f12_needed_time:.2f}\n"
        )

        # Добавим кнопки для дальнейших действий, например, вернуться к списку или в главное меню
        keyboard = [
            [InlineKeyboardButton("↩️ К списку способов", callback_data="mode_income_recalculate")], # Позволит заново получить список
            [InlineKeyboardButton("↩️ Назад в главное меню", callback_data="back_to_main_menu")]
        ]

        await query.edit_message_text(
            text=details_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    finally:
        db_gen.close()