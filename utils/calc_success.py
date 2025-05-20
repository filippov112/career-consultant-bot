import math
from typing import Optional
from db import models  # Импортируем модели для работы с объектами БД


# --- Функции для расчета факторов на основе данных пользователя ---

def calculate_context_factors(user: models.User, region: Optional[models.Region] = None) -> dict:
    """
    Рассчитывает контекстные факторы F1-F10 для пользователя.
    На данный момент F1-F9 берутся напрямую из модели User.
    F10 (географический) берется из Region, если он привязан.
    В дальнейшем будет расширен для более сложных вычислений.
    """
    factors = {
        'f1_motivation': user.f1_motivation,
        'f2_life_experience': user.f2_life_experience,
        'f3_persistence': user.f3_persistence,
        'f4_flexibility': user.f4_flexibility,  # ИСПРАВЛЕНО
        'f5_emotional_intelligence': user.f5_emotional_intelligence,  # ИСПРАВЛЕНО
        'f6_health_energy': user.f6_health_energy,  # ИСПРАВЛЕНО
        'f7_self_perception': user.f7_self_perception,  # ИСПРАВЛЕНО
        'f8_environment_support': user.f8_environment_support,  # ИСПРАВЛЕНО
        'f9_resource_access': user.f9_resource_access,  # ИСПРАВЛЕНО
        'f10_cultural_economic_environment': region.f10_value if region else 0.0
        # Для F10 используем f10_value из Region
    }
    # Заглушка: Если факторы еще не заданы у пользователя (None), используем значения по умолчанию
    for k, v in factors.items():
        if v is None:
            # Для демонстрации используем среднее значение или 5.0 (или 0.0, как в вашей модели)
            # Если в модели default=0.0, то None не должно быть, но на всякий случай оставим
            factors[k] = 0.0  # Исправлено на 0.0, если в модели default=0.0

    # Также убедимся, что f10_cultural_economic_environment не None, если region был None
    if factors['f10_cultural_economic_environment'] is None:
        factors['f10_cultural_economic_environment'] = 0.0  # Дефолтное значение для F10, если нет региона

    return factors


# --- Функции для расчета факторов для Способов (Доход/Должность) ---

def calculate_income_method_derived_factors(method: models.IncomeMethod) -> models.IncomeMethod:
    """
    Рассчитывает и обновляет F11 (Сложность) и F12 (Необходимое время) для IncomeMethod.
    Формулы:
    F11_Complexity = Difficulty * Hard_Skills * Special_Knowledge
    F12_Needed_Time = Speed_of_Result * (1 / Flexible_Schedule) * (1 / Engagement) (пока упрощенно)
    """
    # Убедимся, что значения не None, используем 1.0 для избежания ошибок
    difficulty = method.difficulty if method.difficulty is not None else 1.0
    hard_skills = method.hard_skills if method.hard_skills is not None else 1.0
    special_knowledge = method.special_knowledge if method.special_knowledge is not None else 1.0
    speed_of_result = method.speed_of_result if method.speed_of_result is not None else 1.0
    flexible_schedule = method.flexible_schedule if method.flexible_schedule is not None else 1.0
    engagement = method.engagement if method.engagement is not None else 1.0

    # Расчет F11 (Сложность)
    method.f11_complexity = difficulty * hard_skills * special_knowledge

    # Расчет F12 (Необходимое время). Используем 10.0 для нормализации для примера
    # Чем выше speed_of_result, тем меньше f12_needed_time.
    # Чем выше flexible_schedule, тем меньше f12_needed_time.
    # Чем выше engagement, тем меньше f12_needed_time.
    # Для избежания деления на ноль или очень малые числа, используем max(value, 1)
    method.f12_needed_time = (10.0 / max(speed_of_result, 1)) * (10.0 / max(flexible_schedule, 1)) * (
                10.0 / max(engagement, 1))

    # Можно добавить логику для нормализации или ограничения значений, если они получаются слишком большими/малыми
    method.f11_complexity = round(method.f11_complexity, 2)
    method.f12_needed_time = round(method.f12_needed_time, 2)

    return method


def calculate_career_path_derived_factors(path: models.CareerPath) -> models.CareerPath:
    """
    Рассчитывает и обновляет F11 (Сложность) и F12 (Необходимое время) для CareerPath.
    Формулы:
    F11_Complexity = Материал_усвоение * Скорость_применения (пока упрощенно)
    F12_Needed_Time = Часы_на_освоение (пока упрощенно)
    """
    material_assimilation = path.material_assimilation if path.material_assimilation is not None else 1.0
    application_speed = path.application_speed if path.application_speed is not None else 1.0
    hours_to_master = path.hours_to_master if path.hours_to_master is not None else 1.0

    path.f11_complexity = material_assimilation * application_speed
    path.f12_needed_time = float(hours_to_master)  # Просто приводим к float для единообразия

    path.f11_complexity = round(path.f11_complexity, 2)
    path.f12_needed_time = round(path.f12_needed_time, 2)

    return path


# --- Функции для расчета баллов успеха ---

def calculate_success_score_for_income_method(
    user_factors: dict,
    method: models.IncomeMethod,
    user_current_income: int
) -> float:
    """
    Рассчитывает общий балл успеха для способа дохода.
    Использует формулу, учитывающую F1-F12 и критерии способа.
    """
    score = 0.0

    # Совместимость с факторами пользователя
    score += (user_factors['f1_motivation'] + method.engagement) / 2
    score += (user_factors['f3_persistence'] + method.difficulty) / 2
    score += (user_factors['f4_flexibility'] + method.flexible_schedule) / 2
    score += (user_factors['f5_emotional_intelligence'] + method.psychological_comfort) / 2
    score += (user_factors['f6_health_energy'] + method.engagement) / 2
    score += (user_factors['f7_self_perception'] + method.income_potential) / 2
    score += (user_factors['f8_environment_support'] + (10 - method.risks)) / 2
    score += (user_factors['f9_resource_access'] + (10 - method.financial_investment)) / 2
    score += (user_factors['f10_cultural_economic_environment'] + method.geography) / 2

    # Дополнительные факторы специфичные для метода
    score += method.income_potential
    score += method.speed_of_result
    score += (10 - method.financial_investment)
    score += (10 - method.difficulty)
    score += (10 - method.risks)
    score += (10 - method.impact_on_current_job) # <-- ДОБАВЛЕНО: чем меньше влияние, тем выше балл

    # Учитываем рассчитанные факторы F11, F12
    score += (200 - method.f11_complexity) / 20
    score += (100 - method.f12_needed_time) / 10

    # Общая нормализация балла
    # Увеличил делитель, т.к. добавили новое слагаемое impact_on_current_job
    return round(score / 21.0, 2) # <-- Изменил делитель для нормализации



# --- Основная функция выбора способов дохода ---

def get_recommended_income_methods(
        db_session,
        user_telegram_id: int,
        top_n: int = 3
) -> list[tuple[models.IncomeMethod, float]]:
    """
    Получает рекомендованные способы увеличения дохода для пользователя.
    """
    user = db_session.query(models.User).filter(models.User.telegram_id == user_telegram_id).first()
    if not user:
        return []

    # Предположим, что у пользователя есть привязка к региону (или будем запрашивать)
    # Для простоты, пока будем считать, что региона нет, или всегда использовать один и тот же тестовый
    # region = crud.get_region_by_name(db_session, "Россия") # Пример
    # user_factors = calculate_context_factors(user, region)
    # Для демонстрации пока используем заглушку для факторов пользователя,
    # если они не заданы, или возьмем из БД
    user_factors = calculate_context_factors(user)

    # Получаем все доступные способы дохода
    all_methods = db_session.query(models.IncomeMethod).all()

    scored_methods = []
    for method in all_methods:
        # Убедимся, что расчетные факторы F11, F12 актуальны
        method = calculate_income_method_derived_factors(method)

        # Расчитываем балл успеха для каждого метода
        score = calculate_success_score_for_income_method(
            user_factors,
            method,
            user.current_income  # Передаем текущий доход пользователя
        )
        scored_methods.append((method, score))

    # Сортируем по убыванию балла успеха
    scored_methods.sort(key=lambda x: x[1], reverse=True)

    # Возвращаем N лучших
    return scored_methods[:top_n]