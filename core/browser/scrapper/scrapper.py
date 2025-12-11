from datetime import datetime
from pathlib import Path
import sys

PROJECT_PATH = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_PATH))

from core.browser.base.base import BaseBrowser
from core.browser.regular_serve.check_login import CheckLogin
from utils._logger import CustomLogger


def main():
    """Основная функция для запуска процесса подачи документов"""

    user_name = "Ельчин_Вениамин"

    # Создаем логгер для основного процесса
    date_now = datetime.now().strftime("%d.%m.%Y___%H-%M-%S")
    _logger = CustomLogger(custom_name_log_file=f"{user_name}_{date_now}")
    main_logger = _logger.start_initialization()
    main_logger_path = _logger.get_full_path_to_log_file()

    browser = BaseBrowser(user_name)
    
    try:
        login = CheckLogin(
            page=browser.page,
            user_name=user_name,
            logger=main_logger,
            logger_path=main_logger_path
        )

        is_loging = login.start_check()

        print("DONE")        
    except Exception as ex:
        pass


if __name__ == "__main__":
    main()
