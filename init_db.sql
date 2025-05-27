-- Создание расширения, если оно необходимо, например, для генерации UUID, хотя в данном проекте не требуется
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблица для хранения информации о пользователях Telegram
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY, -- Telegram User ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для хранения списка факторов выбора способа увеличения дохода
-- Факторы будут загружаться из JSON-файла
CREATE TABLE IF NOT EXISTS factors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL, -- Название фактора, например "Скорость результата"
    question_text TEXT NOT NULL DEFAULT '' -- Добавляем новый столбец для текста вопроса
);

-- Таблица для хранения способов увеличения дохода
-- Способы и их описания будут загружаться из JSON-файла
CREATE TABLE IF NOT EXISTS income_methods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL, -- Название способа, например "Фриланс"
    description TEXT NOT NULL -- Подробное описание способа
);

-- Таблица для хранения значений факторов для каждого способа увеличения дохода
-- Эти значения будут загружаться из JSON-файла.
-- Используем INTEGER для score, поскольку шкала от 1 до 10.
CREATE TABLE IF NOT EXISTS method_factor_scores (
    method_id INTEGER REFERENCES income_methods(id) ON DELETE CASCADE,
    factor_id INTEGER REFERENCES factors(id) ON DELETE CASCADE,
    score INTEGER NOT NULL CHECK (score >= 1 AND score <= 10), -- Оценка фактора для данного способа (1-10)
    PRIMARY KEY (method_id, factor_id) -- Композитный ключ
);

-- Таблица для хранения предпочтений пользователя по каждому фактору
-- Здесь будут сохраняться оценки пользователя, которые он дает через inline-кнопки
-- Используем INTEGER для preference_score, поскольку шкала от 1 до 5.
CREATE TABLE IF NOT EXISTS user_factor_preferences (
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    factor_id INTEGER REFERENCES factors(id) ON DELETE CASCADE,
    preference_score INTEGER NOT NULL CHECK (preference_score >= 1 AND preference_score <= 5), -- Оценка пользователя (1-5)
    PRIMARY KEY (user_id, factor_id) -- Композитный ключ
);