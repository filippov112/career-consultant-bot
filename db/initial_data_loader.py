import json
import os
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine, Base
from db import models, crud # Импортируем модели и CRUD-операции

# Определяем путь к каталогу с JSON-файлами
CONTENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'content')

def load_json_data(filepath: str) -> list:
    """
    Загружает данные из JSON-файла.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {filepath}")
        return []
    except json.JSONDecodeError:
        print(f"Ошибка: Некорректный JSON-формат в файле {filepath}")
        return []

def initialize_regions(db: Session):
    """
    Загружает данные о регионах из JSON и добавляет их в БД.
    """
    regions_filepath = os.path.join(CONTENT_DIR, 'regions.json')
    regions_data = load_json_data(regions_filepath)
    if not regions_data:
        return

    print("Загрузка регионов...")
    for region_item in regions_data:
        name = region_item.get('name')
        f10_value = region_item.get('f10_value')
        if name and f10_value is not None:
            existing_region = crud.get_region_by_name(db, name)
            if not existing_region:
                crud.create_region(db, name, f10_value)
                print(f"  Добавлен регион: {name}")
            # else:
                # print(f"  Регион '{name}' уже существует.")
        else:
            print(f"  Пропущен некорректный элемент региона: {region_item}")
    db.commit() # Коммит всех изменений
    print("Загрузка регионов завершена.")

def initialize_skills(db: Session):
    """
    Загружает данные о навыках из JSON и добавляет их в БД.
    """
    skills_filepath = os.path.join(CONTENT_DIR, 'skills.json')
    skills_data = load_json_data(skills_filepath)
    if not skills_data:
        return

    print("Загрузка навыков...")
    for skill_item in skills_data:
        name = skill_item.get('name')
        description = skill_item.get('description')
        if name:
            existing_skill = crud.get_skill_by_name(db, name)
            if not existing_skill:
                crud.create_skill(db, name, description)
                print(f"  Добавлен навык: {name}")
            # else:
                # print(f"  Навык '{name}' уже существует.")
        else:
            print(f"  Пропущен некорректный элемент навыка: {skill_item}")
    db.commit()
    print("Загрузка навыков завершена.")

def initialize_interests(db: Session):
    """
    Загружает данные об интересах из JSON и добавляет их в БД.
    """
    interests_filepath = os.path.join(CONTENT_DIR, 'interests.json')
    interests_data = load_json_data(interests_filepath)
    if not interests_data:
        return

    print("Загрузка интересов...")
    for interest_item in interests_data:
        name = interest_item.get('name')
        if name:
            existing_interest = crud.get_interest_by_name(db, name)
            if not existing_interest:
                crud.create_interest(db, name)
                print(f"  Добавлен интерес: {name}")
            # else:
                # print(f"  Интерес '{name}' уже существует.")
        else:
            print(f"  Пропущен некорректный элемент интереса: {interest_item}")
    db.commit()
    print("Загрузка интересов завершена.")

def initialize_professions(db: Session):
    """
    Загружает данные о профессиях из JSON и добавляет их в БД.
    """
    professions_filepath = os.path.join(CONTENT_DIR, 'professions.json')
    professions_data = load_json_data(professions_filepath)
    if not professions_data:
        return

    print("Загрузка профессий...")
    for profession_item in professions_data:
        name = profession_item.get('name')
        if name:
            existing_profession = crud.get_profession_by_name(db, name)
            if not existing_profession:
                # Создаем словарь только с нужными полями для передачи в crud.create_profession
                # Убедитесь, что все поля из JSON соответствуют вашей модели Profession
                profession_data = {
                    k: v for k, v in profession_item.items() if k in models.Profession.__table__.columns
                }
                crud.create_profession(db, profession_data)
                print(f"  Добавлена профессия: {name}")
            # else:
                # print(f"  Профессия '{name}' уже существует.")
        else:
            print(f"  Пропущен некорректный элемент профессии: {profession_item}")
    db.commit()
    print("Загрузка профессий завершена.")

def initialize_income_methods(db: Session):
    """
    Загружает данные о способах дохода из JSON и добавляет их в БД.
    """
    methods_filepath = os.path.join(CONTENT_DIR, 'income_methods.json')
    methods_data = load_json_data(methods_filepath)
    if not methods_data:
        return

    print("Загрузка способов дохода...")
    for method_item in methods_data:
        name = method_item.get('name')
        if name:
            existing_method = crud.get_income_method_by_name(db, name)
            if not existing_method:
                method_data = {
                    k: v for k, v in method_item.items() if k in models.IncomeMethod.__table__.columns
                }
                crud.create_income_method(db, method_data)
                print(f"  Добавлен способ дохода: {name}")
            # else:
                # print(f"  Способ дохода '{name}' уже существует.")
        else:
            print(f"  Пропущен некорректный элемент способа дохода: {method_item}")
    db.commit()
    print("Загрузка способов дохода завершена.")


def initialize_career_paths(db: Session):
    """
    Загружает данные о способах продвижения по должности из JSON и добавляет их в БД.
    """
    paths_filepath = os.path.join(CONTENT_DIR, 'career_paths.json')
    paths_data = load_json_data(paths_filepath)
    if not paths_data:
        return

    print("Загрузка способов должности...")
    for path_item in paths_data:
        name = path_item.get('name')
        skill_name = path_item.get('skill_name')  # Получаем имя навыка из JSON

        if name:
            existing_path = crud.get_career_path_by_name(db, name)
            if not existing_path:
                skill_id = None
                if skill_name:
                    skill = crud.get_skill_by_name(db, skill_name)
                    if skill:
                        skill_id = skill.id
                    else:
                        print(
                            f"  Внимание: Навык '{skill_name}' для способа '{name}' не найден в БД. Способ будет добавлен без привязки к навыку.")

                path_data = {
                    k: v for k, v in path_item.items() if k in models.CareerPath.__table__.columns
                }
                # Добавляем skill_id в данные для создания, если он был найден
                if skill_id is not None:
                    path_data['skill_id'] = skill_id

                crud.create_career_path(db, path_data)
                print(f"  Добавлен способ должности: {name} (связан с навыком: {skill_name or 'нет'})")
            # else:
            # print(f"  Способ должности '{name}' уже существует.")
        else:
            print(f"  Пропущен некорректный элемент способа должности: {path_item}")
    db.commit()
    print("Загрузка способов должности завершена.")


def initialize_all_data():
    """
    Основная функция для инициализации всех данных в БД.
    Создает таблицы, если они не существуют, и загружает начальные данные.
    """
    # Убедимся, что таблицы созданы перед загрузкой данных
    print("Проверка/создание таблиц перед загрузкой данных...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы готовы.")

    db = SessionLocal()
    try:
        initialize_regions(db)
        initialize_skills(db)
        initialize_interests(db)
        initialize_professions(db)
        initialize_income_methods(db)
        initialize_career_paths(db)
        # Здесь также можно добавить инициализацию ProfessionInterest и ProfessionRequirement,
        # если будут соответствующие JSON-файлы.
    except Exception as e:
        print(f"Произошла ошибка при загрузке данных: {e}")
        db.rollback() # Откатываем все изменения в случае ошибки
    finally:
        db.close() # Всегда закрываем сессию

if __name__ == "__main__":
    print("Начало процесса инициализации данных...")
    initialize_all_data()
    print("Инициализация данных завершена.")