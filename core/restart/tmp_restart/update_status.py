import argparse
import sqlite3


DB_PATH = fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\core\restart\tmp_restart\user_restart.db"
MAIN_DB_PATH = fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\database\CourtActions.db"


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description='Update status')

    parser.add_argument('--user_name', type=str, required=True)
    parser.add_argument('--status', type=str, required=False, default=None)
    parser.add_argument('--main_db', type=str, required=False, default=None)

    return parser.parse_args()


def update_status_in_tmp_db(user_name, status):
    """Записывает или обновляет статус для пользователя во временной БД."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_restart (user_name, status)
        VALUES (?, ?)
    ''', (user_name, status))
    conn.commit()
    conn.close()


def update_status_in_main_db(user_name):
    """Обновляет статус для пользователя в основной БД."""
    conn = sqlite3.connect(MAIN_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE court_actions
        SET status = ?
        WHERE owner = ? AND status = ?
    ''', ("Пакет документов полностью сформирован", user_name, "В обработке"))
    conn.commit()
    conn.close()


def main():
    """Основная функция для запуска из командной строки"""
    args = parse_arguments()

    if args.main_db:
        update_status_in_main_db(
            user_name=args.user_name
        )

    else:
        update_status_in_tmp_db(
            user_name=args.user_name,
            status=args.status
        )


if __name__ == "__main__":
    main()
