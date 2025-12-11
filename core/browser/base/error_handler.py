"""
Общий модуль для обработки ошибок в браузерных модулях
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import PATH_TO_SCREENSHOTS
from database import CourtActions
from models.client.simple_clients import ClientData
from models.database import db_models
from notification._rocket_chat import RocketChat
from utils._logger import CustomLogger


class BaseBrowserError(Exception):
    """Базовое исключение для всех браузерных модулей"""
    pass


class CriticalBrowserError(BaseBrowserError):
    """Критическое исключение, требующее завершения процесса"""
    pass


class SkipClient(Exception):
    """Пропуск клиента, т.к. каких-то данных не хватает"""
    pass


def skip_client(
        logger: CustomLogger,
        error_message: str,
        client: ClientData
        ) -> None:
    """Пропуск клиента.

    Args:
        logger (CustomLogger): _description_
        error_message (str): _description_
        client (ClientData): _description_

    Raises:
        SkipClient: Ошибка для пропуска.
    """
    logger.info(f"Пропускаю клиента \"{client.lawsuit_id}\" из-за: \"{error_message}\"")
    CourtActions.change_status(
        lawsuit_id=client.lawsuit_id,
        status = db_models.Status.ERROR,
        error_msg=error_message
        )
    raise SkipClient(error_message)

def handle_critical_error(
    logger,
    logger_path: str,
    error_message: str,
    exception: Optional[Exception] = None,
    page=None,
    user_name: str = "Нет данных"
) -> None:
    """Универсальная обработка критических ошибок
    
    Args:
        logger: Объект логгера
        logger_path (str): Путь до файла логгера
        error_message (str): Сообщение об ошибке
        exception (Exception, optional): Исключение для детализации
        page: Объект страницы для скриншота (опционально)
        user_name (str): Имя пользователя для скриншота
    """
    full_error = f"{error_message}\nОшибка:\n{exception}" if exception else error_message
    logger.error(full_error)
    
    # Делаем скриншот если есть страница
    if page:
        pass
        # try:
        #     date_now = datetime.now().strftime("%d.%m.%Y___%H-%M-%S")
        #     page.screenshot(path=fr"{PATH_TO_SCREENSHOTS}\{user_name}__{date_now}.png")
        #     page.close()
        # except Exception as screenshot_error:
        #     logger.warning(f"Не удалось сделать скриншот: {screenshot_error}")
    
    # Отправляем уведомление в RocketChat
    try:
        RocketChat().send_message(
            status="error",
            att=logger_path,
            desc="Файл с логом"
        )
    except Exception as rocket_error:
        logger.warning(f"Не удалось отправить уведомление в RocketChat: {rocket_error}")
    # TODO: Временное автоподнятие
    path_file = Path(logger_path).name
    new_user_name = "_".join(path_file.split("_")[0:2])
    subprocess.Popen(
        [
            fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\venv\Scripts\python.exe",
            fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\core\restart\tmp_restart\update_status.py",
            "--user_name", new_user_name,
            "--status", "error"
        ],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    exit(1)


def handle_browser_error(
    logger,
    error_message: str,
    exception: Optional[Exception] = None,
    page=None,
    user_name: str = "Unknown"
) -> None:
    """Обработка обычных ошибок браузера (не критических)
    
    Args:
        logger: Объект логгера
        error_message (str): Сообщение об ошибке
        exception (Exception, optional): Исключение для детализации
        page: Объект страницы для скриншота (опционально)
        user_name (str): Имя пользователя для скриншота
    """
    full_error = f"{error_message}\nОшибка:\n{exception}" if exception else error_message
    logger.warning(full_error)
    
    # Делаем скриншот если есть страница
    if page:
        pass
        # try:
        #     date_now = datetime.now().strftime("%d.%m.%Y___%H-%M-%S")
        #     page.screenshot(path=fr"{PATH_TO_SCREENSHOTS}\{user_name}__{date_now}.png")
        # except Exception as screenshot_error:
        #     logger.warning(f"Не удалось сделать скриншот: {screenshot_error}")
    
    raise BaseBrowserError(full_error)
