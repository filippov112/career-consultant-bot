from typing import Optional

from sqlalchemy.orm import Session
from db import models # Импортируем все наши модели

# --- Функции для работы с моделью User ---

def get_user_by_telegram_id(db: Session, telegram_id: int):
    """
    Получает пользователя по его Telegram ID.
    """
    # Комментарий: Query (запрос) -> filter (фильтрация по условию) -> first (получение первого совпадения)
    return db.query(models.User).filter(models.User.telegram_id == telegram_id).first()

def create_user(db: Session, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """
    Создает нового пользователя в базе данных.
    """
    # Комментарий: Создаем экземпляр модели User
    db_user = models.User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name
    )
    # Комментарий: Добавляем объект в сессию
    db.add(db_user)
    # Комментарий: Фиксируем изменения в БД
    db.commit()
    # Комментарий: Обновляем объект, чтобы получить ID, сгенерированный БД
    db.refresh(db_user)
    return db_user

def update_user_context_factors(db: Session, user_id: int, factors_data: dict):
    """
    Обновляет значения факторов контекста (F1-F9) для пользователя.
    :param db: Сессия базы данных.
    :param user_id: ID пользователя в нашей БД.
    :param factors_data: Словарь с данными факторов, например:
                         {'f1_motivation': 8.5, 'f2_life_experience': 7.0, ...}
    :return: Обновленный объект пользователя или None, если пользователь не найден.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        for factor, value in factors_data.items():
            if hasattr(user, factor): # Проверяем, что атрибут существует в модели
                setattr(user, factor, value)
        db.commit()
        db.refresh(user)
    return user


def update_user_income(db: Session, user_telegram_id: int, income_amount: int):
    """
    Обновляет текущий доход пользователя.
    """
    user = db.query(models.User).filter(models.User.telegram_id == user_telegram_id).first()
    if user:
        user.current_income = income_amount
        db.commit()
        db.refresh(user)
    return user

# --- Функции для работы с моделью Region ---

def get_region_by_name(db: Session, name: str):
    """
    Получает регион по его имени.
    """
    return db.query(models.Region).filter(models.Region.name == name).first()

def create_region(db: Session, name: str, f10_value: float):
    """
    Создает новый регион.
    """
    db_region = models.Region(name=name, f10_value=f10_value)
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    return db_region

# --- Функции для работы с моделью Skill ---

def get_skill_by_name(db: Session, name: str):
    """
    Получает навык по его имени.
    """
    return db.query(models.Skill).filter(models.Skill.name == name).first()

def create_skill(db: Session, name: str, description: str = None):
    """
    Создает новый навык.
    """
    db_skill = models.Skill(name=name, description=description)
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    return db_skill

# --- Функции для работы с моделью Interest ---

def get_interest_by_name(db: Session, name: str):
    """
    Получает интерес по его имени.
    """
    return db.query(models.Interest).filter(models.Interest.name == name).first()

def create_interest(db: Session, name: str):
    """
    Создает новый интерес.
    """
    db_interest = models.Interest(name=name)
    db.add(db_interest)
    db.commit()
    db.refresh(db_interest)
    return db_interest

# --- Функции для работы с моделью Profession ---

def get_profession_by_name(db: Session, name: str):
    """
    Получает профессию по ее имени.
    """
    return db.query(models.Profession).filter(models.Profession.name == name).first()

def create_profession(db: Session, profession_data: dict):
    """
    Создает новую профессию.
    """
    db_profession = models.Profession(**profession_data)
    db.add(db_profession)
    db.commit()
    db.refresh(db_profession)
    return db_profession

# --- Функции для работы с моделью ProfessionInterest ---

def get_profession_interest(db: Session, interest_id: int, profession_id: int):
    """
    Получает связь между профессией и интересом.
    """
    return db.query(models.ProfessionInterest).filter(
        models.ProfessionInterest.interest_id == interest_id,
        models.ProfessionInterest.profession_id == profession_id
    ).first()

def create_profession_interest(db: Session, interest_id: int, profession_id: int, strength: int = 0):
    """
    Создает новую связь между профессией и интересом.
    """
    db_pi = models.ProfessionInterest(
        interest_id=interest_id,
        profession_id=profession_id,
        strength=strength
    )
    db.add(db_pi)
    db.commit()
    db.refresh(db_pi)
    return db_pi

# --- Функции для работы с моделью ProfessionRequirement ---

def get_profession_requirement(db: Session, profession_id: int, skill_id: int, level: str):
    """
    Получает требование к навыку для определенной профессии и уровня.
    """
    return db.query(models.ProfessionRequirement).filter(
        models.ProfessionRequirement.profession_id == profession_id,
        models.ProfessionRequirement.skill_id == skill_id,
        models.ProfessionRequirement.level == level
    ).first()

def create_profession_requirement(db: Session, profession_id: int, skill_id: int, level: str):
    """
    Создает новое требование к навыку для профессии.
    """
    db_pr = models.ProfessionRequirement(
        profession_id=profession_id,
        skill_id=skill_id,
        level=level
    )
    db.add(db_pr)
    db.commit()
    db.refresh(db_pr)
    return db_pr

# --- Функции для работы с моделью IncomeMethod ---


def get_income_method_by_name(db: Session, name: str):
    """
    Получает способ дохода по его имени.
    """
    return db.query(models.IncomeMethod).filter(models.IncomeMethod.name == name).first()


def get_income_method(db: Session, method_id: int) -> Optional[models.IncomeMethod]:
    """
    Получает способ увеличения дохода по его ID.
    """
    return db.query(models.IncomeMethod).filter(models.IncomeMethod.id == method_id).first()


def create_income_method(db: Session, method_data: dict):
    """
    Создает новый способ дохода.
    """
    db_method = models.IncomeMethod(**method_data)
    db.add(db_method)
    db.commit()
    db.refresh(db_method)
    return db_method

# --- Функции для работы с моделью CareerPath (Способ-Должность) ---

def get_career_path_by_name(db: Session, name: str):
    """
    Получает способ продвижения по должности по его имени.
    """
    return db.query(models.CareerPath).filter(models.CareerPath.name == name).first()

def create_career_path(db: Session, path_data: dict):
    """
    Создает новый способ продвижения по должности.
    """
    db_path = models.CareerPath(**path_data)
    db.add(db_path)
    db.commit()
    db.refresh(db_path)
    return db_path

# --- Функции для работы с моделями Карт (пока только для демонстрации) ---

def create_income_map(db: Session, user_id: int, methods_ids: list, probabilities: list):
    """
    Создает новую карту дохода для пользователя.
    (Пример, детали будут доработаны при реализации)
    """
    db_map = models.IncomeMap(user_id=user_id)
    # Здесь нужно будет динамически заполнять methodX_id и probabilityX
    # Для простоты, пока заполним только первые элементы
    if methods_ids:
        db_map.method1_id = methods_ids[0]
        db_map.probability1 = probabilities[0] if probabilities else None
    db.add(db_map)
    db.commit()
    db.refresh(db_map)
    return db_map

def get_user_income_maps(db: Session, user_id: int):
    """
    Получает все карты дохода для пользователя.
    """
    return db.query(models.IncomeMap).filter(models.IncomeMap.user_id == user_id).all()

def delete_income_map(db: Session, map_id: int):
    """
    Удаляет карту дохода по ID.
    """
    db_map = db.query(models.IncomeMap).filter(models.IncomeMap.id == map_id).first()
    if db_map:
        db.delete(db_map)
        db.commit()
        return True
    return False


if __name__ == "__main__":
    from db.database import SessionLocal
    print("Тестирование CRUD-операций...")

    # Создаем временную сессию БД для тестирования
    with SessionLocal() as db:
        # Тестируем User
        test_telegram_id = 123456789
        user = get_user_by_telegram_id(db, test_telegram_id)
        if not user:
            print(f"Пользователь с Telegram ID {test_telegram_id} не найден. Создаем...")
            user = create_user(db, test_telegram_id, username="test_user", first_name="Test", last_name="User")
            print(f"Создан пользователь: {user}")
        else:
            print(f"Найден пользователь: {user}")

        # Тестируем обновление факторов контекста
        updated_factors = {'f1_motivation': 7.5, 'f3_persistence': 9.0}
        updated_user = update_user_context_factors(db, user.id, updated_factors)
        print(f"Обновленный пользователь (факторы F1, F3): F1={updated_user.f1_motivation}, F3={updated_user.f3_persistence}")

        # Тестируем Region
        region_name = "Europe"
        region = get_region_by_name(db, region_name)
        if not region:
            print(f"Регион '{region_name}' не найден. Создаем...")
            region = create_region(db, region_name, 7.0)
            print(f"Создан регион: {region}")
        else:
            print(f"Найден регион: {region}")

        # Тестируем Skill
        skill_name = "Python"
        skill = get_skill_by_name(db, skill_name)
        if not skill:
            print(f"Навык '{skill_name}' не найден. Создаем...")
            skill = create_skill(db, skill_name, "Программирование на Python")
            print(f"Создан навык: {skill}")
        else:
            print(f"Найден навык: {skill}")

        # Тестируем IncomeMethod (для примера)
        income_method_data = {
            "name": "Freelance Writing",
            "short_description": "Earn by writing articles.",
            "detailed_description": "Detailed guide on freelance writing...",
            "speed_of_result": 7,
            "difficulty": 6,
            "financial_investment": 2,
            "income_potential": 8,
            "flexible_schedule": 9,
            "risks": 4,
            "psychological_comfort": 7,
            "impact_on_current_job": 3,
            "hard_skills": 7,
            "soft_skills": 8,
            "geography": 10,
            "special_knowledge": 5,
            "engagement": 8,
            "f11_complexity": 6.0, # Пример расчета
            "f12_needed_time": 7.0 # Пример расчета
        }
        income_method = get_income_method_by_name(db, income_method_data["name"])
        if not income_method:
            print(f"Способ дохода '{income_method_data['name']}' не найден. Создаем...")
            income_method = create_income_method(db, income_method_data)
            print(f"Создан способ дохода: {income_method}")
        else:
            print(f"Найден способ дохода: {income_method}")

        # Тестируем создание карты дохода (базовый пример)
        if user and income_method:
            print(f"Создаем карту дохода для пользователя {user.id} со способом {income_method.id}...")
            income_map = create_income_map(db, user.id, [income_method.id], [0.85])
            print(f"Создана карта дохода: {income_map}")

            # Получаем все карты дохода пользователя
            user_maps = get_user_income_maps(db, user.id)
            print(f"Все карты дохода для пользователя {user.id}:")
            for m in user_maps:
                print(f"  - {m}")
        else:
            print("Не удалось создать карту дохода: пользователь или способ не найден.")

        print("CRUD-операции протестированы.")