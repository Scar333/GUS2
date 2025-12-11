import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_PATH))

from core.browser.base.base import BaseBrowser
from core.browser.base.error_handler import handle_critical_error
from core.browser.regular_serve import RegularServe
from core.rmc.sending_data_to_RMC import send_data_from_rmc
from database.database import CourtActions
from models.database import db_models
from utils._logger import CustomLogger


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description='Restart module')

    parser.add_argument('--owner', type=str, required=True, help='Owner name')
    parser.add_argument('--project', type=str, required=True, help='Project name')
    parser.add_argument('--one_user', type=str, required=False, default=None, help='From one user')

    return parser.parse_args()


def restart_process(
        owner: str,
        project: str,
        one_user: str = None
        ) -> None:

    os.system(f'title {owner}')

    if one_user:
        actions = CourtActions.get_actions(owner=owner, completed_processing=False)
        action_in_processing = [
            action for action in actions if action.get('status') == db_models.Status.PROCESSING
            ]
        for action in action_in_processing:
            CourtActions.change_status(
                lawsuit_id=action['lawsuit_id'], status=db_models.Status.DOCS_FORMED
                )

    date_now = datetime.now().strftime("%d.%m.%Y___%H-%M-%S")
    _logger = CustomLogger(custom_name_log_file=f"{owner}_{date_now}")
    main_logger = _logger.start_initialization()
    main_logger_path = _logger.get_full_path_to_log_file()

    final_path_to_folder = fr"S:\Взаимодействие\ДСВ - ДАР\ГАСП\{owner}\{project}\Пакеты"

    browser = BaseBrowser(owner)

    try:
        regular_serve = RegularServe(
            page=browser.page,
            path_to_packages_dir=final_path_to_folder,
            user_name=owner,
            logger=main_logger,
            logger_path=main_logger_path
        )

        success = regular_serve.start_serving()

        if success:
            main_logger.info("Все документы поданы успешно!")
            send_data_from_rmc(
                user_name=owner,
                logger=main_logger,
                logger_path=main_logger_path
            )
            to_archived = CourtActions._flush_to_archive(owner)
            main_logger.info(f"Переместил и удалил клиентов в размере \"{to_archived}\" шт.")
        else:
            main_logger.error("Не удалось подать все документы")

        return success

    except Exception as ex:
        handle_critical_error(
            logger=main_logger,
            logger_path=main_logger_path,
            error_message="Произошла непредвиденная ошибка!",
            exception=ex,
            page=browser.page,
            user_name=owner
        )

def main():
    """Основная функция для запуска из командной строки"""
    args = parse_arguments()

    restart_process(
        owner=args.owner,
        project=args.project,
        one_user=args.one_user
    )


if __name__ == "__main__":
    main()
