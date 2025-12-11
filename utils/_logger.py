import logging
import os
from datetime import datetime
from logging import FileHandler, Logger, StreamHandler


class CustomLogger:
    """Кастомный логгер"""

    NAME_FOLDER = "logs"
    LOG_FILE_EXTENSION = ".log"
    DATE_FORMAT = "%d.%m.%Y %H:%M:%S"

    def __init__(
        self,
        custom_path_to_folder: str = None,
        custom_name_log_file: str = None,
        console_output: bool = True
    ) -> None:
        """Инициализация параметров.

        Args:
            custom_path_to_folder (str, optional): Кастомный путь до директории с логами. По умолчанию None.
            custom_name_log_file (str, optional): Кастомное наименование файла с логом. По умолчанию None.
            console_output (bool, optional): Вывод в консоль. По умолчанию True.

        Пример:
            logger = CustomLogger(custom_path_to_folder="/путь/до/директории", custom_name_log_file="Иванов Иван")
        """

        self.current_day = self.__get_current_day()
        self.path_to_folder = self.__get_path_to_folder(custom_path_to_folder)
        self.name_log_file = self.__get_name_file(custom_name_log_file)
        self.full_path_to_log_file = self.get_full_path_to_log_file()

        self.log = logging.getLogger(self.full_path_to_log_file)
        self.log.setLevel(logging.DEBUG)

        self.__create_log_directory()

        self.__setup_file_handler()
        if console_output:
            self.__setup_console_handler()

    @staticmethod
    def __get_current_day() -> str:
        """Получение текущего дня, месяца и года.

        Returns:
            str: Текущая дата в формате "DD.MM.YYYY".

        Пример:
            "03.03.2025"
        """

        return datetime.now().strftime("%d.%m.%Y")

    def __get_path_to_folder(self, custom_path_to_folder: str = None) -> str:
        """Получение пути до директории с логами.

        Args:
            custom_path_to_folder (str, optional): Кастомный путь до директории с логами. По умолчанию None.

        Returns:
            str: Путь до директории.

        Пример:
            "/путь/до/директории/Log"
        """

        base_path = custom_path_to_folder or os.getcwd()

        return os.path.join(base_path, self.NAME_FOLDER)

    def __get_name_file(self, custom_name_log_file: str = None) -> str:
        """Получение имени для лог файла.

        Args:
            custom_name_log_file (str, optional): Кастомное наименование файла с логом. По умолчанию None.

        Returns:
            str: Наименование лог файла.

        Пример:
            "Иванов Иван.log" или "03.03.2025.log"
        """

        log_file_name = custom_name_log_file or self.current_day

        return f"{log_file_name}{self.LOG_FILE_EXTENSION}"

    def get_full_path_to_log_file(self) -> str:
        """Получение полного пути к лог файлу.

        Returns:
            str: Полный путь до лог файла.

        Пример:
            "/путь/до/директории/Log/03.03.2025.log" или "/путь/до/директории/Log/Иванов Иван.log"
        """

        return os.path.join(self.path_to_folder, self.name_log_file)

    def __create_log_directory(self) -> None:
        """Создание директории для логов."""

        if not os.path.exists(self.path_to_folder):
            os.makedirs(self.path_to_folder)


    def __setup_file_handler(self) -> None:
        """Настройка файлового обработчика для логгера."""

        file_formatter = logging.Formatter(
            "%(asctime)s - [%(levelname)s] - [%(filename)s] - %(funcName)s: (%(lineno)d) - %(message)s", 
            datefmt=self.DATE_FORMAT
            )
        file_handler = FileHandler(self.full_path_to_log_file, encoding="UTF-8")
        file_handler.setFormatter(file_formatter)
        self.log.addHandler(file_handler)
        self.file_handler = file_handler

    def __setup_console_handler(self) -> None:
        """Настройка консольного обработчика для логгера."""

        console_formatter = logging.Formatter(
            "[%(asctime)s] - %(message)s", 
            datefmt=self.DATE_FORMAT
            )
        console_handler = StreamHandler()
        console_handler.setFormatter(console_formatter)
        self.log.addHandler(console_handler)
        self.console_handler = console_handler

    def __check_and_update_log_file(self) -> None:
        """Проверка текущей даты и обновление файла лога, если дата изменилась."""

        current_day = self.__get_current_day()

        if current_day != self.current_day:
            self.current_day = current_day
            self.name_log_file = self.__get_name_file()
            self.full_path_to_log_file = self.get_full_path_to_log_file()

            self.log.removeHandler(self.file_handler)
            self.file_handler.close()
            self.__setup_file_handler()
            self.log.addHandler(self.file_handler)

    def start_initialization(self) -> Logger:
        """Запуск логгера"""
        self.__check_and_update_log_file()

        return self.log

    def close_logger(self) -> None:
        """Общее закрытие обработчиков (файл, консоль) и удаление их из логгера."""

        if hasattr(self, "file_handler") and self.file_handler:
            self.file_handler.close()
            self.log.removeHandler(self.file_handler)

        if hasattr(self, "console_handler") and self.console_handler:
            self.console_handler.close()
            self.log.removeHandler(self.console_handler)
