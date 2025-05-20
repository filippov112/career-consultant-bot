from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import settings # Импортируем наш объект настроек

# Создаем движок SQLAlchemy
# echo=False означает, что SQLAlchemy не будет выводить все SQL-запросы в консоль.
# Для отладки можно установить в True.
engine = create_engine(settings.DATABASE_URL, echo=False)

# Создаем фабрику сессий.
# expire_on_commit=False предотвращает "обезличивание" объектов после коммита,
# позволяя получить к ним доступ вне сессии.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для декларативных моделей SQLAlchemy.
# Все наши ORM-модели будут наследоваться от него.
Base = declarative_base()

def get_db():
    """
    Генераторная функция для получения сессии базы данных.
    Используется для создания и закрытия сессии в контексте запроса.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Пример использования (можно удалить после проверки)
if __name__ == "__main__":
    print("Попытка подключения к базе данных...")
    try:
        # Простая проверка подключения: пытаемся получить сессию и закрыть её.
        with SessionLocal() as db:
            print("Успешное подключение к базе данных!")
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")