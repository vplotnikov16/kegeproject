import random
from datetime import timedelta

from faker import Faker

from app.utils.date_utils import utcnow
from run_in_venv import get_project_root

# Параметры (можно менять)
# количество пользователей
X = 100
# количество задач
Y = 500
# количество вариантов
Z = 150

# Вероятность того, что у пользователя будет вариант (чтобы у некоторых не было)
VARIANT_PROBABILITY = 0.7

# Вероятность наличия отчества у пользователя
MIDDLE_NAME_PROBABILITY = 0.7

# Вероятность наличия источника у задачи/варианта
SOURCE_PROBABILITY = 0.6


def create_users(db, fake):
    from app.models import User

    print(f"Создание {X} пользователей...")
    users = []

    for _ in range(X):
        first_name = fake.first_name()
        last_name = fake.last_name()
        middle_name = fake.middle_name() if random.random() < MIDDLE_NAME_PROBABILITY else None

        # Генерация уникального username
        username = User.generate_username(first_name, last_name, middle_name)

        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            registered_at=utcnow() - timedelta(days=random.randint(0, 365))
        )
        user.set_password('P@ssw0rd')

        db.session.add(user)
        users.append(user)

    db.session.commit()
    print(f"Создано {len(users)} пользователей")

    return users


def create_tasks(db, fake, users):
    from app.models import Task

    # 2. Создание Y задач
    print(f"\nСоздание {Y} задач...")
    tasks = []

    for _ in range(Y):
        # Генерация номера задачи от 1 до 27, но если 19-21, то 19
        number = random.randint(1, 27)
        if 19 <= number <= 21:
            number = 19

        statement_parts = []
        for _ in range(random.randint(3, 8)):
            statement_parts.append(f"<p>{fake.sentence()}</p>")
        statement_html = "".join(statement_parts)

        if random.random() < 0.7:
            answer = str(random.randint(1, 100))
        else:
            answer = fake.word().upper()

        task = Task(
            number=number,
            statement_html=statement_html,
            answer=answer,
            published_at=utcnow() - timedelta(days=random.randint(0, 180)),
            source=fake.sentence() if random.random() < SOURCE_PROBABILITY else None,
            author=random.choice(users) if random.random() < 0.8 else None  # 80% задач с автором
        )

        db.session.add(task)
        tasks.append(task)

    db.session.commit()
    print(f"Создано {len(tasks)} задач")

    return tasks


def create_variants(db, fake, users):
    from app.models import Variant

    print(f"\nСоздание {Z} вариантов...")
    variants = []

    potential_authors = [user for user in users if random.random() < VARIANT_PROBABILITY]

    for _ in range(Z):
        variant = Variant(
            source=fake.sentence() if random.random() < SOURCE_PROBABILITY else None,
            created_at=utcnow() - timedelta(days=random.randint(0, 90)),
            duration=random.choice([14100, 10800, 7200]),  # разная длительность
            author=random.choice(potential_authors) if potential_authors and random.random() < 0.9 else None
        )

        db.session.add(variant)
        variants.append(variant)

    db.session.commit()
    print(f"Создано {len(variants)} вариантов")

    return variants, potential_authors


def link_variants_tasks(db, variants, tasks):
    from app.models import VariantTask

    print("Создание связей вариантов с задачами...")
    variant_tasks_count = 0

    for variant in variants:
        # количество задач в варианте
        tasks_in_variant = random.randint(1, 20)

        available_tasks = tasks.copy()
        random.shuffle(available_tasks)

        selected_tasks = available_tasks[:tasks_in_variant]

        for _, task in enumerate(selected_tasks):
            # Создаем связь вариант-задача
            variant_task = VariantTask(
                variant=variant,
                task=task,
                order=1
            )
            db.session.add(variant_task)
            variant_tasks_count += 1

    db.session.commit()
    print(f"Создано {variant_tasks_count} связей вариантов с задачами")

    return variant_tasks_count


def print_statistics(users, tasks, variants, potential_authors, variant_tasks_count):
    print(f"\n{'=' * 50}")
    print("СТАТИСТИКА:")
    print(f"{'=' * 50}")
    print(f"Всего пользователей: {len(users)}")
    print(f"Пользователей без вариантов: {len([u for u in users if u not in potential_authors])}")
    print(f"Всего задач: {len(tasks)}")

    # Распределение задач по номерам
    task_numbers = {}
    for task in tasks:
        task_numbers[task.number] = task_numbers.get(task.number, 0) + 1

    print("\nРаспределение задач по номерам:")
    for num in sorted(task_numbers.keys()):
        print(f"  Задача #{num}: {task_numbers[num]} шт.")

    print(f"\nВсего вариантов: {len(variants)}")
    print(f"Вариантов без автора: {len([v for v in variants if v.author is None])}")
    print(f"Всего связей вариант-задача: {variant_tasks_count}")
    print(f"Среднее количество задач в варианте: {variant_tasks_count / len(variants):.1f}")
    print(f"{'=' * 50}")
    print("\nТестовые данные успешно созданы!")
    print("\nДоступные тестовые пользователи:")
    for user in users:
        print(f"  Логин: {user.username}, Пароль: P@ssw0rd")


def create_test_data(db):
    fake = Faker('ru_RU')

    users = create_users(db, fake)
    tasks = create_tasks(db, fake, users)
    variants, potential_authors = create_variants(db, fake, users)
    variant_tasks_count = link_variants_tasks(db, variants, tasks)

    print_statistics(
        users=users,
        tasks=tasks,
        variants=variants,
        potential_authors=potential_authors,
        variant_tasks_count=variant_tasks_count
    )


def main():
    import sys

    from app import create_app
    from app.extensions import db

    sys.path.insert(0, str(get_project_root()))

    app = create_app()

    with app.app_context():
        create_test_data(db)


if __name__ == '__main__':
    main()
