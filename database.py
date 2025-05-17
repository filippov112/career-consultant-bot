# database.py
import psycopg2
from psycopg2.extras import RealDictCursor # Позволяет получать строки как словари
from datetime import datetime
import json
import logging

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Устанавливает соединение с базой данных PostgreSQL.
    Возвращает объект соединения.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Ошибка подключения к PostgreSQL: {e}")
        # В реальном приложении здесь может быть более сложная обработка,
        # например, попытки переподключения или уведомление администратора.
        raise  # Перевыбрасываем исключение, чтобы вызывающий код знал об ошибке

def init_db():
    """
    Инициализирует базу данных и создает таблицы, если они еще не существуют.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Таблица пользователей
        # Используем JSONB для quiz_results для лучшей производительности и возможностей индексации в PostgreSQL
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registration_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            quiz_results JSONB DEFAULT '{}'::jsonb
        )
        ''')
        # Примечание: user_id в Telegram может быть большим, поэтому BIGINT.
        # registration_date теперь TIMESTAMP WITH TIME ZONE и имеет значение по умолчанию.

        # Можно добавить другие таблицы по аналогии (для тестов, вопросов и т.д.)
        # Например:
        # CREATE TABLE IF NOT EXISTS quizzes (
        #     quiz_id SERIAL PRIMARY KEY,
        #     quiz_internal_id TEXT UNIQUE NOT NULL, -- Идентификатор из quizzes_data.py
        #     quiz_name TEXT NOT NULL,
        #     description TEXT,
        #     max_possible_score INTEGER
        # );
        #
        # CREATE TABLE IF NOT EXISTS questions (
        #     question_id SERIAL PRIMARY KEY,
        #     quiz_id INTEGER REFERENCES quizzes(quiz_id) ON DELETE CASCADE,
        #     question_text TEXT NOT NULL,
        #     options JSONB NOT NULL -- [{"text": "Option 1", "score": 10}, ...]
        # );
        # Пока что тесты хранятся в quizzes_data.py для простоты шаблона.

        conn.commit()
        logger.info("База данных PostgreSQL инициализирована (таблицы проверены/созданы).")
    except psycopg2.Error as e:
        logger.error(f"Ошибка при инициализации БД PostgreSQL: {e}")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


def add_or_update_user(user_id: int, username: str, first_name: str, last_name: str):
    """
    Добавляет нового пользователя или обновляет информацию о существующем.
    """
    sql = '''
    INSERT INTO users (user_id, username, first_name, last_name, registration_date, quiz_results)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (user_id) DO UPDATE SET
        username = EXCLUDED.username,
        first_name = EXCLUDED.first_name,
        last_name = EXCLUDED.last_name,
        registration_date = CASE  -- Обновлять дату регистрации только если она не установлена,
                                  -- или оставить как есть, или обновлять всегда.
                                  -- Здесь: обновляем дату при каждом /start для простоты.
            WHEN users.registration_date IS NULL THEN EXCLUDED.registration_date
            ELSE users.registration_date
        END;
    '''
    # registration_date = datetime.now(datetime.timezone.utc) # Используем UTC
    registration_date = datetime.now() # или время сервера, если настроено
    initial_quiz_results = json.dumps({})

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql, (user_id, username, first_name, last_name, registration_date, initial_quiz_results))
        conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Ошибка при добавлении/обновлении пользователя {user_id}: {e}")
        if conn: conn.rollback() # Откатываем транзакцию при ошибке
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

def get_user_data(user_id: int) -> dict | None:
    """
    Получает данные пользователя по его ID.
    Возвращает dict или None, если пользователь не найден.
    """
    sql = "SELECT * FROM users WHERE user_id = %s;"
    try:
        conn = get_db_connection()
        # RealDictCursor возвращает строки как словари {column_name: value}
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql, (user_id,))
        user_data = cursor.fetchone()
        return user_data if user_data else None
    except psycopg2.Error as e:
        logger.error(f"Ошибка при получении данных пользователя {user_id}: {e}")
        return None
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

def save_quiz_result(user_id: int, quiz_name: str, achieved_score: int, max_score_for_quiz: int):
    """
    Сохраняет результаты теста для пользователя.
    Результаты добавляются или обновляются в JSONB-поле quiz_results.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Получаем текущие результаты
        cursor.execute("SELECT quiz_results FROM users WHERE user_id = %s;", (user_id,))
        row = cursor.fetchone()

        if row:
            quiz_results = row['quiz_results'] if row['quiz_results'] else {}
            quiz_results[quiz_name] = {
                "achieved_score": achieved_score,
                "max_possible_score": max_score_for_quiz,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            updated_results_json = json.dumps(quiz_results) # psycopg2 сам преобразует в jsonb

            # Обновляем поле quiz_results
            cursor.execute("UPDATE users SET quiz_results = %s WHERE user_id = %s;", (updated_results_json, user_id))
            conn.commit()
            logger.info(f"Результат теста '{quiz_name}' для пользователя {user_id} сохранен.")
        else:
            logger.warning(f"Попытка сохранить результат теста для несуществующего пользователя {user_id}.")

    except psycopg2.Error as e:
        logger.error(f"Ошибка при сохранении результата теста для пользователя {user_id}: {e}")
        if conn: conn.rollback()
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()


if __name__ == '__main__':
    # Этот блок выполнится, если запустить файл database.py напрямую
    # Используется для первоначальной инициализации БД
    logging.basicConfig(level=logging.INFO) # Для вывода логов init_db
    print("Попытка инициализации базы данных PostgreSQL...")
    try:
        # Перед запуском убедитесь, что база данных 'telegram_bot_db' создана в PostgreSQL
        # и пользователь 'your_db_user' имеет к ней доступ.
        # Пример создания БД и пользователя в psql:
        # CREATE DATABASE telegram_bot_db;
        # CREATE USER your_db_user WITH PASSWORD 'your_db_password';
        # GRANT ALL PRIVILEGES ON DATABASE telegram_bot_db TO your_db_user;
        # \c telegram_bot_db -- подключиться к БД
        # GRANT ALL ON SCHEMA public TO your_db_user; -- дать права на схему public (где будут таблицы)
        init_db()

        # Пример использования (раскомментируйте для теста):
        # print("Тестирование функций БД...")
        # test_user_id = 123456789
        # add_or_update_user(test_user_id, 'testpguser', 'Test', 'PGUserov')
        # user = get_user_data(test_user_id)
        # if user:
        #     print(f"Найден пользователь: {user['first_name']}, Результаты тестов: {user['quiz_results']}")
        #
        # save_quiz_result(test_user_id, "Python Advanced", 75, 100)
        # user = get_user_data(test_user_id)
        # if user:
        #      print(f"Обновленные результаты тестов: {user['quiz_results']}")
        # else:
        #     print(f"Пользователь {test_user_id} не найден после обновления.")

    except Exception as e:
        print(f"Не удалось выполнить операции с БД: {e}")