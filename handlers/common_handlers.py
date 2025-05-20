import json
import os
from telegram import Update
from telegram.ext import ContextTypes
from db.database import get_db
from db import crud
from keyboards.common_keyboards import get_main_menu_keyboard, get_back_to_main_menu_keyboard # Добавили get_back_to_main_menu_keyboard

# Путь к файлам с диалогами
DIALOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dialogs')
INTRO_DIALOG_PATH = os.path.join(DIALOGS_DIR, 'intro_dialog.json')
COMMON_PHRASES_PATH = os.path.join(DIALOGS_DIR, 'common_phrases.json') # Добавили путь к common_phrases.json

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает команду /start.
    Представляет бота и предлагает выбрать режим работы.
    Создает или находит пользователя в базе данных.
    """
    user_telegram_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name

    dialog_phrases = load_dialog_phrases(INTRO_DIALOG_PATH)
    start_message = dialog_phrases.get("start_message", "Привет! Я Карьерный консультант.")
    welcome_back_message = dialog_phrases.get("welcome_back_message", "Снова привет! Рад тебя видеть.")

    db_gen = get_db()
    db = next(db_gen)
    try:
        user = crud.get_user_by_telegram_id(db, user_telegram_id)

        if user:
            message_text = welcome_back_message
        else:
            user = crud.create_user(db, telegram_id=user_telegram_id,
                                    username=username,
                                    first_name=first_name,
                                    last_name=last_name)
            print(f"Новый пользователь добавлен в БД: {user}")
            message_text = start_message

        await update.message.reply_text(
            message_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    finally:
        db_gen.close()

# ... (импорты)

async def handle_main_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает выбор режима работы из главного меню.
    """
    query = update.callback_query
    await query.answer()

    chosen_mode = query.data.replace("mode_", "")
    common_phrases = load_dialog_phrases(COMMON_PHRASES_PATH)

    print(f"DEBUG (common_handler): Выбран режим: {chosen_mode} из callback_data: {query.data}") # <-- ДОБАВИТЬ ЭТУ СТРОКУ

    response_text = ""
    reply_markup = None

    if chosen_mode == "income":
        response_text = common_phrases.get("mode_income_selected", "Вы выбрали режим 'Увеличить доход'. Отличный выбор! Я помогу тебе найти новые источники дохода или оптимизировать текущие.")
        # Здесь мы не будем переходить в ConversationHandler напрямую из этого обработчика,
        # так как ConversationHandler сам перехватит callback_data='mode_income'
        # Но если вы хотите здесь запустить что-то, это другое дело.
        # Для текущей структуры, ConversationHandler сработает как entry_point.
    elif chosen_mode == "position":
        response_text = common_phrases.get("mode_position_selected", "Вы выбрали режим 'Карьерный рост / Новая работа'. Поехали! Мы разработаем план для твоего профессионального развития.")
    elif chosen_mode == "orientation":
        response_text = common_phrases.get("mode_orientation_selected", "Вы выбрали режим 'Профориентация'. Замечательно! Вместе мы определим профессию, которая максимально соответствует твоим способностям и интересам.")
    else:
        response_text = common_phrases.get("unknown_mode_selected", "Произошла ошибка при выборе режима. Пожалуйста, попробуйте еще раз.")
        reply_markup = get_main_menu_keyboard()
        print(
            f"ERROR (common_handler): Неизвестный режим: {chosen_mode} из callback_data: {query.data}")  # <-- ДОБАВИТЬ ЭТУ СТРОКУ

    # Важно: если выбран режим "income", мы НЕ должны выводить это сообщение,
    # так как ConversationHandler сам отправит сообщение из start_income_dialog.
    # Если мы все еще в `handle_main_menu_choice`, это означает, что ConversationHandler
    # НЕ перехватил `mode_income`.
    if chosen_mode != "income": # Только если режим не "income", продолжаем обрабатывать здесь
         await query.edit_message_text(
            text=response_text,
            reply_markup=get_back_to_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    else:
        print("DEBUG: Режим 'income' выбран. Ожидаем, что ConversationHandler перехватит.")
        # Здесь нет необходимости отправлять сообщение, ConversationHandler сделает это.
        # Если вы все еще видите старое сообщение, значит ConversationHandler не сработал.


async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает нажатие кнопки "Назад в главное меню" и возвращает к выбору основного режима.
    """
    query = update.callback_query
    await query.answer()

    common_phrases = load_dialog_phrases(COMMON_PHRASES_PATH)
    message_text = common_phrases.get("back_to_main_menu_message", "Вы вернулись в главное меню. Что будем делать дальше?")

    await query.edit_message_text(
        text=message_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )