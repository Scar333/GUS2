from pathlib import Path

from playwright.sync_api import Page, sync_playwright


PATH_TO_DIR = Path(__file__).parent.parent.resolve()
# TODO: Инструкция по добавлению плагина -> (вставить описание из конфлюенса)
PATH_TO_GOSPLAGIN_EXTENSION = (PATH_TO_DIR / "extensions" / "GosPlugin").resolve()
PATH_TO_PROFILES = (PATH_TO_DIR / "profiles").resolve()


class BaseBrowser:
    """Базовый класс для работы с браузером"""

    def __init__(self, profile_name: str) -> None:
        """Инициализация параметров.

        Args:
            profile_name (str): Наименование профиля, например, Солонарь_Анастасия.
        """

        user_profile_dir = self.__create_profile(profile_name)

        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch_persistent_context(
            user_data_dir=str(user_profile_dir),
            headless=False,
            args=[
                "--no-default-browser-check",
                "--no-first-run",
                "--disable-infobars",
                f"--disable-extensions-except={PATH_TO_GOSPLAGIN_EXTENSION}",
                f"--load-extension={PATH_TO_GOSPLAGIN_EXTENSION}",
                "--start-maximized",
            ],
            slow_mo=2000
        )

        self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()

        cdp = self.browser.new_cdp_session(self.page)
        win = cdp.send("Browser.getWindowForTarget")
        cdp.send("Browser.setWindowBounds", {
            "windowId": win["windowId"],
            "bounds": {"windowState": "maximized"}
        })

    def __create_profile(self, profile_name: str) -> Path:
        """Создание профиля пользователя.

        Args:
            profile_name (str): Наименование профиля, например, Солонарь_Анастасия.

        Returns:
            Path: Путь до профиля пользователя.
        """

        profile_folder_name = f"profile_{profile_name}"

        user_profile_dir = PATH_TO_PROFILES / profile_folder_name
        user_profile_dir.mkdir(parents=True, exist_ok=True)

        for bad_file in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
            try:
                Path.unlink(user_profile_dir / bad_file)
            except FileNotFoundError:
                pass

        return user_profile_dir

    def close(self) -> None:
        """Закрытие браузера"""

        self.browser.close()
        self._pw.stop()


class BasePage:
    """Базовый класс для работы со страницей"""

    def __init__(self, page: Page) -> None:
        """Инициализация параметров"""

        self.page = page
