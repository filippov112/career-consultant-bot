import os
import json

import telegram
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters,
)

from db_manager import DBManager  # Убедись, что этот импорт правильный

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
FACTORS_JSON_PATH = os.getenv("FACTORS_JSON_PATH")
INCOME_METHODS_JSON_PATH = os.getenv("INCOME_METHODS_JSON_PATH")

db_manager = DBManager()

ASKING_FACTORS = 0
SHOWING_RECOMMENDATIONS = 1  # Новое состояние для отображения рекомендаций

USER_PREFERENCE_SCORES = {
    "Очень важно": 5,
    "Важно": 4,
    "Не особо важно": 3,
    "Скорее не важно": 2,
    "Всё равно": 1,
}

SURVEY_BUTTONS = [
    [InlineKeyboardButton("Очень важно", callback_data="score_5")],
    [InlineKeyboardButton("Важно", callback_data="score_4")],
    [InlineKeyboardButton("Не особо важно", callback_data="score_3")],
    [InlineKeyboardButton("Скорее не важно", callback_data="score_2")],
    [InlineKeyboardButton("Всё равно", callback_data="score_1")],
]

START_SURVEY_BUTTON = [
    [InlineKeyboardButton("Начать тест", callback_data="start_survey_btn")]
]

# Константа для эмодзи звезд
STAR_EMOJI = "⭐️"
EMPTY_STAR_EMOJI = "▪️" # Можно использовать другую эмодзи или просто пробел
MAX_SCORE_STARS = 10 # Максимальное количество звезд для нашей шкалы от 1 до 10


def score_to_stars(score: int) -> str:
    """Преобразует числовую оценку (1-10) в строку эмодзи звезд."""
    filled_stars = int(score)
    empty_stars = MAX_SCORE_STARS - filled_stars
    return STAR_EMOJI * filled_stars + EMPTY_STAR_EMOJI * empty_stars


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    db_manager.add_user_if_not_exists(user.id)

    reply_markup = InlineKeyboardMarkup(START_SURVEY_BUTTON) # Добавляем кнопку

    await update.message.reply_html(
        f"Привет, {user.mention_html()}! Я Карьерный консультант. "
        "Я помогу тебе выбрать способы увеличения дохода, исходя из твоих предпочтений. "
        "Чтобы начать тест, нажмите кнопку ниже."
    )
    # Отдельное сообщение для кнопки, чтобы оно не редактировалось при перезапуске
    await update.effective_chat.send_message(
        "Готовы приступить к тесту?",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help."""
    await update.message.reply_text("Нажмите кнопку 'Начать тест' или используйте команду /survey (если настроена) для прохождения опроса.")


# Обработчик для кнопки "Начать тест"
async def handle_start_survey_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    # Удаляем сообщение с кнопкой "Начать тест".
    # Важно: если это последнее сообщение в чате, Telegram может его не удалить,
    # но это не критично для дальнейшей логики.
    try:
        await query.message.delete()
    except Exception as e:
        # Логируем ошибку, но не останавливаем выполнение, так как сообщение могло быть уже удалено
        # или бот не имеет прав на удаление старых сообщений.
        print(f"Не удалось удалить сообщение с кнопкой 'Начать тест': {e}")

    # Важно: При старте опроса всегда отправляем новое сообщение.
    # Поэтому очищаем user_data["survey_message_id"], чтобы ask_next_factor не пытался редактировать.
    if "survey_message_id" in context.user_data:
        del context.user_data["survey_message_id"]

    # Теперь вызываем start_survey, которая запустит ask_next_factor
    return await start_survey(update, context)


async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает опрос пользователя."""
    user_id = update.effective_user.id
    db_manager.add_user_if_not_exists(user_id)

    factors = db_manager.get_all_factors()
    if not factors:
        await update.effective_chat.send_message("Извините, не могу загрузить факторы для опроса. Попробуйте позже.")
        return ConversationHandler.END

    context.user_data["factors"] = factors
    context.user_data["current_factor_index"] = 0
    context.user_data["user_preferences_temp"] = {}

    # НОВОЕ: Очищаем message_id для опроса, чтобы первый вопрос всегда отправлялся как новое сообщение
    if "survey_message_id" in context.user_data:
        del context.user_data["survey_message_id"]

    return await ask_next_factor(update, context)


async def ask_next_factor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Задает следующий вопрос из списка факторов."""
    factors = context.user_data["factors"]
    current_index = context.user_data["current_factor_index"]

    if current_index < len(factors):
        factor_id, factor_name, question_text = factors[current_index]

        keyboard = InlineKeyboardMarkup(SURVEY_BUTTONS)

        question_number = current_index + 1
        total_questions = len(factors)

        text = f"**Вопрос {question_number}/{total_questions}**\n\n{question_text}"

        # ИСПРАВЛЕНИЕ ЛОГИКИ РЕДАКТИРОВАНИЯ/ОТПРАВКИ:
        # Проверяем, есть ли уже ID сообщения опроса в user_data.
        # Если есть, пытаемся его отредактировать. Иначе отправляем новое.
        if "survey_message_id" in context.user_data:
            try:
                # Если сообщение отправлено от бота, используем context.bot.edit_message_text
                # Если оно было результатом callback_query (что здесь не так),
                # нужно использовать update.callback_query.message.edit_text.
                # Но для вопросов мы всегда отправляем первое сообщение, а затем редактируем его.
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=context.user_data["survey_message_id"],
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            except Exception as e:
                # Если редактирование не удалось (например, сообщение удалено), отправляем новое
                print(f"Ошибка редактирования сообщения опроса: {e}")
                new_message = await update.effective_chat.send_message(text, reply_markup=keyboard,
                                                                       parse_mode="Markdown")
                context.user_data["survey_message_id"] = new_message.message_id
        else:
            # Отправляем первое сообщение опроса
            new_message = await update.effective_chat.send_message(text, reply_markup=keyboard, parse_mode="Markdown")
            context.user_data["survey_message_id"] = new_message.message_id

        return ASKING_FACTORS
    else:
        # Если опрос завершен, удаляем сообщение с последним вопросом,
        # так как finish_survey отправит новое сообщение с рекомендациями
        if "survey_message_id" in context.user_data:
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=context.user_data["survey_message_id"]
                )
                del context.user_data["survey_message_id"]
            except Exception as e:
                print(f"Не удалось удалить сообщение с последним вопросом: {e}")

        return await finish_survey(update, context)


async def receive_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    score_str = query.data.replace("score_", "")
    user_score = int(score_str)

    factors = context.user_data["factors"]
    current_index = context.user_data["current_factor_index"]
    factor_id, factor_name, _ = factors[current_index]

    user_id = query.from_user.id

    db_manager.save_user_preference(user_id, factor_id, user_score)
    context.user_data["user_preferences_temp"][factor_id] = user_score

    context.user_data["current_factor_index"] += 1

    return await ask_next_factor(update, context)


async def finish_survey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Завершает опрос и подводит итоги, выводит рекомендации."""
    # Если мы пришли сюда через CallbackQuery (последний ответ на вопрос),
    # сообщение уже отредактировано ask_next_factor, поэтому не нужно редактировать
    # сообщение снова, а просто отправить новое сообщение с рекомендациями.

    # Удаляем сообщение с деталями, если оно есть, перед выводом новых рекомендаций
    if "details_message_id" in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data["details_message_id"]
            )
            del context.user_data["details_message_id"]
        except Exception as e:
            print(f"Не удалось удалить старое сообщение с деталями перед выводом рекомендаций: {e}")

    user_id = update.effective_user.id
    user_preferences = db_manager.get_user_preferences(user_id)

    if not user_preferences:
        await update.effective_chat.send_message("Не удалось получить ваши предпочтения. Пожалуйста, пройдите опрос снова.")
        return ConversationHandler.END

    all_methods = db_manager.get_all_methods_with_factors()

    if not all_methods:
        await update.effective_chat.send_message("Не удалось загрузить способы увеличения дохода. Попробуйте позже.")
        return ConversationHandler.END

    all_db_factors = db_manager.get_all_factors()
    factor_name_to_id = {name: fid for fid, name, _ in all_db_factors}

    scored_methods = []
    for method in all_methods:
        total_score = 0
        for factor_name, method_factor_score in method['factors'].items():
            factor_id = factor_name_to_id.get(factor_name)
            if factor_id and factor_id in user_preferences:
                user_preference_score = user_preferences[factor_id]
                total_score += method_factor_score * user_preference_score
        scored_methods.append({'method': method, 'total_score': total_score})

    scored_methods.sort(key=lambda x: x['total_score'], reverse=True)
    top_5_recommendations = scored_methods[:5]

    if top_5_recommendations:
        recommendation_text = "Вот 5 наиболее подходящих для вас способов увеличения дохода. Нажмите на название, чтобы узнать подробности:\n\n"
        keyboard_buttons = []
        for i, item in enumerate(top_5_recommendations):
            method = item['method']
            keyboard_buttons.append([InlineKeyboardButton(method['name'], callback_data=f"show_method_{method['id']}")])

        # НОВОЕ: Добавляем кнопку "Начать заново"
        keyboard_buttons.append([InlineKeyboardButton("Начать заново", callback_data="start_new_survey")])

        reply_markup = InlineKeyboardMarkup(keyboard_buttons)

        await update.effective_chat.send_message(
            recommendation_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return SHOWING_RECOMMENDATIONS
    else:
        await update.effective_chat.send_message("Не удалось найти подходящие рекомендации.")
        return ConversationHandler.END


# НОВАЯ ФУНКЦИЯ: Обработчик для кнопки "Начать заново"
async def start_new_survey_from_recommendations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Удаляем сообщение с рекомендациями, чтобы начать заново с чистого листа
    try:
        await query.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение с рекомендациями: {e}")

    # Также удаляем сообщение с деталями, если оно было открыто
    if "details_message_id" in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=query.message.chat_id,
                message_id=context.user_data["details_message_id"]
            )
            del context.user_data["details_message_id"]
        except Exception as e:
            print(f"Не удалось удалить старое сообщение с деталями: {e}")

    # Перезапускаем опрос
    return await start_survey(update, context)


async def show_method_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    method_id = int(query.data.replace("show_method_", ""))
    method_details = db_manager.get_method_details(method_id)

    if not method_details:
        await query.message.reply_text("Извините, не удалось найти информацию об этом способе.")
        return SHOWING_RECOMMENDATIONS

    message_text = (
        f"**{method_details['name']}**\n\n"
        f"{method_details['description']}\n\n"
        "**Характеристики:**\n"
    )

    all_factors_ordered = db_manager.get_all_factors()
    method_factor_scores_dict = method_details['factors']

    for factor_id, factor_name, _ in all_factors_ordered:
        score = method_factor_scores_dict.get(factor_name)
        if score is not None:
            stars = score_to_stars(score)
            message_text += f"- {factor_name}: {stars}\n"

    message_text += "\nВы можете выбрать другой способ из списка выше или начать новый опрос: /survey"

    # Кнопки для сообщения с деталями
    details_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Закрыть", callback_data="close_details")]
    ])

    # Логика редактирования/отправки сообщения с деталями
    if "details_message_id" in context.user_data:
        # Пытаемся отредактировать существующее сообщение
        try:
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=context.user_data["details_message_id"],
                text=message_text,
                parse_mode="Markdown",
                reply_markup=details_markup
            )
        except telegram.error.BadRequest as e:
            # Обрабатываем BadRequest
            if "Message is not modified" in str(e):
                # Если сообщение не изменилось, просто игнорируем, ничего не делаем.
                # Это и есть случай повторного нажатия на ту же кнопку.
                print(f"DEBUG: Message not modified: {e}")
                pass  # Сообщение уже соответствует желаемому, нет необходимости отправлять новое.
            elif "Message to edit not found" in str(e):
                # Если сообщение не найдено (удалено, истекло и т.д.), отправляем новое.
                print(f"WARNING: Message to edit not found, sending new message: {e}")
                new_message = await query.message.reply_text(message_text, parse_mode="Markdown",
                                                             reply_markup=details_markup)
                context.user_data["details_message_id"] = new_message.message_id
            else:
                # Другие BadRequest ошибки
                print(f"ERROR: Other BadRequest on editing message: {e}")
                new_message = await query.message.reply_text(message_text, parse_mode="Markdown",
                                                             reply_markup=details_markup)
                context.user_data["details_message_id"] = new_message.message_id
        except Exception as e:
            # Другие непредвиденные ошибки
            print(f"ERROR: Unexpected error on editing message: {e}")
            new_message = await query.message.reply_text(message_text, parse_mode="Markdown",
                                                         reply_markup=details_markup)
            context.user_data["details_message_id"] = new_message.message_id
    else:
        # Если message_id нет (первое открытие деталей), отправляем новое сообщение
        new_message = await query.message.reply_text(message_text, parse_mode="Markdown", reply_markup=details_markup)
        context.user_data["details_message_id"] = new_message.message_id

    return SHOWING_RECOMMENDATIONS


async def close_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if "details_message_id" in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=query.message.chat_id,
                message_id=context.user_data["details_message_id"]
            )
            del context.user_data["details_message_id"]
        except Exception as e:
            print(f"Ошибка удаления сообщения деталей: {e}")
            await query.message.reply_text("Не удалось закрыть окно с подробностями. Просто проигнорируйте его.")
    # При закрытии деталей мы хотим снова показать список рекомендаций,
    # поэтому не завершаем разговор, а остаемся в состоянии SHOWING_RECOMMENDATIONS.
    # Если список рекомендаций не виден (например, прокрутился вверх),
    # можно добавить команду, которая его переотправит.
    return SHOWING_RECOMMENDATIONS


async def cancel_survey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Опрос отменен. Вы можете начать его снова командой /survey.")
    return ConversationHandler.END


def main() -> None:
    db_manager.initialize_db_schema("init_db.sql")
    data_dir = os.path.dirname(FACTORS_JSON_PATH)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    db_manager.load_factors_from_json(FACTORS_JSON_PATH)
    db_manager.load_income_methods_from_json(INCOME_METHODS_JSON_PATH)
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("survey", start_survey),
            CallbackQueryHandler(handle_start_survey_button, pattern="^start_survey_btn$")
        ],
        states={
            ASKING_FACTORS: [CallbackQueryHandler(receive_preference, pattern="^score_")],
            SHOWING_RECOMMENDATIONS: [
                CallbackQueryHandler(show_method_details, pattern="^show_method_"),
                CallbackQueryHandler(close_details, pattern="^close_details$"),
                # НОВОЕ: Добавляем обработчик для кнопки "Начать заново"
                CallbackQueryHandler(start_new_survey_from_recommendations, pattern="^start_new_survey$")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_survey),
            CommandHandler("survey", start_survey),
            MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: u.message.reply_text(
                "Пожалуйста, используйте кнопки для ответа или команду /cancel для отмены."))
        ],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)

    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

    db_manager.close()

if __name__ == "__main__":
    main()