# quizzes_data.py

# Словарь с тестами.
# Каждый вопрос теперь содержит опции в виде списка словарей: {"text": "...", "score": X}

QUIZZES = {
    "python1": {
        "name": "Основы Python (с баллами)",
        "description": "Тест на знание базовых концепций Python. За каждый ответ начисляются баллы.",
        "questions": [
            {
                "text": "Какой тип данных используется для хранения целых чисел в Python?",
                "options": [
                    {"text": "float", "score": 0},
                    {"text": "str", "score": 0},
                    {"text": "int", "score": 10}, # Правильный ответ дает 10 баллов
                    {"text": "bool", "score": 0}
                ]
            },
            {
                "text": "Как создать пустой список в Python?",
                "options": [
                    {"text": "list()", "score": 5},  # Частично правильный
                    {"text": "[]", "score": 5},    # Частично правильный
                    {"text": "Оба варианта верны", "score": 10}, # Наиболее полный
                    {"text": "Ни один из вариантов", "score": 0}
                ]
            },
            {
                "text": "Какой оператор используется для возведения в степень?",
                "options": [
                    {"text": "^", "score": 0},
                    {"text": "**", "score": 10},
                    {"text": "%", "score": 0},
                    {"text": "//", "score": 0}
                ]
            }
        ]
        # max_possible_score будет рассчитан автоматически
    },
    "telegram1": {
        "name": "Telegram Боты (с баллами)",
        "description": "Тест по основам разработки Telegram ботов. За каждый ответ начисляются баллы.",
        "questions": [
            {
                "text": "Какой метод используется для отправки текстового сообщения через Telegram Bot API?",
                "options": [
                    {"text": "sendText", "score": 0},
                    {"text": "sendMessage", "score": 10},
                    {"text": "postMessage", "score": 0},
                    {"text": "writeMessage", "score": 0}
                ]
            },
            {
                "text": "Что такое 'webhook' в контексте Telegram ботов?",
                "options": [
                    {"text": "Способ получить обновления от Telegram через HTTP POST запросы", "score": 10},
                    {"text": "Инструмент для отладки бота", "score": 2}, # Может быть полезен, но не определение
                    {"text": "Формат файла конфигурации бота", "score": 0},
                    {"text": "Тип клавиатуры в сообщении", "score": 0}
                ]
            }
        ]
    }
}

def _calculate_max_score(questions: list) -> int:
    """
    Вспомогательная функция для расчета максимального балла за список вопросов.
    Максимальный балл за вопрос - это максимальный балл среди его вариантов.
    """
    total_max_score = 0
    for question in questions:
        if question.get("options"):
            max_score_for_question = 0
            for option in question["options"]:
                if option.get("score", 0) > max_score_for_question:
                    max_score_for_question = option["score"]
            total_max_score += max_score_for_question
    return total_max_score

def get_quiz_by_id(quiz_id: str) -> dict | None:
    """
    Возвращает данные теста по его идентификатору, добавляя рассчитанный 'max_possible_score'.
    """
    quiz_data = QUIZZES.get(quiz_id)
    if quiz_data:
        # Копируем, чтобы не изменять исходный QUIZZES
        quiz_data_copy = quiz_data.copy()
        quiz_data_copy["questions"] = [q.copy() for q in quiz_data.get("questions", [])] # Глубокое копирование вопросов
        quiz_data_copy['max_possible_score'] = _calculate_max_score(quiz_data_copy.get("questions", []))
        return quiz_data_copy
    return None

def get_all_quizzes_info() -> list:
    """
    Возвращает список словарей с информацией о всех доступных тестах (id, имя и макс. балл).
    """
    quizzes_info = []
    for q_id, q_data in QUIZZES.items():
        max_score = _calculate_max_score(q_data.get("questions", []))
        quizzes_info.append({
            "id": q_id,
            "name": q_data.get("name", "Неизвестный тест"),
            "max_score": max_score # Добавляем информацию о макс. балле
        })
    return quizzes_info

if __name__ == '__main__':
    # Пример использования
    python_quiz = get_quiz_by_id("python_basics")
    if python_quiz:
        print(f"Тест: {python_quiz['name']}")
        print(f"Описание: {python_quiz['description']}")
        print(f"Максимально возможный балл: {python_quiz['max_possible_score']}")
        # print(f"Вопросы: {python_quiz['questions']}")

    all_quizzes = get_all_quizzes_info()
    print("\nВсе тесты:")
    for quiz_info in all_quizzes:
        print(f"- {quiz_info['name']} (ID: {quiz_info['id']}, Макс. балл: {quiz_info['max_score']})")