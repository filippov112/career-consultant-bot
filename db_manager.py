import os
import json
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection as PgConnection

class DBManager:
    def __init__(self):
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self.conn = None

    def connect(self) -> PgConnection:
        if self.conn is None or self.conn.closed:
            try:
                self.conn = psycopg2.connect(
                    host=self.db_host,
                    port=self.db_port,
                    dbname=self.db_name,
                    user=self.db_user,
                    password=self.db_password
                )
                self.conn.autocommit = True
                print("Успешное подключение к базе данных PostgreSQL.")
            except psycopg2.Error as e:
                print(f"Ошибка подключения к базе данных: {e}")
                self.conn = None
        return self.conn

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()
            print("Соединение с базой данных закрыто.")

    def _execute_query(self, query: sql.Composable, params=None, fetch_one=False, fetch_all=False):
        conn = self.connect()
        if not conn:
            return None

        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if fetch_one:
                    return cur.fetchone()
                if fetch_all:
                    return cur.fetchall()
        except psycopg2.Error as e:
            print(f"Ошибка при выполнении запроса: {e}")
            return None

    def initialize_db_schema(self, sql_script_path: str):
        conn = self.connect()
        if not conn:
            return

        try:
            with open(sql_script_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            with conn.cursor() as cur:
                cur.execute(sql_script)
            print(f"Схема базы данных успешно инициализирована из {sql_script_path}")
        except FileNotFoundError:
            print(f"Ошибка: Файл SQL-скрипта '{sql_script_path}' не найден.")
        except psycopg2.Error as e:
            print(f"Ошибка при инициализации схемы БД: {e}")

    def load_factors_from_json(self, json_path: str):
        conn = self.connect()
        if not conn:
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                factors_data = json.load(f)

            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM factors;")
                if cur.fetchone()[0] > 0:
                    print("Таблица 'factors' уже содержит данные. Пропуск загрузки.")
                    # Если данные уже есть, но нужно обновить вопрос, можно добавить логику UPDATE
                    # Но пока что оставим так, чтобы не дублировать.
                    # Если ты изменил question_text в JSON и хочешь обновить БД,
                    # тебе нужно будет очистить таблицу factors и перезапустить бота.
                    return

                for factor in factors_data:
                    # Изменяем запрос:
                    query = sql.SQL(
                        "INSERT INTO factors (id, name, question_text) VALUES (%s, %s, %s) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, question_text = EXCLUDED.question_text;")
                    self._execute_query(query, (factor['id'], factor['name'], factor['question_text']))
                print(f"Факторы успешно загружены из {json_path}")
        except FileNotFoundError:
            print(f"Ошибка: Файл факторов '{json_path}' не найден.")
        except json.JSONDecodeError:
            print(f"Ошибка: Некорректный формат JSON-файла '{json_path}'.")
        except Exception as e:
            print(f"Неизвестная ошибка при загрузке факторов: {e}")

    def load_income_methods_from_json(self, json_path: str):
        conn = self.connect()
        if not conn:
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                methods_data = json.load(f)

            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM income_methods;")
                if cur.fetchone()[0] > 0:
                    print("Таблицы 'income_methods' и 'method_factor_scores' уже содержат данные. Пропуск загрузки.")
                    return

                for method in methods_data:
                    insert_method_query = sql.SQL(
                        "INSERT INTO income_methods (id, name, description) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING RETURNING id;"
                    )
                    cur.execute(insert_method_query, (method['id'], method['name'], method['description']))
                    method_id = cur.fetchone()[0]

                    for factor_name, score in method['factors'].items():
                        get_factor_id_query = sql.SQL("SELECT id FROM factors WHERE name = %s;")
                        cur.execute(get_factor_id_query, (factor_name,))
                        factor_row = cur.fetchone()
                        if factor_row:
                            factor_id = factor_row[0]
                            insert_score_query = sql.SQL(
                                "INSERT INTO method_factor_scores (method_id, factor_id, score) VALUES (%s, %s, %s);"
                            )
                            cur.execute(insert_score_query, (method_id, factor_id, score))
                        else:
                            print(f"Предупреждение: Фактор '{factor_name}' не найден в БД для метода '{method['name']}'.")
                print(f"Способы увеличения дохода и их факторы успешно загружены из {json_path}")
        except FileNotFoundError:
            print(f"Ошибка: Файл методов '{json_path}' не найден.")
        except json.JSONDecodeError:
            print(f"Ошибка: Некорректный формат JSON-файла '{json_path}'.")
        except Exception as e:
            print(f"Неизвестная ошибка при загрузке способов: {e}")

    def get_all_factors(self):
        """Получает все факторы из базы данных, включая текст вопроса."""
        # Изменяем запрос, чтобы выбрать также question_text
        query = sql.SQL("SELECT id, name, question_text FROM factors ORDER BY id;")
        return self._execute_query(query, fetch_all=True)

    def get_user_preferences(self, user_id: int) -> dict:
        """Получает предпочтения пользователя по факторам в виде словаря {factor_id: preference_score}."""
        query = sql.SQL("SELECT factor_id, preference_score FROM user_factor_preferences WHERE user_id = %s;")
        preferences = self._execute_query(query, (user_id,), fetch_all=True)
        return {p[0]: p[1] for p in preferences} if preferences else {}

    def save_user_preference(self, user_id: int, factor_id: int, score: int):
        query = sql.SQL(
            """
            INSERT INTO user_factor_preferences (user_id, factor_id, preference_score)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, factor_id) DO UPDATE SET preference_score = EXCLUDED.preference_score;
            """
        )
        self._execute_query(query, (user_id, factor_id, score))

    def add_user_if_not_exists(self, user_id: int):
        query = sql.SQL("INSERT INTO users (id) VALUES (%s) ON CONFLICT (id) DO NOTHING;")
        self._execute_query(query, (user_id,))

    def get_all_methods_with_factors(self) -> list:
        """
        Получает все способы увеличения дохода с их факторными оценками.
        Возвращает список словарей:
        [
            {'id': 1, 'name': 'Метод 1', 'description': '...', 'factors': {'FactorName1': score1, 'FactorName2': score2}},
            {'id': 2, 'name': 'Метод 2', 'description': '...', 'factors': {'FactorName1': score3, 'FactorName2': score4}},
            ...
        ]
        """
        query = sql.SQL(
            """
            SELECT
                im.id AS method_id,
                im.name AS method_name,
                im.description AS method_description,
                f.name AS factor_name,
                mfs.score AS factor_score
            FROM
                income_methods im
            JOIN
                method_factor_scores mfs ON im.id = mfs.method_id
            JOIN
                factors f ON mfs.factor_id = f.id
            ORDER BY
                im.id, f.id;
            """
        )
        raw_data = self._execute_query(query, fetch_all=True)

        if not raw_data:
            return []

        methods_dict = {}
        for row in raw_data:
            method_id, method_name, method_description, factor_name, factor_score = row
            if method_id not in methods_dict:
                methods_dict[method_id] = {
                    'id': method_id,
                    'name': method_name,
                    'description': method_description,
                    'factors': {}
                }
            methods_dict[method_id]['factors'][factor_name] = factor_score

        return list(methods_dict.values())

    def get_method_details(self, method_id: int):
        """
        Получает подробную информацию об одном способе по его ID,
        включая факторные оценки.
        """
        query = sql.SQL(
            """
            SELECT
                im.id,
                im.name,
                im.description,
                f.name AS factor_name,
                mfs.score AS factor_score
            FROM
                income_methods im
            LEFT JOIN -- Используем LEFT JOIN, чтобы получить метод, даже если у него нет факторов (хотя у нас они должны быть)
                method_factor_scores mfs ON im.id = mfs.method_id
            LEFT JOIN
                factors f ON mfs.factor_id = f.id
            WHERE
                im.id = %s
            ORDER BY
                f.id; -- Сортируем по ID фактора для последовательности
            """
        )
        raw_data = self._execute_query(query, (method_id,), fetch_all=True)

        if not raw_data:
            return None

        method_info = {
            'id': raw_data[0][0],
            'name': raw_data[0][1],
            'description': raw_data[0][2],
            'factors': {}
        }
        for row in raw_data:
            factor_name, factor_score = row[3], row[4]
            if factor_name and factor_score is not None: # Убедимся, что данные фактора существуют
                method_info['factors'][factor_name] = factor_score
        return method_info