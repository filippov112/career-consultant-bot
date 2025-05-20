import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

class Settings:
    """
    Класс для хранения настроек приложения, загруженных из переменных окружения.
    """
    # Настройки Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")

    # Настройки PostgreSQL
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: str = os.getenv("DB_PORT")
    DB_NAME: str = os.getenv("DB_NAME")

    # Формирование строки подключения к базе данных
    @property
    def DATABASE_URL(self) -> str:
        """
        Формирует URL для подключения к базе данных PostgreSQL.
        """
        # Убедитесь, что все необходимые переменные загружены
        if not all([self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_PORT, self.DB_NAME]):
            raise ValueError("Не все переменные окружения для подключения к БД установлены.")
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

# Создаем единственный экземпляр настроек, чтобы их можно было импортировать в другие модули
settings = Settings()

# if __name__ == "__main__":
#     # Пример использования и проверки загруженных настроек
#     print("Проверка загруженных настроек:")
#     print(f"BOT_TOKEN: {'<скрыто>' if settings.BOT_TOKEN else 'Не установлен'}")
#     print(f"DB_USER: {settings.DB_USER}")
#     print(f"DB_HOST: {settings.DB_HOST}")
#     print(f"DB_PORT: {settings.DB_PORT}")
#     print(f"DB_NAME: {settings.DB_NAME}")
#     try:
#         print(f"DATABASE_URL: {settings.DATABASE_URL}")
#     except ValueError as e:
#         print(f"Ошибка при формировании DATABASE_URL: {e}")