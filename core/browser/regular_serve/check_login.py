from time import sleep

from playwright._impl._errors import TimeoutError, Error
from playwright.sync_api import Page
from pywinauto import Desktop, timings

from utils._logger import CustomLogger

from ..base import BaseBrowserError, BasePage, handle_critical_error, handle_browser_error
from ..config_words import WORDS


class CheckLogin(BasePage):
    """Проверка авторизации пользователя"""

    def __init__(self, page: Page, user_name: str, logger: CustomLogger, logger_path: str) -> None:
        """Инициализация параметров

        Args:
            page (Page): Объект страницы в браузере.
            user_name (str): Имя пользователя, например, Солонарь_Анастасия
            logger (CustomLogger): Объект логгера.
            logger_path (str): Путь до файла логгера.
        """

        super().__init__(page)
        self.user_name = user_name.split("_")[0]

        self.logger = logger
        self.logger_path = logger_path

    # ✅
    def _user_is_authorized_or_not_authorized(self) -> bool:
        """Проверка авторизации пользователя.

        Returns:
            bool: Возвращает 'True', если пользователь залогинен, иначе возвращает 'False'
        """

        self.logger.info(f"Провожу проверку авторизации пользователя \"{self.user_name.title()}\"...")

        try:
            # Проверка: Результат либо ФИО пользователя на сайте, либо ошибка (ошибка = вход)
            self.page.reload()
            self.page.locator("#profile-link a").first.inner_text(timeout=2_000).split()[0].lower().title()
            self.logger.info(f"Пользователь \"{self.user_name.title()}\" уже авторизован на сайте!")
            return True

        except (TimeoutError, Error):
            self.logger.info(f"Пользователь \"{self.user_name.title()}\" не авторизован на сайте!")
            return False

        except Exception as ex:
            handle_critical_error(
                logger=self.logger,
                logger_path=self.logger_path,
                error_message=f"Произошла непредвиденная ошибка при проверки авторизации пользователя \"{self.user_name}\"!",
                exception=ex,
                page=self.page,
                user_name=self.user_name
            )

    # ✅
    def _click_login_button(self) -> None:
        """Нажимает на кнопку 'Вход' на главной странице ГАСП."""
        self.logger.info(f"Нажимаю на кнопку {WORDS['Кнопка \'Вход\' на главной странице']!r} на главной странице ГАСП")

        try:
            login_button = self.page.get_by_role("link", name=WORDS["Кнопка 'Вход' на главной странице"])
            login_button.first.click(timeout=2_000)
            sleep(1)
            self.logger.info("Успешно нажал на кнопку!")

        except (TimeoutError, Error):
            handle_browser_error(
                logger=self.logger,
                error_message=f"Не смог найти кнопку {WORDS['Кнопка \'Вход\' на главной странице']!r} на главной странице!",
                page=self.page,
                user_name=self.user_name
            )

    # ✅
    def _checkbox_agree(self) -> bool:
        """Проставление чекбокса.
        Чекбокс ставится сюда:
            Я ознакомился(ась) с «Пользовательским соглашением» и согласен(на) на обработку персональных данных.
        
        Returns:
            bool: True если чекбокс был успешно установлен
        """
        self.logger.info("Ставлю галочку на 'Пользовательское соглашение'")

        try:
            self.page.locator("#iAgree").set_checked(True, timeout=5_000)
            self.logger.info("Успешно проставил галочку!")
            return True
        except Exception as ex:
            handle_browser_error(
                logger=self.logger,
                error_message=f"Не смог найти кнопку {WORDS['Кнопка \'Вход\' на главной странице']!r} на главной странице!",
                page=self.page,
                exception=ex,
                user_name=self.user_name
            )

    # ✅
    def _click_login_button_on_authorization_page(self):
        """Нажатие на кнопку 'Войти'
        Данная кнопка находится на странице 'Авторизация пользователя'
        """
        self.logger.info(f"Нажимаю на кнопу {WORDS['Кнопка \'Войти\' на странице \'Авторизация пользователя\'']} на странице 'Авторизация пользователя'")

        try:
            login_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Войти' на странице 'Авторизация пользователя'"])
            login_button.first.click(timeout=2_000)
            self.logger.info("Успешно нажал на кнопку!")

        except (TimeoutError, Error):
            handle_browser_error(
                logger=self.logger,
                error_message=f"Не смог найти кнопку {WORDS['Кнопка \'Войти\' на странице \'Авторизация пользователя\'']!r} на странице 'Авторизация пользователя'",
                page=self.page,
                user_name=self.user_name
            )

    # ✅
    def _click_button_electronic_signature(self):
        """Нажатие на копку 'Эл. подпись'
        Данная копка находится и прожимается на сайте 'ГосУслуг'
        """
        self.logger.info("Нажимаю на кнопку 'Эл. подпись' на сайте 'ГосУслуг'")

        try:
            electronic_signature_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Эл. подпись' на главной странице 'ГосУслуг'"])
            electronic_signature_button.first.click(timeout=5_000)
            return True

        except (TimeoutError, Error):
            handle_browser_error(
                logger=self.logger,
                error_message=f"Не смог найти кнопку \"{WORDS["Кнопка 'Эл. подпись' на главной странице 'ГосУслуг'"]}\" на сайте \"ГосУслуг\"",
                page=self.page,
                user_name=self.user_name
            )

    # ✅
    def _click_button_continue(self):
        """Нажатие на копку 'Продолжить'
        Данная копка находится и прожимается на сайте 'ГосУслуг'
        """
        self.logger.info("Нажимаю на кнопку 'Продолжить' на сайте 'ГосУслуг'")

        try:
            continue_button = self.page.get_by_role("button", name=WORDS["Кнопка Продолжить на странице 'ГосУслуг'"])
            continue_button.first.click(timeout=5_000)

        except (TimeoutError, Error):
            handle_browser_error(
                logger=self.logger,
                error_message=f"Не смог найти кнопку \"{WORDS["Кнопка Продолжить на странице 'ГосУслуг'"]}\" на сайте \"ГосУслуг\"",
                page=self.page,
                user_name=self.user_name
            )

    # ✅
    def _certificate_selection(self) -> bool:
        """Выбор сертификата пользователя на сайте 'ГосУслуг'
        
        Returns:
            bool: True если сертификат был успешно выбран
        """
        self.logger.info(f"Начинаю выбирать сертификат для пользователя {self.user_name.title()!r}")
        s = self.user_name.casefold()
        cards = self.page.locator("button.eds-card")
        
        try:
            cards.first.wait_for(state="visible", timeout=5_000)
        except (TimeoutError, Error):
            handle_browser_error(
                logger=self.logger,
                error_message=f"Не смог найти сертификаты на сайте \"ГосУслуг\"",
                page=self.page,
                user_name=self.user_name
            )

        idx = cards.evaluate_all(
            "(els, s) => els.findIndex(el => el.innerText.replace('\\u00A0',' ').toLowerCase().includes(s))",
            s
        )
        
        if idx == -1:
            handle_browser_error(
                logger=self.logger,
                error_message=f"Не смог найти сертификат пользователя на сайте \"ГосУслуг\"",
                page=self.page,
                user_name=self.user_name
            )

        cards.nth(idx).scroll_into_view_if_needed()
        cards.nth(idx).click(timeout=5_000)

    def _desktop_gosplugin(self):
        """GUI плагин от ГосУслуг (вводит пароль и нажимает 'ок')
        """
        try:
            try:
                dlg_license = Desktop(backend="uia").window(title="Уведомление - КриптоПро CSP")
                dlg_license.wait("visible", timeout=10)
                dlg_license.child_window(title="ОК", control_type="Button").click_input()
            except timings.TimeoutError:
                self.logger.info("Уведомления об окончании действия программы не найдено!")
            dlg = Desktop(backend="uia").window(title="Госплагин")
            dlg.wait("visible", timeout=10)
            dlg.set_focus()
            dlg.child_window(control_type="Edit").set_edit_text("12345678")
            try:
                dlg.child_window(control_type="CheckBox").click_input()
            except Exception:
                pass
            dlg.child_window(title="OK", control_type="Button").click_input()
        except Exception as ex:
            handle_browser_error(
                logger=self.logger,
                error_message="Возникла непредвиденная проблема с плагином ГосУслуг!",
                page=self.page,
                exception=ex,
                user_name=self.user_name
            )

    def start_check(self) -> bool:
        """Порядок запуска методов.
        
        Returns:
            bool: True если авторизация прошла успешно, иначе False.
        """
        _step = 0
        #TODO:здесь исправить количество попыток входа
        _attempt = 20
        while _step <= _attempt:

            if _step + 1 == _attempt:
                handle_critical_error(
                    logger=self.logger,
                    logger_path=self.logger_path,
                    error_message=f"Не смог войти на ГАСП спустя \"{_step}\" попыток! Проверьте работу робота.",
                    page=self.page,
                    user_name=self.user_name
                )
            
            try:
                try:
                    self.page.goto("https://ej.sudrf.ru/")
                except (TimeoutError, Error):
                    raise BaseBrowserError

                if self._user_is_authorized_or_not_authorized():
                    return True

                self._click_login_button()
                self._checkbox_agree()
                self._click_login_button_on_authorization_page()
                self._click_button_electronic_signature()
                self._click_button_continue()
                self._certificate_selection()
                self._desktop_gosplugin()

                if self._user_is_authorized_or_not_authorized():
                    return True

            except BaseBrowserError:
                _step += 1
                sleep(30)
                continue

