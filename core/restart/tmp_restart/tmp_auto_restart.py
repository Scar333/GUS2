import sqlite3
import subprocess
import time
from datetime import datetime

DB_PATH = fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\core\restart\tmp_restart\user_restart.db"
MAIN_DB_PATH = fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\database\CourtActions.db"


def create_db():
    """Создаёт БД и таблицу, если они не существуют."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_restart (
            user_name TEXT UNIQUE,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()


def monitor_db():
    """Мониторит БД на статус 'error'."""
    while True:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_name, status FROM user_restart WHERE status = 'error'")
        errors = cursor.fetchall()
        if errors:
            print("Пользователи с ошибками:")
            for user, stat in errors:

                subprocess.Popen(
                    [
                        fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\venv\Scripts\python.exe",
                        fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\core\restart\tmp_restart\update_status.py",
                        "--user_name", user,
                        "--status", "ok"
                    ],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )

                subprocess.Popen(
                    [
                        fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\venv\Scripts\python.exe",
                        fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\core\restart\tmp_restart\update_status.py",
                        "--user_name", user,
                        "--main_db", "yes"
                    ],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )

                time.sleep(10)

                conn_2 = sqlite3.connect(MAIN_DB_PATH)
                cursor_2 = conn_2.cursor()
                cursor_2.execute(
                    "SELECT project FROM court_actions WHERE owner = ? LIMIT 1;", (user,)
                )
                try:
                    project = cursor_2.fetchone()[0]
                except Exception as ex:
                    print(f"Произошла ошибка при попытке получения проекта! Ошибка:\n{ex}")
                    conn_2.close()
                    continue
                

                subprocess.Popen(
                    [
                        fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\venv\Scripts\python.exe",
                        fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\core\restart\restart_module.py",
                        "--owner", user,
                        "--project", project
                        ],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )


                print(f"[{datetime.now().strftime("%d.%m.%Y %H:%M")}] - {user}: {stat}")
                time.sleep(60)
        conn.close()
        time.sleep(60)


if __name__ == "__main__":
    create_db()
    monitor_db()
