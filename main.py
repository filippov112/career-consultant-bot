# main.py
import logging
from datetime import datetime

from telegram import LinkPreviewOptions # <-- Добавлен импорт
from telegram.ext import Application, ApplicationBuilder, Defaults
from telegram.constants import ParseMode

from config import BOT_TOKEN
import database
import handlers

# Включение логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """
    Главная функция для запуска Telegram-бота.
    """
    logger.info("Инициализация базы данных PostgreSQL...")
    try:
        database.init_db()
        logger.info("База данных PostgreSQL успешно инициализирована.")
    except Exception as e:
        logger.critical(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось инициализировать базу данных PostgreSQL: {e}")
        logger.critical("Убедитесь, что сервер PostgreSQL запущен и настроен правильно в config.py.")
        logger.critical("Бот не может быть запущен без БД.")
        return

    # Глобальные данные для бота, которые будут доступны через context.application.bot_data
    app_data = {
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "admin_ids": [123456789], # Пример ID администраторов
    }

    # Установка ParseMode.HTML и отключение предпросмотра ссылок по умолчанию
    # Исправлено в соответствии с предупреждением:
    defaults = Defaults(
        parse_mode=ParseMode.HTML,
        link_preview_options=LinkPreviewOptions(is_disabled=True) # <-- Изменено
    )

    logger.info("Создание экземпляра приложения бота...")
    application_builder = ApplicationBuilder().token(BOT_TOKEN).defaults(defaults)

    # Исправлено: .application_data() больше не используется в ApplicationBuilder
    # Вместо этого, bot_data устанавливается после создания application
    application = application_builder.build()

    # Добавляем app_data в application.bot_data
    application.bot_data.update(app_data)

    logger.info("Приложение бота успешно создано.")

    # Регистрация обработчиков
    for handler_obj in handlers.ALL_HANDLERS:
        application.add_handler(handler_obj)

    application.add_handler(handlers.unknown_command_handler)
    application.add_handler(handlers.unknown_text_handler)
    logger.info("Обработчики успешно добавлены.")

    logger.info("Запуск бота (опрос обновлений)...")
    try:
        application.run_polling()
    except Exception as e:
        logger.critical(f"Критическая ошибка во время работы бота: {e}")
    finally:
        logger.info("Бот остановлен.")


if __name__ == '__main__':
    main()