from datetime import datetime, timedelta

from playwright._impl._errors import TimeoutError, Error
from playwright.sync_api import Page

from utils import retry_func
from utils._logger import CustomLogger

from ..base import (BaseBrowserError, BasePage, handle_critical_error, handle_browser_error)
from ..config_words import WORDS
from .check_login import CheckLogin


class CleaningDrafts(BasePage):
    """Очистка черновиков перед подачей"""

    def __init__(self, page: Page, user_name: str, logger: CustomLogger, logger_path: str) -> None:
        """Инициализация параметров.

        Args:
            page (Page): Объект страницы в браузере.
            user_name (str): Имя пользователя, например, Солонарь_Анастасия
            logger (CustomLogger): Объект логгера.
            logger_path (str): Путь до файла логгера.
        """

        super().__init__(page)
        self.user_name = user_name
        
        self.logger = logger
        self.logger_path = logger_path

    def _click_go_to_section(self) -> None:
        """Нажимает на кнопку 'Перейти в раздел' на главной странице ГАСП"""

        self.logger.info(f"Нажимаю на кнопку {WORDS["Кнопка 'Перейти в раздел' на главной странице ГАСП"]!r} на главной странице ГАСП...")

        try:
            go_to_section_button = self.page.get_by_role("link", name=WORDS["Кнопка 'Перейти в раздел' на главной странице ГАСП"])
            go_to_section_button.first.click(timeout=10_000)
            self.logger.info("Успешно нажал на кнопку!")

        except (TimeoutError, Error):
            handle_browser_error(
                logger=self.logger,
                error_message="Не смог найти кнопку на кнопку 'Перейти в раздел' на главной странице ГАСП!",
                page=self.page,
                user_name=self.user_name
            )

    def _date_change(self) -> None:
        """Меняет дату на странице 'Обращения'"""

        self.logger.info("Меняю дату! (Текущий день - 30 дней)")
        try:
            old_date = (datetime.now() - timedelta(days=30)).strftime("%d.%m.%Y")
            date_now = datetime.now().strftime("%d.%m.%Y")

            # Ввод даты "с"
            input_start_date = self.page.locator('#date_start ~ input.form-control[type="text"]')
            input_start_date.fill(old_date, timeout=10_000)

            # Ввод даты "по"
            input_end_date = self.page.locator('#date_end ~ input.form-control[type="text"]')
            input_end_date.fill(date_now, timeout=10_000)

            # Ставит чекбокс на "Показать черновики"
            self.page.locator('input[type="checkbox"][name="showDrafts"]').set_checked(True, timeout=5_000)

            # Нажимает "Найти"
            find_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Найти' на странице 'Обращения'"])
            find_button.first.click()
            self.logger.info("Успешно нажал на кнопку!")

        except (TimeoutError, Error):
            handle_browser_error(
                logger=self.logger,
                error_message="Не смог завершить процесс на странице 'Обращения'",
                page=self.page,
                user_name=self.user_name
            )

    def _delete_requests(self) -> None:
        """Удаление 'Обращений' на странице с 'Обращениями'"""
        
        self.logger.info(f"Нажимаю на кнопку {WORDS["Кнопка 'Удалить' на странице 'Обращения'"]!r} на странице с 'Обращениями'")
        try:
            del_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Удалить' на странице 'Обращения'"])
            del_button.first.click(timeout=30_000)
            del_button.last.click(timeout=10_000)
            self.logger.info("Успешно нажал на кнопку!")
        except (TimeoutError, Error):
            self.logger.warning("Не смог найти кнопку или ее не было!")

    def _click_to_logo(self) -> None:
        """Нажимает на логотип."""

        self.logger.info("Нажимаю на логотип")
        try:
            logo = self.page.locator("a.nav-logo").first
            logo.click()
            self.logger.info("Успешно нажал на логотип!")
        except (TimeoutError, Error):
            handle_browser_error(
                logger=self.logger,
                error_message="Не смог логотип ГАСП!",
                page=self.page,
                user_name=self.user_name
            )

    def start_cleaning_drafts(self):
        """Порядок запуска методов
        
        Returns:
            bool: True если очистка черновиков прошла успешно, False если все попытки исчерпаны
        """
        _step = 0
        _attempt = 15
        while _step <= _attempt:

            if _step + 1 == _attempt:
                handle_critical_error(
                    logger=self.logger,
                    logger_path=self.logger_path,
                    error_message=f"Не смог очистить черновики на ГАСП спустя \"{_step}\" попыток! Проверьте работу робота.",
                    page=self.page,
                    user_name=self.user_name
                )

            # Проверяем авторизацию пользователя
            user_is_authorized = CheckLogin(
                page=self.page,
                user_name=self.user_name,
                logger=self.logger,
                logger_path=self.logger_path
                ).start_check()

            try:
                if user_is_authorized:
                    self.logger.info("Пользователь авторизован, начинаю очистку черновиков...")

                    # Переходим на главную страницу
                    try:
                        self.page.goto("https://ej.sudrf.ru/")
                    except (TimeoutError, Error):
                        raise BaseBrowserError

                    # Выполняем очистку черновиков
                    self._click_go_to_section()
                    self._date_change()
                    self._delete_requests()
                    self._click_to_logo()
                    
                    self.logger.info("Очистка черновиков завершена успешно!")
                    return True
                else:
                    continue

            except BaseBrowserError:
                _step += 1
                continue