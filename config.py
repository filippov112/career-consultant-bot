# config.py
import os
from dotenv import load_dotenv
import logging

# Загружаем переменные окружения из файла .env
# load_dotenv() ищет файл .env в текущей директории или выше по дереву
# и загружает найденные переменные в окружение os.environ
load_dotenv()

logger = logging.getLogger(__name__)

def get_env_variable(var_name: str, default_value: str | None = None, required: bool = True) -> str | None:
    """
    Получает переменную окружения.
    Если переменная обязательна и не найдена, выбрасывает исключение.
    Если не обязательна и не найдена, возвращает default_value.
    """
    value = os.getenv(var_name)
    if value is None:
        if required:
            logger.error(f"Критическая ошибка: Обязательная переменная окружения '{var_name}' не установлена. "
                         f"Пожалуйста, определите ее в файле .env или в системных переменных окружения.")
            raise ValueError(f"Переменная окружения '{var_name}' не установлена.")
        else:
            logger.warning(f"Необязательная переменная окружения '{var_name}' не установлена. Используется значение по умолчанию: {default_value}")
            return default_value
    return value

# --- Telegram Bot Configuration ---
BOT_TOKEN = get_env_variable('BOT_TOKEN')

# --- PostgreSQL Database Configuration ---
DB_HOST = get_env_variable('DB_HOST', default_value='localhost', required=False)
DB_PORT = get_env_variable('DB_PORT', default_value='5432', required=False)
DB_NAME = get_env_variable('DB_NAME', required=True)
DB_USER = get_env_variable('DB_USER', required=True)
DB_PASSWORD = get_env_variable('DB_PASSWORD', required=True)


# --- Optional Configurations ---
# Пример для LOG_LEVEL
# LOG_LEVEL = get_env_variable('LOG_LEVEL', default_value='INFO', required=False).upper()

# Пример для ADMIN_IDS (список ID администраторов)
# admin_ids_str = get_env_variable('ADMIN_IDS', default_value='', required=False)
# ADMIN_IDS = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip().isdigit()] \
#             if admin_ids_str else []


# Проверка при импорте, что все обязательные переменные загружены
# (get_env_variable уже делает это, но можно добавить дополнительную логику)
if not BOT_TOKEN or not DB_NAME or not DB_USER or not DB_PASSWORD:
    # Это сообщение не должно появиться, если get_env_variable работает корректно
    # и required=True для этих переменных
    logger.critical("Одна или несколько критически важных переменных окружения не были загружены.")
    # Выход из программы или более сложная обработка ошибки
    # exit(1) # Раскомментировать, если нужна жесткая остановка

logger.info("Конфигурация успешно загружена из переменных окружения.")

# Остальные файлы (database.py, main.py и т.д.) будут импортировать
# эти переменные из config.py как и раньше, им не нужны изменения.