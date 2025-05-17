# handlers.py
import logging
# import asyncio # Если нужна задержка
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

import database
import keyboards
from quizzes_data import get_quiz_by_id # get_quiz_by_id теперь возвращает и max_possible_score

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Вспомогательные функции ---
async def register_user_if_not_exists(update: Update):
    """
    Проверяет и регистрирует пользователя в БД, если его там еще нет.
    """
    user = update.effective_user
    if user:
        # Проверка существования пользователя может быть оптимизирована,
        # чтобы не делать SELECT перед каждым INSERT/UPDATE,
        # но для простоты шаблона оставим так. add_or_update_user сама справится с ON CONFLICT.
        database.add_or_update_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        # logger.info(f"Пользователь {user.id} @{user.username} проверен/обновлен.")


# --- Обработчики команд ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await register_user_if_not_exists(update)
    user = update.effective_user
    welcome_message = (
        f"👋 Привет, {user.mention_html(user.first_name)}!\n\n"
        "Я твой бот-помощник. Здесь ты можешь:\n"
        "✅ Проходить тесты и набирать баллы\n"
        "📊 Узнавать свои результаты\n"
        "📄 Получать полезную информацию\n\n"
        "Выбери действие из меню ниже:"
    )
    reply_markup = keyboards.main_menu_keyboard()
    # Сохраняем сообщение для возможного последующего редактирования
    sent_message = await update.message.reply_html(text=welcome_message, reply_markup=reply_markup)
    context.user_data['main_menu_message_id'] = sent_message.message_id


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "🤖 **Справка по боту**\n\n"
        "Вот список доступных команд:\n"
        "/start - Перезапустить бота и показать главное меню.\n"
        "/help - Показать это справочное сообщение.\n"
        "/menu - Показать главное меню.\n"
        "/info - Получить общую информацию.\n"
        "/quiz - Начать новый тест (выбрать из списка).\n\n"
        "Вы также можете использовать кнопки в меню для навигации."
    )
    await update.message.reply_markdown(help_text)


async def _send_or_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup: InlineKeyboardMarkup):
    """Вспомогательная функция для отправки или редактирования сообщения с меню."""
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='HTML')
        except Exception as e: # Если сообщение не изменилось или другая ошибка
            logger.warning(f"Не удалось отредактировать сообщение для меню: {e}. Отправляю новое.")
            # Если редактирование не удалось (например, сообщение слишком старое или не изменилось),
            # отправляем новое сообщение.
            if update.effective_message:
                 sent_message = await update.effective_message.reply_html(text=text, reply_markup=reply_markup)
                 context.user_data['main_menu_message_id'] = sent_message.message_id
            elif update.effective_chat: # если нет effective_message, но есть чат (например, от /команды)
                 sent_message = await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup, parse_mode='HTML')
                 context.user_data['main_menu_message_id'] = sent_message.message_id

    elif update.message: # Если это команда
        sent_message = await update.message.reply_html(text=text, reply_markup=reply_markup)
        context.user_data['main_menu_message_id'] = sent_message.message_id


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await register_user_if_not_exists(update)
    menu_text = "📋 <b>Главное меню:</b>"
    reply_markup = keyboards.main_menu_keyboard()
    await _send_or_edit_menu(update, context, menu_text, reply_markup)


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await register_user_if_not_exists(update)
    current_time_str = context.application.bot_data.get('start_time', 'недоступно') # Используем application.bot_data
    info_text = (
        "💡 <b>Информация</b>\n\n"
        "Этот бот создан как шаблон для демонстрации различных функций:\n"
        "- Приветственные сообщения\n"
        "- Меню с кнопками (inline keyboards)\n"
        "- Тесты с системой баллов за каждый ответ\n"
        "- Хранение данных пользователей в PostgreSQL\n\n"
        "Разработчик: Ваш OpenAI ассистент.\n"
        f"Бот запущен: {current_time_str}\n"
    )
    reply_markup = keyboards.back_to_main_menu_keyboard()
    await _send_or_edit_menu(update, context, info_text, reply_markup)


# --- Обработчики для тестов ---
async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ Команда /quiz """
    await register_user_if_not_exists(update)
    text = "📚 <b>Выберите тест, который хотите пройти:</b>"
    reply_markup = keyboards.select_quiz_keyboard()
    await _send_or_edit_menu(update, context, text, reply_markup)

async def select_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ Показывает список доступных тестов для выбора. """
    query = update.callback_query
    await query.answer()
    text = "📚 <b>Выберите тест, который хотите пройти:</b>"
    reply_markup = keyboards.select_quiz_keyboard()
    await _send_or_edit_menu(update, context, text, reply_markup)


async def start_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ Начинает выбранный тест. """
    query = update.callback_query
    await query.answer()
    quiz_id = query.data.split('_')[-1]

    quiz_data = get_quiz_by_id(quiz_id) # уже содержит max_possible_score
    if not quiz_data:
        error_text = "Ошибка: Тест не найден."
        await _send_or_edit_menu(update, context, error_text, keyboards.back_to_main_menu_keyboard())
        return

    context.user_data['current_quiz_id'] = quiz_id
    context.user_data['current_question_index'] = 0
    context.user_data['current_quiz_score'] = 0
    # Сохраняем максимальный балл для теста в user_data для отображения в конце
    context.user_data['current_quiz_max_score'] = quiz_data['max_possible_score']

    await send_quiz_question(update, context, edit_message=True)


async def send_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE, edit_message: bool = True) -> None:
    """ Отправляет текущий вопрос теста пользователю. """
    quiz_id = context.user_data.get('current_quiz_id')
    question_index = context.user_data.get('current_question_index', 0)

    quiz_data = get_quiz_by_id(quiz_id) # Получаем данные теста, включая вопросы и max_possible_score
    if not quiz_data or question_index >= len(quiz_data["questions"]):
        # Эта ситуация должна быть обработана в quiz_answer_callback (завершение теста)
        logger.error(f"Ошибка в send_quiz_question: Неверный quiz_id ({quiz_id}) или question_index ({question_index})")
        error_text="Произошла внутренняя ошибка с тестом. Пожалуйста, вернитесь в меню."
        await _send_or_edit_menu(update,context, error_text, keyboards.back_to_main_menu_keyboard())
        return

    question = quiz_data["questions"][question_index]
    question_text = (
        f"❓ <b>Вопрос {question_index + 1}/{len(quiz_data['questions'])} ({quiz_data['name']})</b>\n\n"
        f"{question['text']}\n\n"
        f"<i>Текущий балл: {context.user_data.get('current_quiz_score',0)}</i>"
    )
    reply_markup = keyboards.quiz_question_keyboard(question['options'], question_index, quiz_id)

    if edit_message and update.callback_query:
        await _send_or_edit_menu(update, context, question_text, reply_markup)
    elif update.message: # Крайне редкий случай для этого потока, но для полноты
        await update.message.reply_html(text=question_text, reply_markup=reply_markup)
    elif update.effective_chat: # Если нет сообщения, но есть чат (например, после ответа)
         await context.bot.send_message(chat_id=update.effective_chat.id, text=question_text, reply_markup=reply_markup, parse_mode='HTML')


async def quiz_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ Обрабатывает ответ пользователя на вопрос теста. """
    query = update.callback_query
    await query.answer()

    data_parts = query.data.split('_') # ans_{quiz_id}_{question_index}_{answer_index}
    quiz_id_from_callback = data_parts[1]
    question_index_from_callback = int(data_parts[2])
    selected_option_index = int(data_parts[3])

    current_quiz_id = context.user_data.get('current_quiz_id')
    current_question_index = context.user_data.get('current_question_index')

    if quiz_id_from_callback != current_quiz_id or question_index_from_callback != current_question_index:
        logger.warning(f"Получен ответ на устаревший/некорректный вопрос. User: {update.effective_user.id}, "
                       f"Ожидалось: qid={current_quiz_id} qidx={current_question_index}, "
                       f"Получено: qid={quiz_id_from_callback} qidx={question_index_from_callback}")
        await query.message.reply_text("Похоже, вы ответили на старый вопрос или произошла ошибка. Попробуйте продолжить или начать тест заново.")
        # Не меняем сообщение с вопросом, чтобы пользователь мог сориентироваться
        return

    quiz_data = get_quiz_by_id(current_quiz_id)
    question = quiz_data["questions"][current_question_index]
    selected_option = question["options"][selected_option_index]
    score_for_answer = selected_option.get("score", 0)

    context.user_data['current_quiz_score'] = context.user_data.get('current_quiz_score', 0) + score_for_answer
    feedback_text = f"Вы выбрали: \"{selected_option['text']}\".\n<b>Начислено баллов: +{score_for_answer}</b>\nОбщий балл: {context.user_data['current_quiz_score']}"

    # Отправляем фидбек как новое сообщение, чтобы не затирать вопрос сразу
    # или можно редактировать сообщение с вопросом, добавив фидбек
    await query.message.reply_html(text=feedback_text)
    # await asyncio.sleep(1.5) # Небольшая задержка, чтобы пользователь успел прочитать

    context.user_data['current_question_index'] += 1
    if context.user_data['current_question_index'] < len(quiz_data["questions"]):
        await send_quiz_question(update, context, edit_message=True) # Редактируем предыдущее сообщение с вопросом
    else:
        # Тест завершен
        user_id = update.effective_user.id
        achieved_score = context.user_data['current_quiz_score']
        max_possible_score_for_quiz = context.user_data.get('current_quiz_max_score', quiz_data['max_possible_score']) # Берем сохраненный или из quiz_data
        quiz_name = quiz_data["name"]

        database.save_quiz_result(user_id, quiz_name, achieved_score, max_possible_score_for_quiz)

        result_text = (
            f"🎉 <b>Тест '{quiz_name}' завершен!</b> 🎉\n\n"
            f"Ваш результат: <b>{achieved_score} из {max_possible_score_for_quiz}</b> возможных баллов.\n\n"
        )
        percentage = (achieved_score / max_possible_score_for_quiz * 100) if max_possible_score_for_quiz > 0 else 0
        if percentage == 100:
            result_text += "🏆 Великолепно! Максимальный результат!"
        elif percentage >= 75:
            result_text += "👍 Отлично! Вы набрали высокий балл!"
        elif percentage >= 50:
            result_text += "😊 Хороший результат!"
        elif percentage >= 25:
            result_text += "🙂 Неплохо, но есть к чему стремиться."
        else:
            result_text += "Попробуйте еще раз, у вас получится лучше! 💪"

        await _send_or_edit_menu(update, context, result_text, keyboards.back_to_main_menu_keyboard())

        # Очистка состояния теста
        for key in ['current_quiz_id', 'current_question_index', 'current_quiz_score', 'current_quiz_max_score']:
            context.user_data.pop(key, None)


# --- Обработчики кнопок главного меню ---
async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    menu_text = "📋 <b>Главное меню:</b>"
    reply_markup = keyboards.main_menu_keyboard()
    await _send_or_edit_menu(update, context, menu_text, reply_markup)


# --- Обработчик неизвестных команд/сообщений ---
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤷‍♂️ Извините, я не понимаю эту команду. "
        "Пожалуйста, используйте /help для просмотра доступных команд или воспользуйтесь меню."
    )

async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📝 Я получил ваше сообщение. Если вы хотите выполнить команду, "
        "начните ее с символа '/' или воспользуйтесь кнопками меню."
    )


# --- Собираем все обработчики ---
start_handler = CommandHandler('start', start_command)
help_handler = CommandHandler('help', help_command)
menu_handler_cmd = CommandHandler('menu', menu_command)
info_handler_cmd = CommandHandler('info', info_command)
quiz_handler_cmd = CommandHandler('quiz', quiz_command)

callback_query_handlers = [
    CallbackQueryHandler(main_menu_callback, pattern='^main_menu$'),
    CallbackQueryHandler(info_command, pattern='^get_info$'),
    CallbackQueryHandler(select_quiz_callback, pattern='^select_quiz$'),
    CallbackQueryHandler(start_quiz_callback, pattern=r'^start_quiz_'),
    CallbackQueryHandler(quiz_answer_callback, pattern=r'^ans_'),
    # Можно добавить обработчик для 'no_quizzes_available' если нужно специфическое действие
    CallbackQueryHandler(main_menu_callback, pattern='^no_quizzes_available$') # Просто вернет в меню
]

unknown_command_handler = MessageHandler(filters.COMMAND, unknown_command)
unknown_text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text)

ALL_HANDLERS = [
    start_handler,
    help_handler,
    menu_handler_cmd,
    info_handler_cmd,
    quiz_handler_cmd,
    *callback_query_handlers,
    # unknown_command_handler, # Переместим в main.py для корректного порядка
    # unknown_text_handler,
]