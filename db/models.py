from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base # Импортируем базовый класс Base из нашего database.py

class User(Base):
    """
    Модель таблицы 'users' для хранения информации о пользователях бота
    и их факторов контекста.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False) # Изменено на BigInteger
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    # Добавляем поле для текущего дохода
    current_income = Column(Integer, default=0, nullable=False)

    # Факторы контекста (F1-F10)
    f1_motivation = Column(Float, default=0.0)
    f2_life_experience = Column(Float, default=0.0)
    f3_persistence = Column(Float, default=0.0)
    f4_flexibility = Column(Float, default=0.0)
    f5_emotional_intelligence = Column(Float, default=0.0)
    f6_health_energy = Column(Float, default=0.0)
    f7_self_perception = Column(Float, default=0.0)
    f8_environment_support = Column(Float, default=0.0)
    f9_resource_access = Column(Float, default=0.0)
    f10_cultural_economic_environment = Column(Float, default=0.0)  # Связь с Region

    # Связи с другими таблицами (пока не созданы, но определяются здесь)
    # region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    # region = relationship("Region")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связь с картами
    income_maps = relationship("IncomeMap", back_populates="user")
    position_maps = relationship("PositionMap", back_populates="user")
    profession_maps = relationship("ProfessionMap", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"


class Region(Base):
    """
    Модель таблицы 'regions' для хранения информации о регионах
    и их факторе контекста F10.
    """
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    f10_value = Column(Float, nullable=False) # Значение фактора F10 для региона

    # users = relationship("User", back_populates="region") # Обратная связь, если раскомментируем в User

    def __repr__(self):
        return f"<Region(id={self.id}, name='{self.name}', f10_value={self.f10_value})>"


class Skill(Base):
    """
    Модель таблицы 'skills' для хранения информации о навыках.
    """
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    # Связи с таблицами требований к профессиям и способам должности
    # profession_requirements = relationship("ProfessionRequirement", back_populates="skill")
    career_paths = relationship("CareerPath", back_populates="skill") # Добавляем обратную связь

    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}')>"


class Interest(Base):
    """
    Модель таблицы 'interests' для хранения информации об интересах.
    """
    __tablename__ = "interests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    # Связь с таблицей ProfessionInterest
    # profession_interests = relationship("ProfessionInterest", back_populates="interest")

    def __repr__(self):
        return f"<Interest(id={self.id}, name='{self.name}')>"


class Profession(Base):
    """
    Модель таблицы 'professions' для хранения информации о профессиях
    и их критериях.
    """
    __tablename__ = "professions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    # Критерии
    competition = Column(Integer)
    demand = Column(Integer)
    trends = Column(Integer)
    salary_entry = Column(Integer)
    salary_average = Column(Integer)
    salary_peak = Column(Integer)
    entry_threshold = Column(Integer)
    learning_time = Column(Integer)
    stress_level = Column(Integer)
    creativity = Column(Integer)
    remote_work = Column(Integer)
    freelance_potential = Column(Integer)
    horizontal_growth = Column(Integer)
    hard_skills_score = Column(Integer) # Обобщенный балл по Hard-навыкам
    soft_skills_score = Column(Integer) # Обобщенный балл по Soft-навыкам

    # Связи
    # requirements = relationship("ProfessionRequirement", back_populates="profession")
    # profession_interests = relationship("ProfessionInterest", back_populates="profession")
    # profession_maps = relationship("ProfessionMap", back_populates="profession")

    def __repr__(self):
        return f"<Profession(id={self.id}, name='{self.name}')>"


class ProfessionInterest(Base):
    """
    Промежуточная модель таблицы 'profession_interests' для связи профессий с интересами.
    """
    __tablename__ = "profession_interests"

    id = Column(Integer, primary_key=True, index=True)
    interest_id = Column(Integer, ForeignKey("interests.id"), nullable=False)
    profession_id = Column(Integer, ForeignKey("professions.id"), nullable=False)
    strength = Column(Integer, default=0) # Сила связи (0-10, например)

    # relationship("Interest", back_populates="profession_interests")
    # relationship("Profession", back_populates="profession_interests")

    def __repr__(self):
        return f"<ProfessionInterest(id={self.id}, interest_id={self.interest_id}, profession_id={self.profession_id})>"


class ProfessionRequirement(Base):
    """
    Модель таблицы 'profession_requirements' для хранения требований к навыкам
    для определенной профессии и уровня.
    """
    __tablename__ = "profession_requirements"

    id = Column(Integer, primary_key=True, index=True)
    profession_id = Column(Integer, ForeignKey("professions.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    level = Column(String, nullable=False) # 'начинающий', 'опытный', 'эксперт'

    # profession = relationship("Profession", back_populates="requirements")
    # skill = relationship("Skill", back_populates="profession_requirements")

    def __repr__(self):
        return f"<ProfessionRequirement(id={self.id}, profession_id={self.profession_id}, skill_id={self.skill_id}, level='{self.level}')>"


class IncomeMethod(Base):
    """
    Модель таблицы 'income_methods' для хранения способов дохода и их критериев.
    """
    __tablename__ = "income_methods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    short_description = Column(String, nullable=True)
    detailed_description = Column(String, nullable=True)

    # Критерии "Способ-Доход"
    speed_of_result = Column(Integer)      # Временные затраты / Скорость результата
    difficulty = Column(Integer)           # Уровень сложности
    financial_investment = Column(Integer)
    income_potential = Column(Integer)
    flexible_schedule = Column(Integer)
    risks = Column(Integer)
    psychological_comfort = Column(Integer)
    impact_on_current_job = Column(Integer)
    hard_skills = Column(Integer)
    soft_skills = Column(Integer)
    geography = Column(Integer)
    special_knowledge = Column(Integer)
    engagement = Column(Integer)

    # Факторы контекста для расчета успеха
    f11_complexity = Column(Float) # Сложность = Сложность
    f12_needed_time = Column(Float) # Необходимое время = Скорость результата

    def __repr__(self):
        return f"<IncomeMethod(id={self.id}, name='{self.name}')>"


class CareerPath(Base): # Способ-Должность
    """
    Модель таблицы 'career_paths' для хранения способов продвижения по должности
    и их критериев.
    """
    __tablename__ = "career_paths"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    short_description = Column(String, nullable=True)
    detailed_description = Column(String, nullable=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True) # Добавляем внешний ключ на навык

    # Критерии "Способ-Должность"
    hours_to_master = Column(Integer)
    flexible_schedule = Column(Integer)
    direct_costs = Column(Integer)
    indirect_costs = Column(Integer)
    material_assimilation = Column(Integer)
    application_speed = Column(Integer)
    geographical_accessibility = Column(Integer)
    technical_requirements = Column(Integer)
    feedback_presence = Column(Integer) # Обратная связь
    feedback_frequency = Column(Integer)
    gamification = Column(Integer)
    goal_alignment = Column(Integer) # Совпадение с целями
    market_demand = Column(Integer)
    probability_of_quitting = Column(Integer)

    # Факторы контекста для расчета успеха
    f11_complexity = Column(Float) # Сложность = Усвоение материала * Скорость применения
    f12_needed_time = Column(Float) # Необходимое время = Часы на освоение

    skill = relationship("Skill", back_populates="career_paths") # Связь с навыком

    def __repr__(self):
        return f"<CareerPath(id={self.id}, name='{self.name}')>"


class IncomeMap(Base):
    """
    Модель таблицы 'income_maps' для хранения "Карты-Доход" пользователя.
    """
    __tablename__ = "income_maps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи с 5 способами дохода и их вероятностями
    # Используем nullable=True, так как карта может быть заполнена не полностью
    method1_id = Column(Integer, ForeignKey("income_methods.id"), nullable=True)
    probability1 = Column(Float, nullable=True)

    method2_id = Column(Integer, ForeignKey("income_methods.id"), nullable=True)
    probability2 = Column(Float, nullable=True)

    method3_id = Column(Integer, ForeignKey("income_methods.id"), nullable=True)
    probability3 = Column(Float, nullable=True)

    method4_id = Column(Integer, ForeignKey("income_methods.id"), nullable=True)
    probability4 = Column(Float, nullable=True)

    method5_id = Column(Integer, ForeignKey("income_methods.id"), nullable=True)
    probability5 = Column(Float, nullable=True)

    user = relationship("User", back_populates="income_maps")
    method1 = relationship("IncomeMethod", foreign_keys=[method1_id])
    method2 = relationship("IncomeMethod", foreign_keys=[method2_id])
    method3 = relationship("IncomeMethod", foreign_keys=[method3_id])
    method4 = relationship("IncomeMethod", foreign_keys=[method4_id])
    method5 = relationship("IncomeMethod", foreign_keys=[method5_id])

    def __repr__(self):
        return f"<IncomeMap(id={self.id}, user_id={self.user_id}, created_at='{self.created_at}')>"


class PositionMap(Base):
    """
    Модель таблицы 'position_maps' для хранения "Карты-Должность" пользователя.
    """
    __tablename__ = "position_maps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи с 5 способами должности и их вероятностями
    path1_id = Column(Integer, ForeignKey("career_paths.id"), nullable=True)
    probability1 = Column(Float, nullable=True)

    path2_id = Column(Integer, ForeignKey("career_paths.id"), nullable=True)
    probability2 = Column(Float, nullable=True)

    path3_id = Column(Integer, ForeignKey("career_paths.id"), nullable=True)
    probability3 = Column(Float, nullable=True)

    path4_id = Column(Integer, ForeignKey("career_paths.id"), nullable=True)
    probability4 = Column(Float, nullable=True)

    path5_id = Column(Integer, ForeignKey("career_paths.id"), nullable=True)
    probability5 = Column(Float, nullable=True)

    user = relationship("User", back_populates="position_maps")
    path1 = relationship("CareerPath", foreign_keys=[path1_id])
    path2 = relationship("CareerPath", foreign_keys=[path2_id])
    path3 = relationship("CareerPath", foreign_keys=[path3_id])
    path4 = relationship("CareerPath", foreign_keys=[path4_id])
    path5 = relationship("CareerPath", foreign_keys=[path5_id])

    def __repr__(self):
        return f"<PositionMap(id={self.id}, user_id={self.user_id}, created_at='{self.created_at}')>"


class ProfessionMap(Base):
    """
    Модель таблицы 'profession_maps' для хранения "Карты-Профессия" пользователя.
    """
    __tablename__ = "profession_maps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи с 5 профессиями
    profession1_id = Column(Integer, ForeignKey("professions.id"), nullable=True)
    profession2_id = Column(Integer, ForeignKey("professions.id"), nullable=True)
    profession3_id = Column(Integer, ForeignKey("professions.id"), nullable=True)
    profession4_id = Column(Integer, ForeignKey("professions.id"), nullable=True)
    profession5_id = Column(Integer, ForeignKey("professions.id"), nullable=True)

    user = relationship("User", back_populates="profession_maps")
    profession1 = relationship("Profession", foreign_keys=[profession1_id])
    profession2 = relationship("Profession", foreign_keys=[profession2_id])
    profession3 = relationship("Profession", foreign_keys=[profession3_id])
    profession4 = relationship("Profession", foreign_keys=[profession4_id])
    profession5 = relationship("Profession", foreign_keys=[profession5_id])

    def __repr__(self):
        return f"<ProfessionMap(id={self.id}, user_id={self.user_id}, created_at='{self.created_at}')>"


# Проверка создания таблиц (можно удалить после первого запуска)
if __name__ == "__main__":
    from db.database import engine
    print("Создание таблиц в базе данных...")
    try:
        # Создает все таблицы, которые наследуются от Base
        Base.metadata.create_all(bind=engine)
        print("Таблицы успешно созданы или уже существуют.")
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")