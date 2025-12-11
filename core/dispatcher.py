import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_PATH))

from database import CourtActions
from models import ActivityType
from utils import complete_package_documents, signed_files
from utils._logger import CustomLogger

from core.browser.base.base import BaseBrowser
from core.browser.base.error_handler import handle_critical_error
from core.browser.regular_serve import RegularServe
from core.rmc.data_unloading_from_RMC import get_data_from_RMC
from core.rmc.sending_data_to_RMC import send_data_from_rmc


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description='Start module')

    parser.add_argument('--user_name', type=str, required=True, help='Owner name')

    return parser.parse_args()


def process_manager(user_name: str) -> None:
    """Распределение запуска.

    Args:
        user_name (str): Пользователь, например, Солонарь_Анастасия.
    """

    os.system(f'title {user_name}')

    # Логгер
    date_now = datetime.now().strftime("%d.%m.%Y___%H-%M-%S")
    _logger = CustomLogger(
        custom_path_to_folder=fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\logs",
        custom_name_log_file=f"{user_name}_{date_now}"
        )
    main_logger = _logger.start_initialization()
    main_logger_path = _logger.get_full_path_to_log_file()

    main_logger.info("TEST")

    # Скачивание реестра из РМЦ
    try:
        final_path_to_folder = get_data_from_RMC(
            user_name=user_name,
            activity_type=ActivityType.NORMAL,
            logger=main_logger,
            logger_path=main_logger_path
            )

    except Exception as ex:
        handle_critical_error(
            logger=main_logger,
            logger_path=main_logger_path,
            error_message="Произошла ошибка при скачивании данных из РМЦ!",
            exception=ex,
            user_name=user_name
        )


    # Первичная комплектация файлов
    try:
        complete_package_documents(
            path_to_folder=final_path_to_folder,
            logger=main_logger,
            logger_path=main_logger_path
            )

    except Exception as ex:
        handle_critical_error(
            logger=main_logger,
            logger_path=main_logger_path,
            error_message="Произошла непредвиденная ошибка при первичной комплектации документов!",
            exception=ex,
            user_name=user_name
        )


    # Подписание документов
    try:
        signed_files(
            path_to_folder=final_path_to_folder,
            user_name=user_name,
            logger=main_logger
            )

    except Exception as ex:
        handle_critical_error(
            logger=main_logger,
            logger_path=main_logger_path,
            error_message="Произошла непредвиденная ошибка при подписи документов!",
            exception=ex,
            user_name=user_name
        )

    browser = BaseBrowser(user_name)
    try:
        regular_serve = RegularServe(
            page=browser.page,
            path_to_packages_dir=final_path_to_folder,
            user_name=user_name,
            logger=main_logger,
            logger_path=main_logger_path
        )

        success = regular_serve.start_serving()

        if success:
            main_logger.info("Все документы поданы успешно!")
            # Отправка данных в РМЦ # ADD BLOCKER WHILE PARSING IN PROCCESS AFTER CONTINUE
            send_data_from_rmc(
                user_name=user_name,
                logger=main_logger,
                logger_path=main_logger_path
            )

            # Перенос в архивную БД
            to_archived = CourtActions._flush_to_archive(user_name)
            main_logger.info(f"Переместил и удалил клиентов в размере \"{to_archived}\" шт.")

        else:
            main_logger.error("Не удалось подать все документы")

    except Exception as ex:
        handle_critical_error(
            logger=main_logger,
            logger_path=main_logger_path,
            error_message="Произошла непредвиденная ошибка!",
            exception=ex,
            page=browser.page,
            user_name=user_name
        )

    finally:
        _logger.close_logger()


def main():
    """Основная функция для запуска из командной строки"""
    args = parse_arguments()

    process_manager(
        user_name=args.user_name
    )


if __name__ == "__main__":
    main()
