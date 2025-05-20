import asyncio
import platform
import nest_asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, \
    ConversationHandler  # Добавляем MessageHandler, filters
from config.settings import settings
from handlers.common_handlers import start, handle_main_menu_choice, back_to_main_menu
from db.initial_data_loader import initialize_all_data
from handlers.income_handlers import start_income_dialog, handle_income_input, cancel_income_dialog, show_income_method_details, GET_INCOME_AMOUNT, show_recommended_methods
from handlers.factor_handlers import (
    start_factor_dialog, handle_factor_rating, cancel_factor_dialog,
    ASK_F1_MOTIVATION, ASK_F2_LIFE_EXPERIENCE, ASK_F3_PERSISTENCE,
    ASK_F4_FLEXIBILITY, ASK_F5_EMOTIONAL_INTELLIGENCE, ASK_F6_HEALTH_ENERGY,
    ASK_F7_SELF_PERCEPTION, ASK_F8_ENVIRONMENT_SUPPORT, ASK_F9_RESOURCE_ACCESS
)

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

nest_asyncio.apply()

async def main():
    """
    Основная асинхронная функция для запуска Telegram бота.
    """
    print("Инициализация данных базы данных...")
    initialize_all_data()

    print("Запуск Telegram бота...")
    application = Application.builder().token(settings.BOT_TOKEN).build()

    # ConversationHandler для диалога "Доход"
    income_conversation_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_income_dialog, pattern='^mode_income$'),
        ],
        states={
            GET_INCOME_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_income_input)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_income_dialog),
            CallbackQueryHandler(cancel_income_dialog, pattern='^cancel_income_dialog$'),
            CallbackQueryHandler(back_to_main_menu, pattern='^back_to_main_menu$')
        ],
        allow_reentry=True,
        per_message=False
    )

    # ConversationHandler для опроса факторов контекста
    factor_survey_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_factor_dialog, pattern='^start_factor_survey$')],
        states={
            ASK_F1_MOTIVATION: [CallbackQueryHandler(handle_factor_rating, pattern='^rating_')],
            ASK_F2_LIFE_EXPERIENCE: [CallbackQueryHandler(handle_factor_rating, pattern='^rating_')],
            ASK_F3_PERSISTENCE: [CallbackQueryHandler(handle_factor_rating, pattern='^rating_')],
            ASK_F4_FLEXIBILITY: [CallbackQueryHandler(handle_factor_rating, pattern='^rating_')],
            ASK_F5_EMOTIONAL_INTELLIGENCE: [CallbackQueryHandler(handle_factor_rating, pattern='^rating_')],
            ASK_F6_HEALTH_ENERGY: [CallbackQueryHandler(handle_factor_rating, pattern='^rating_')],
            ASK_F7_SELF_PERCEPTION: [CallbackQueryHandler(handle_factor_rating, pattern='^rating_')],
            ASK_F8_ENVIRONMENT_SUPPORT: [CallbackQueryHandler(handle_factor_rating, pattern='^rating_')],
            ASK_F9_RESOURCE_ACCESS: [CallbackQueryHandler(handle_factor_rating, pattern='^rating_')],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_factor_dialog, pattern='^cancel_factor_dialog$'),
            CommandHandler("cancel", cancel_factor_dialog),
            CallbackQueryHandler(back_to_main_menu, pattern='^back_to_main_menu$')
        ],
        allow_reentry=True,
        per_message=False
    )

    # --- ПОРЯДОК РЕГИСТРАЦИИ ОБРАБОТЧИКОВ ОЧЕНЬ ВАЖЕН ---
    # Более специфичные хендлеры должны быть зарегистрированы раньше, чем более общие.

    application.add_handler(CommandHandler("start", start))  # Команда /start
    application.add_handler(income_conversation_handler)  # Диалог по доходу
    application.add_handler(factor_survey_handler)  # Диалог по факторам

    # Хендлеры для CallbackQuery (кнопок)
    # Сначала специфичные для детализации способа и возврата к списку
    application.add_handler(CallbackQueryHandler(show_income_method_details, pattern='^income_method_details_'))
    application.add_handler(CallbackQueryHandler(show_recommended_methods,
                                                 pattern='^mode_income_recalculate$'))  # <-- ЭТОТ ДОЛЖЕН БЫТЬ ПЕРЕД ОБЩИМ 'mode_'

    # Затем более общие хендлеры для кнопок
    application.add_handler(CallbackQueryHandler(handle_main_menu_choice,
                                                 pattern='^mode_'))  # <-- ЭТОТ ДОЛЖЕН БЫТЬ ПОСЛЕ СПЕЦИФИЧНЫХ 'mode_'
    application.add_handler(CallbackQueryHandler(back_to_main_menu, pattern='^back_to_main_menu$'))

    print("Бот запущен. Ожидание команд...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())