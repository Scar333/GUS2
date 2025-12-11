# import sqlite3
# import subprocess
# import sys
# import time
# from pathlib import Path

# PROJECT_PATH = Path(__file__).parent.parent.parent
# sys.path.insert(0, str(PROJECT_PATH))

# from database.database import CourtActions
# from models.database import db_models

# DB_PATH = PROJECT_PATH / "database" / "CourtActions.db"
# VENV_PATH = PROJECT_PATH / "venv"
# PYTHON_PATH = VENV_PATH / "Scripts" / "python.exe"
# SCRIPT_PATH = PROJECT_PATH / "core" / "restart" / "restart_module.py"


# def update_owner_status(owner: str):
#     """Обновление статусов в БД.

#     Меняет статусы из "В обработке" на "Пакет документов полностью сформирован".

#     Args:
#         owner (str): Пользователь.
#     """
#     actions = CourtActions.get_actions(owner=owner, completed_processing=False)
#     action_in_processing = [
#         action for action in actions if action.get('status') == db_models.Status.PROCESSING
#         ]
#     for action in action_in_processing:
#         CourtActions.change_status(
#             lawsuit_id=action['lawsuit_id'], status=db_models.Status.DOCS_FORMED
#             )


# def get_owners_and_projects():
#     """Получение пользователей и их проектов"""
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         cursor = conn.cursor()

#         cursor.execute("SELECT DISTINCT owner, project FROM court_actions")

#         owner_project = {}
#         for owner, project in cursor.fetchall():
#             owner_project[owner] = project

#         conn.close()
#         print(f"Всего пользователей: {len(owner_project)}")
#         return owner_project

#     except sqlite3.Error as ex:
#         print(f"Ошибка при получении пользователей: {ex}")
#         raise


# def all_users():
#     owner_project = get_owners_and_projects()

#     if owner_project:
#         for owner, project in owner_project.items():
#             update_owner_status(owner=owner)

#             subprocess.Popen(
#                 [str(PYTHON_PATH), str(SCRIPT_PATH), "--owner", owner, "--project", project],
#                 creationflags=subprocess.CREATE_NEW_CONSOLE
#             )
            
#             print(f"Запущен процесс для пользователя: {owner}")
#             time.sleep(30)
        
#     else:
#         print("Не найдено пользователей для перезапуска!")
    
#     input("___Нажмите Enter для выхода...")
#     sys.exit(0)


# def one_user():
#     user_list = list(db_models.User.__members__.keys())
#     for idx, user in enumerate(user_list, 1):
#         print(f"{idx}) {user}")
    
#     while True:
#         try:
#             user_input = input("Введи номер пользователя: ")
#             choice_num = int(user_input)
            
#             if 1 <= choice_num <= len(user_list):
#                 owner_project = get_owners_and_projects()
#                 user = user_list[choice_num - 1]
#                 user_project = None
#                 for owner, project in owner_project.items():
#                     if owner == user:
#                         user_project = project
#                         break
#                 update_owner_status(owner=owner)

#                 subprocess.Popen(
#                     [str(PYTHON_PATH), str(SCRIPT_PATH), "--owner", owner, "--project", user_project],
#                     creationflags=subprocess.CREATE_NEW_CONSOLE
#                 )
                
#                 print(f"Запущен процесс для пользователя: {owner}")
#                 break
#             else:
#                 print(f"Пожалуйста, введите число от 1 до {len(user_list)}")
                
#         except ValueError:
#             print("Пожалуйста, введите корректное число")


# def restart():
#     print("Необходимо проверить подключения ЭЦП через \"DistKontrolUSB Client\"")
#     print("После проверки необходимо выбрать цифру и нажать\"Enter\"")
#     print("1) Перезапуск подачи по всем пользователям")
#     print("2) Перезапуск подачи по конкретному пользователю")

#     while True:
#         user_input = input("Введите цифру: \"1\" или \"2\": ")
#         if user_input == "1":
#             print("\n")
#             all_users()
#         elif user_input == "2":
#             print("\n")
#             one_user()


# if __name__ == "__main__":
#     restart()

import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict

PROJECT_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_PATH))

from database.database import CourtActions
from models.database import db_models

DB_PATH = PROJECT_PATH / "database" / "CourtActions.db"
VENV_PATH = PROJECT_PATH / "venv"
PYTHON_PATH = VENV_PATH / "Scripts" / "python.exe"
SCRIPT_PATH = PROJECT_PATH / "core" / "restart" / "restart_module.py"


def update_owner_status(owner: str) -> None:
    """Меняет статусы пользователя с 'В обработке' на 'Пакет документов полностью сформирован'"""
    actions = CourtActions.get_actions(owner=owner, completed_processing=False)
    processing_actions = [
        action for action in actions
        if action.get('status') == db_models.Status.PROCESSING
    ]

    for action in processing_actions:
        CourtActions.change_status(
            lawsuit_id=action['lawsuit_id'],
            status=db_models.Status.DOCS_FORMED
        )


def get_all_owners_with_projects() -> Dict[str, str]:
    """Возвращает словарь {owner: project} для всех уникальных пользователей в таблице court_actions."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT owner, project FROM court_actions")
            return {row["owner"]: row["project"] for row in cursor.fetchall()}
    except sqlite3.Error as e:
        print(f"Ошибка подключения к базе данных: {e}")
        raise


def launch_restart_script(owner: str, project: str) -> None:
    """Запускает restart_module.py в отдельном окне для конкретного пользователя."""
    subprocess.Popen(
        [str(PYTHON_PATH), str(SCRIPT_PATH), "--owner", owner, "--project", project],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    print(f"Запущен процесс для пользователя: {owner} (проект: {project})")


def restart_all_users() -> None:
    """Перезапуск для всех пользователей из БД."""
    owners = get_all_owners_with_projects()

    if not owners:
        print("Не найдено ни одного пользователя в БД.")
        return

    print(f"Найдено пользователей: {len(owners)}\n")

    for idx, (owner, project) in enumerate(owners.items(), 1):
        print(f"[{idx}/{len(owners)}] Обрабатывается {owner}...")
        update_owner_status(owner)
        launch_restart_script(owner, project)
        if idx < len(owners):
            time.sleep(30)

    print("\nВсе процессы успешно запущены!")


def restart_one_user() -> None:
    """Перезапуск одного пользователя."""
    available_users = list(db_models.User.__members__.keys())
    if not available_users:
        print("Список пользователей пуст!")
        return

    print("Доступные пользователи:")
    for idx, user in enumerate(available_users, 1):
        print(f"  {idx}) {user}")

    while True:
        try:
            choice = int(input("\nВведите номер пользователя: ")) - 1
            if 0 <= choice < len(available_users):
                selected_owner = available_users[choice]
                break
            print(f"Введите число от 1 до {len(available_users)}")
        except ValueError:
            print("Пожалуйста, введите число")

    owners = get_all_owners_with_projects()
    project = owners.get(selected_owner)

    if not project:
        print(f"Пользователь {selected_owner} не найден в базе court_actions!")
        return

    update_owner_status(selected_owner)
    launch_restart_script(selected_owner, project)
    print(f"\nПроцесс для пользователя {selected_owner} успешно запущен!")


def main_menu() -> None:
    print("=" * 60)
    print("   Перезапуск подачи документов в ГАСП")
    print("=" * 60)
    print("Важно: перед запуском убедитесь, что \"DistKontrolUSB Client\" работает")
    print("и ЭЦП всех нужных пользователей подключены")
    print("и сетевой диск \"S\" доступен.")
    print("-" * 60)
    print("1) Перезапустить подачу для ВСЕХ пользователей")
    print("2) Перезапустить подачу для одного пользователя")
    print("-" * 60)

    while True:
        choice = input("Выберите действие (1 или 2): ").strip()
        if choice == "1":
            print("\nЗапуск для всех пользователей...\n")
            restart_all_users()
            break
        elif choice == "2":
            print()
            restart_one_user()
            break
        else:
            print("Пожалуйста, введите 1 или 2")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nРабота прервана пользователем.")
    except Exception as ex:
        print(f"\nКритическая ошибка: {ex}")
    finally:
        input("\nНажмите Enter для выхода...")