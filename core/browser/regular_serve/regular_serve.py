import shutil
import time
from pathlib import Path
from time import sleep

from playwright._impl._errors import Error, TimeoutError
from playwright.sync_api import Page

from config import PATH_TO_APPLICANTS_DETAILS
from database import CourtActions
from models.client.simple_clients import ClientData
from models.database import db_models
from utils import get_data_from_toml, is_similar
from utils._logger import CustomLogger

from ..base import BaseBrowserError, BasePage
from ..base.error_handler import handle_browser_error
from ..config_words import WORDS
from .cleaning_drafts import CleaningDrafts

APPS_DIR = "Приложения"
REGION_EXCEPTIONS = ["кемеровская"]


class RegularServe(BasePage):
    """Подача документов"""

    def __init__(self,
                 page: Page,
                 path_to_packages_dir: str | Path,
                 user_name: str,
                 logger: CustomLogger,
                 logger_path: str
                 ) -> None:
        """Инициализация параметров.

        Args:
            page (Page): Объект страницы в браузере.
            path_to_packages_dir (str | Path): Путь до директории 'Пакеты'.
            user_name (str): Имя пользователя, например, Солонарь_Анастасия
            logger (CustomLogger): Объект логгера.
            logger_path (str): Путь до файла логгера.
        """

        super().__init__(page)
        self.path_to_packages_dir = Path(path_to_packages_dir)
        self.user_name = user_name
        self.client = None

        self.logger = logger
        self.logger_path = logger_path

        self.data_applicant: dict = get_data_from_toml(
            path_to_toml_file=PATH_TO_APPLICANTS_DETAILS,
            logger=self.logger,
            logger_path=self.logger_path
            )[self.path_to_packages_dir.parent.name]

    def _get_clients(self) -> dict[list]:
        """Получение данных о клиенте."""
        return CourtActions().get_actions(
            owner=self.user_name,
            status=db_models.Status.DOCS_FORMED
        )

    def _click_submit_appeal(self) -> None:
        """Процесс 'Подать обращение' на главной странице ГАСП"""

        self.logger.info("Хочу подать обращение...")

        def _click_button():
            """Нажатие на кнопку 'Подать обращение'"""
            _step = 0
            _attempt = 5
            while _attempt > _step:
                _step += 1

                if _step + 1 == _attempt:
                    handle_browser_error(
                        logger=self.logger,
                        error_message=f"Не смог перейти на создание обращения уже \"{_step}\" раз!",
                        page=self.page,
                        user_name=self.user_name
                    )

                try:
                    # Кнопка 'Подать обращение' в верху страницы
                    login_button = self.page.get_by_role("link", name=WORDS["Кнопка 'Подать обращение' на главной странице ГАСП"])
                    login_button.first.click(timeout=10_000)

                    # Секция 'Гражданское судопроизводство' и кнопка 'Подать обращение'
                    section = self.page.locator("div.mainpage-service").filter(
                        has = self.page.get_by_role("heading", name="Гражданское судопроизводство")
                    )
                    section.get_by_role(
                        "link", name=WORDS["Кнопка 'Подать обращение' на странице, где есть 'Гражданское судопроизводство'"]
                        ).click(timeout=10_000)

                    # Ссылка "Заявление о вынесении судебного приказа (дубликата)"
                    application_button = self.page.get_by_role("link", name=WORDS["Кнопка 'Заявление о вынесении судебного приказа (дубликата)' на странице, где есть 'Гражданское судопроизводство'"])
                    application_button.first.click(timeout=10_000)
                    sleep(2)
                    break

                except (TimeoutError, Error):
                    try:
                        self.page.goto("https://ej.sudrf.ru/", timeout=60_000)
                    except (TimeoutError, Error):
                        raise BaseBrowserError
                    continue

        _click_button()
        self.logger.info("Перешёл на создание обращения!")

    def _click_representative_button(self) -> None:
        """Нажимает на кнопку 'Кнопка 'Я являюсь представителем' на странице 'Заявление о вынесении судебного приказа (дубликата)'"""

        self.logger.info("Ввожу данные...")

        def _input_data():
            """Выбор 'Я являюсь представителем' и ввод данных (индекс, адрес) в поля: 'Адрес для направления судебных повесток и иных судебных извещений'"""
            _step = 0
            _attempt = 5
            while _attempt > _step:
                _step += 1

                if _step + 1 == _attempt:
                    handle_browser_error(
                        logger=self.logger,
                        error_message=f"Не смог нажать на \"Я являюсь представителем\" и ввести индекс с адресом уже \"{_step}\" раз!",
                        page=self.page,
                        user_name=self.user_name
                    )

                try:
                    # Кнопка 'Я являюсь представителем' на странице 'Заявление о вынесении судебного приказа (дубликата)'
                    representative_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Я являюсь представителем' на странице 'Заявление о вынесении судебного приказа (дубликата)'"])
                    representative_button.click(timeout=10_000)

                    # Поле для ввода 'Индекса'
                    self.page.locator('#Address_CourtNotices_Index').fill(self.data_applicant.get("index"), timeout=2_000)

                    # Поле для ввода 'Адреса'
                    self.page.locator('#Address_CourtNotices_Address').fill(self.data_applicant.get("legal_address"), timeout=2_000)
                    break

                except (TimeoutError, Error):
                    try:
                        self.page.reload(timeout=60_000)
                    except (TimeoutError, Error):
                        raise BaseBrowserError
                    continue

        _input_data()
        self.logger.info("Успешно выбрал 'Я являюсь представителем' и ввёл данные (индекс, адрес)")

    def _click_document_confirming_authority_button(self) -> None:
        """Нажимает на кнопку 'Добавить файл', рядышком с 'Документ, подтверждающий полномочия' на странице 'Заявление о вынесении судебного приказа (дубликата)'"""
        self.logger.info("Прикрепляю доверенность...")

        power_attorney_file = None
        path_to_apps_dir = self.path_to_packages_dir / self.client.lawsuit_id / APPS_DIR
        for file in path_to_apps_dir.iterdir():
            if "доверенность" in file.name.lower():
                    power_attorney_file = str(file)
                    break

        if power_attorney_file is None:
            handle_browser_error(
                logger=self.logger,
                error_message="Не смог найти \"Доверенность\" в папке \"Приложения\"",
                page=self.page,
                user_name=self.user_name
            )

        def _file_upload():
            """Загрузка Доверенности"""
            _step = 0
            _attempt = 5
            while _attempt > _step:
                _step += 1

                if _step + 1 == _attempt:
                    handle_browser_error(
                        logger=self.logger,
                        error_message=f"Не смог найти кнопку для прикрепления доверенности спустя \"{_step}\" попыток!",
                        page=self.page,
                        user_name=self.user_name
                    )

                try:
                    # Кнопка для 'Документ, подтверждающий полномочия'
                    document_confirming_authority_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Добавить файл' рядышком с 'Документ, подтверждающий полномочия'"])
                    document_confirming_authority_button.first.click(timeout=10_000)

                except (TimeoutError, Error):
                    try:
                        self.page.reload(timeout=60_000)
                    except (TimeoutError, Error):
                        raise BaseBrowserError
                    continue

                def _upload():
                    """Загрузка файла"""
                    __step = 0
                    __attempt = 10
                    while __attempt > __step:
                        __step += 1

                        if __step + 1 == __attempt:
                            handle_browser_error(
                                logger=self.logger,
                                error_message=f"Не смог найти кнопку для прикрепления доверенности спустя \"{_step}\" попыток!",
                                page=self.page,
                                user_name=self.user_name
                            )

                        try:
                            # Загрузка файла (Доверенность)
                            self.page.locator(WORDS["JS для загрузки файла"]).first.set_input_files(power_attorney_file, timeout=10_000)
                            sleep(3)

                            # Кнопка 'Добавить'
                            self.page.get_by_role("button", name=WORDS["Кнопка 'Добавить' в popup окне"]).first.click(timeout=2_000)

                            # Надпись 'Необходимо прикрепить файл'
                            self.page.locator(".help-block").text_content(timeout=2_000).strip()

                            # Кнопка 'Отменить'
                            cancel_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Отменить'в popup окне"])
                            cancel_button.first.click(timeout=10_000)
                            sleep(2)

                            # Кнопка для 'Документ, подтверждающий полномочия'
                            document_confirming_authority_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Добавить файл' рядышком с 'Документ, подтверждающий полномочия'"])
                            document_confirming_authority_button.first.click(timeout=10_000)
                        except (TimeoutError, Error):
                            return True

                if _upload():
                    break

        _file_upload()
        self.logger.info("Доверенность успешно загружена!")

    def _click_applicants_details(self) -> None:
        """Процесс, связанный с кнопкой 'Данные заявителей'"""

        self.logger.info("Ввожу данные заявителя...")

        def _input_data():
            """Данные заявителя"""
            _step = 0
            _attempt = 5
            while _attempt > _step:
                _step += 1

                if _step + 1 == _attempt:
                    handle_browser_error(
                        logger=self.logger,
                        error_message=f"Не смог найти кнопку кнопку 'Добавить заявителя' спустя \"{_step}\" попыток!",
                        page=self.page,
                        user_name=self.user_name
                    )

                try:
                    # Кнопка 'Добавить заявителя'
                    applicants_details_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Данные заявителей'"])
                    applicants_details_button.first.click(timeout=2_000)
                    sleep(2)

                    # Кнопка 'Юридическое лицо'
                    legal_entity_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Юридическое лицо'"])
                    legal_entity_button.first.click(timeout=2_000)

                except (TimeoutError, Error):
                    try:
                        self.page.reload(timeout=60_000)
                    except (TimeoutError, Error):
                        raise BaseBrowserError
                    continue
            
                def _input():
                    """Ввод данных"""
                    try:
                        # Наименование организации
                        self.page.locator('#Company_Name').fill(self.data_applicant.get("name"), timeout=2_000)

                        # Выбор 'Заявитель'
                        self.page.locator('#ProceduralStatus').select_option("Заявитель", timeout=2_000)

                        # ИНН
                        self.page.locator('#Company_INN').fill(self.data_applicant.get("inn"), timeout=2_000)

                        # ОГРН
                        self.page.locator('#Company_OGRN').fill(self.data_applicant.get("ogrn"), timeout=2_000)

                        # КПП
                        self.page.locator('#Company_KPP').fill(self.data_applicant.get("kpp"), timeout=2_000)

                        # Индекс
                        self.page.locator('#Address_Legal_Index').fill(self.data_applicant.get("index"), timeout=2_000)

                        # Адрес
                        self.page.locator('#Address_Legal_Address').fill(self.data_applicant.get("legal_address"), timeout=2_000)

                        # Чекбокс на то, что адресы совпадают
                        self.page.locator('input[type="checkbox"][name="Address_Physical_Same"]').set_checked(True, timeout=2_000)

                        # Email
                        self.page.locator('#Email').last.fill(self.data_applicant.get("email"), timeout=2_000)

                        # Номер телефона
                        self.page.locator('#Phone').last.fill(self.data_applicant.get("phone"), timeout=2_000)

                        # Кнопка 'Сохранить'
                        self.page.get_by_role("button", name=WORDS["Кнопка 'Сохранить' в popup окне"]).first.click(timeout=2_000)
                        sleep(2)
                        return True
                    
                    except (TimeoutError, Error):
                        return False

                if _input():
                    break
                else:
                    try:
                        self.page.reload(timeout=60_000)
                    except (TimeoutError, Error):
                        raise BaseBrowserError
                    sleep(2)

        _input_data()
        self.logger.info("Данные заявителя успешно введены!")

    def _click_participants_details(self) -> None:
        """Процесс, связанный с кнопкой 'Данные участников процесса'"""

        self.logger.info("Ввожу данные участника...")

        def _input_data():
            """Данные участника"""
            _step = 0
            _attempt = 5
            while _attempt > _step:
                _step += 1

                if _step + 1 == _attempt:
                    handle_browser_error(
                        logger=self.logger,
                        error_message=f"Не смог найти кнопку кнопку 'Добавить участника' спустя \"{_step}\" попыток!",
                        page=self.page,
                        user_name=self.user_name
                    )
                try:
                    # Кнопка 'Добавить участника'
                    participants_details_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Добавить участника'"])
                    participants_details_button.first.click(timeout=10_000)

                    # Кнопка 'Физическое лицо'
                    natural_person_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Физическое лицо'"])
                    natural_person_button.first.click(timeout=10_000)
                except (TimeoutError, Error):
                    try:
                        self.page.reload(timeout=60_000)
                    except (TimeoutError, Error):
                        raise BaseBrowserError
                    continue

                def _input():
                    """Ввод данных"""
                    try:
                        # Выбор 'Должник'
                        self.page.locator('#ProceduralStatus').select_option("Должник")

                        # Фамилия
                        surname = self.client.client_father_name if self.client.client_father_name else None
                        if surname:
                            self.page.locator('#Surname').last.fill(self.client.client_father_name, timeout=2_000)

                        # Имя
                        name = self.client.client_first_name if self.client.client_first_name else None
                        if name:
                            self.page.locator('#Name').last.fill(self.client.client_first_name, timeout=2_000)

                        # Отчество
                        patronymic = self.client.client_last_name if self.client.client_last_name else None
                        if patronymic:
                            self.page.locator('#Patronymic').last.fill(self.client.client_last_name, timeout=2_000)

                        # Дата рождения
                        birth_date = self.client.client_last_name if self.client.client_last_name else None
                        if birth_date:
                            self.page.locator('#BirthDate').last.fill(self.client.client_birthday, timeout=2_000)

                        # Гендер
                        if self.client.client_gender == "Ж":
                            self.page.get_by_role("button", name=WORDS["Кнопка пола 'Женский'"]).last.click(timeout=2_000)
                        else:
                            self.page.get_by_role("button", name=WORDS["Кнопка пола 'Мужской'"]).last.click(timeout=2_000)

                        # Место рождения
                        birth_place = self.client.client_birth_place if self.client.client_birth_place else None
                        if birth_place:
                            self.page.locator('#BirthPlace').last.fill(self.client.client_birth_place, timeout=2_000)

                        # Индекс регистрации
                        address_permanent_index = self.client.client_registration_index if self.client.client_registration_index else None
                        if address_permanent_index:
                            self.page.locator('#Address_Permanent_Index').last.fill(self.client.client_registration_index, timeout=2_000)

                        # Фактический индекс
                        address_actual_index = self.client.client_actual_index if self.client.client_actual_index else None
                        if address_actual_index:
                            self.page.locator('#Address_Actual_Index').last.fill(self.client.client_actual_index, timeout=2_000)

                        # Адрес регистрации
                        address_permanent_address = self.client.client_reg_address if self.client.client_reg_address else None
                        if address_permanent_address:
                            self.page.locator('#Address_Permanent_Address').last.fill(self.client.client_reg_address, timeout=2_000)

                        # Фактический адрес
                        address_actual_address = self.client.client_actual_address if self.client.client_actual_address else None
                        if address_actual_address:
                            self.page.locator('#Address_Actual_Address').last.fill(self.client.client_actual_address, timeout=2_000)

                        # СНИЛС
                        snils = self.client.client_snils if self.client.client_snils else None
                        if snils:
                            self.page.locator('#Snils').last.fill(self.client.client_snils, timeout=2_000)

                        # ИНН
                        inn = self.client.client_inn if self.client.client_inn else None
                        if inn:
                            self.page.locator('#INN').last.fill(self.client.client_inn if self.client.client_inn else None, timeout=2_000)

                        # Выбор паспорта
                        self.page.locator('#Type').last.select_option("Паспорт гражданина Российской Федерации", timeout=2_000)

                        # Серия паспорта
                        series = self.client.client_series if self.client.client_series else None
                        if series:
                            self.page.locator('#Series').last.fill(self.client.client_series, timeout=2_000)

                        # Номер паспорта
                        number = self.client.client_number if self.client.client_number else None
                        if number:
                            self.page.locator('#Number').last.fill(self.client.client_number, timeout=2_000)

                        # Дата выдачи паспорта
                        issued_date = self.client.client_issue_on if self.client.client_issue_on else None
                        if issued_date:
                            self.page.locator('#IssueDate').last.fill(self.client.client_issue_on, timeout=2_000)

                        # Кем выдан паспорт
                        issued_by = self.client.client_issue_by if self.client.client_issue_by else None
                        if issued_by:
                            self.page.locator('#IssuedBy').last.fill(self.client.client_issue_by, timeout=2_000)

                        # Код подразделения
                        issued_id = self.client.client_code if self.client.client_code else None
                        if issued_id:
                            self.page.locator('#IssuerId').last.fill(self.client.client_code, timeout=2_000)

                        # Номер телефона
                        phone = self.client.client_phone if self.client.client_phone else None
                        if phone:
                            self.page.locator('#Phone').last.fill(self.client.client_phone, timeout=2_000)

                        # Сохранить
                        self.page.get_by_role("button", name=WORDS["Кнопка 'Сохранить' в popup окне"]).first.click(timeout=2_000)
                        sleep(2)
                        return True
                    
                    except (TimeoutError, Error):
                        return False

                if _input():
                    break
                else:
                    try:
                        self.page.reload(timeout=60_000)
                    except (TimeoutError, Error):
                        raise BaseBrowserError
                    sleep(2)

        _input_data()
        self.logger.info("Данные участника успешно введены!")

    def _court_selection(self):
        """Процесс, связанный с кнопкой 'Выбрать суд'"""

        self.logger.info("Выбираю суд...")

        _step = 0
        _attempt = 5
        while _attempt > _step:
            _step += 1

            if _step + 1 == _attempt:
                handle_browser_error(
                    logger=self.logger,
                    error_message=f"Не смог найти кнопку кнопку 'Выбрать суд' спустя \"{_step}\" попыток!",
                    page=self.page,
                    user_name=self.user_name
                )

            try:
                court_selection_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Выбрать суд'"])
                court_selection_button.first.click(timeout=2_000)
            except (TimeoutError, Error):
                try:
                    self.page.reload()
                except (TimeoutError, Error):
                    raise BaseBrowserError
                continue
            
            # Сбор всех регионов
            try:
                regions = self.page.locator("#currentRegion")
                if regions.count() > 0:
                    options_regions = self.page.locator('#currentRegion option:not([value=""])')
                    list_regions = [options_regions.nth(reg).text_content().strip() for reg in range(options_regions.count())]
                else:
                    continue
            except (TimeoutError, Error):
                try:
                    self.page.reload()
                except (TimeoutError, Error):
                    raise BaseBrowserError
                continue

            client_region = self.client.region_name
            best_region, best_region_sim = None, 0.0

            for region in list_regions:
                _, sim = is_similar(client_region, region)
                
                # Проверяем исключения
                exception_found = False
                for exception in REGION_EXCEPTIONS:
                    if exception in client_region.lower() and exception in region.lower():
                        best_region = region
                        best_region_sim = 1.0
                        exception_found = True
                        break

                if exception_found:
                    break  # выходим из основного цикла, нашли точное совпадение

                # Обычное сравнение
                if sim > best_region_sim:
                    best_region = region
                    best_region_sim = sim

            try:
                if best_region:
                    self.logger.info(f"Выбран регион: {best_region!r} (схожесть: '{best_region_sim:.2f})'")
                    regions.select_option(best_region, timeout=2_000)
                    sleep(5)
                else:
                    continue
            except (TimeoutError, Error):
                try:
                    self.page.reload()
                except (TimeoutError, Error):
                    raise BaseBrowserError
                continue

            try:
                # Выбор судебного органа
                judicial_authorities = self.page.locator("#currentCourt")
                if judicial_authorities.count() > 0:
                    options_judicial_authority = self.page.locator('#currentCourt option:not([value=""])')
                    list_judicial_authority = [options_judicial_authority.nth(reg).text_content().strip() for reg in range(options_judicial_authority.count())]
                else:
                    continue
            except (TimeoutError, Error):
                try:
                    self.page.reload()
                except (TimeoutError, Error):
                    raise BaseBrowserError
                continue

            client_court_name = self.client.court_name
            best_court, best_court_sim = None, 0.0

            for judicial_authority in list_judicial_authority:
                _, sim = is_similar(client_court_name, judicial_authority)

                if sim > best_court_sim:
                    best_court = judicial_authority
                    best_court_sim = sim

            try:
                if best_court and best_court_sim >= 0.7:
                    self.logger.info(f"Выбран судебный орган: {best_court!r} (схожесть: '{best_court_sim:.2f})'")
                    judicial_authorities.select_option(best_court, timeout=2_000)
                    sleep(5)
                else:
                    continue
            except (TimeoutError, Error):
                try:
                    self.page.reload()
                except (TimeoutError, Error):
                    raise BaseBrowserError
                continue

            try:
                self.page.get_by_role("button", name=WORDS["Кнопка 'Сохранить' в popup окне"]).first.click(timeout=2_000)
            except (TimeoutError, Error):
                try:
                    self.page.reload()
                except (TimeoutError, Error):
                    raise BaseBrowserError
                continue
            
            break
        self.logger.info("Суд успешно выбран!")

    def _essence_of_appeal(self):
        """Процесс, связанный с секцией 'Суть обращения'"""

        self.logger.info("Прикрепляю 'Заявление'")

        # Файлы с заявлениями
        path_to_statement = self.path_to_packages_dir / self.client.lawsuit_id / "Заявление.pdf"
        path_to_statement_sig = self.path_to_packages_dir / self.client.lawsuit_id / "Заявление.pdf.sig"

        docs = [path_to_statement, path_to_statement_sig]
        _exists = 0
        for doc in docs:
            if doc.exists():
                _exists += 1

        if _exists == 2:
            _step = 0
            _attempt = 5
            while _attempt > _step:
                _step += 1

                if _step + 1 == _attempt:
                    handle_browser_error(
                        logger=self.logger,
                        error_message=f"Не смог прикрепить 'Заявление' спустя \"{_step}\" попыток!",
                        page=self.page,
                        user_name=self.user_name
                    )
                try:
                    container = self.page.locator(f'h2:has-text("Суть обращения")').locator('xpath=../..')
                    container.locator(f'button:has-text("{WORDS["Кнопка 'Добавить файл'"]}")').click(timeout=2_000)
                except (TimeoutError, Error):
                    try:
                        self.page.reload()
                    except (TimeoutError, Error):
                        raise BaseBrowserError
                    continue
                
                def _upload():
                    """Загрузка файла"""
                    try:
                        self.page.locator(WORDS["JS для загрузки файла"]).first.set_input_files(str(path_to_statement), timeout=2_000)
                        sleep(5)

                        try:
                            # Надпись 'Необходимо прикрепить файл'
                            self.page.locator(".help-block").text_content(timeout=2_000).strip()

                            # Кнопка 'Отменить'
                            cancel_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Отменить'в popup окне"])
                            cancel_button.first.click(timeout=10_000)
                            sleep(2)
                            return False

                        except (TimeoutError, Error):
                            # Если надписи нет 'Необходимо прикрепить файл'
                            try:
                                sleep(5)
                                self.page.locator(WORDS["JS для загрузки файла"]).first.set_input_files(str(path_to_statement_sig), timeout=2_000)

                                try:
                                    self.page.locator('.form-group span:has-text("Файл подписан УКЭП")').text_content(timeout=2_000).strip()
                                    # Если удачно прикреплен файл .sig
                                    return True
                                except (TimeoutError, Error):
                                    # Кнопка 'Отменить'
                                    try:
                                        cancel_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Отменить'в popup окне"])
                                        cancel_button.first.click(timeout=10_000)
                                        sleep(2)
                                        return False
                                    except (TimeoutError, Error):
                                        return False

                            except (TimeoutError, Error):
                                return False

                    except (TimeoutError, Error):
                        return False

                if _upload():
                    self.page.get_by_role("button", name=WORDS["Кнопка 'Добавить' в popup окне"]).first.click()
                    break

                else:
                    try:
                        self.page.reload()
                    except (TimeoutError, Error):
                        raise BaseBrowserError
                    continue
        
        self.logger.info("Заявление успешно прикреплено!")

    def _appendices_to_appeal(self):
        """Процесс, связанный с секцией 'Приложения к обращению'"""

        tmp_val = 0
        self.logger.info("Прикрепляю приложения...")

        # Файлы с в папке "Приложения"
        state_duty = ["Квитанция об уплате госпошлины.pdf", "Квитанция об уплате госпошлины.pdf.sig"]
        amount_of_claims = ["Расчет суммы требований.pdf", "1. Расчет суммы требований.pdf", "Расчет суммы требований.pdf.sig", "1. Расчет суммы требований.pdf.sig"]

        path_to_apps_dir = self.path_to_packages_dir / self.client.lawsuit_id / APPS_DIR
        for file in path_to_apps_dir.iterdir():
            file_name = file.name
            file = str(file)

            if file_name in state_duty or file_name in amount_of_claims:
                if file_name in amount_of_claims:
                    if tmp_val == 1:
                        continue
                    else:
                        file_1 = path_to_apps_dir / "Расчет суммы требований.pdf"
                        file_2 = path_to_apps_dir / "Расчет суммы требований.pdf.sig"

                        if not file_1.exists():
                            file_1 = path_to_apps_dir / "1. Расчет суммы требований.pdf"
                            file_2 = path_to_apps_dir / "1. Расчет суммы требований.pdf.sig"

                        __step = 0
                        __attempt = 10
                        while __attempt > __step:
                            __step += 1

                            if __step + 1 == __attempt:
                                handle_browser_error(
                                    logger=self.logger,
                                    error_message=f"Не смог прикрепить \"Расчет суммы требований\" спустя \"{__step}\" попыток!",
                                    page=self.page,
                                    user_name=self.user_name
                                )
                            
                            try:
                                container = self.page.locator(f'h2:has-text("Приложения к обращению")').locator('xpath=../..')
                                container.locator(f'button:has-text("{WORDS["Кнопка 'Добавить файл'"]}")').click(timeout=30_000)
                            except (TimeoutError, Error):
                                try:
                                    self.page.reload()
                                except (TimeoutError, Error):
                                    raise BaseBrowserError
                                continue

                            def __upload():
                                """Загрузка"""
                                try:
                                    # Загружаем "file_1" = Расчет суммы требований.pdf
                                    self.page.locator(WORDS["JS для загрузки файла"]).first.set_input_files(str(file_1), timeout=30_000)
                                    sleep(2)
                                    # Загружаем "file_2" = Расчет суммы требований.pdf.sig
                                    self.page.locator(WORDS["JS для загрузки файла"]).first.set_input_files(str(file_2), timeout=30_000)
                                    sleep(2)
                                except (TimeoutError, Error):
                                    return False

                                try:
                                    # Надпись 'Файл подписан УКЭП' при приклеплении *.sig файла
                                    self.page.locator('.form-group span:has-text("Файл подписан УКЭП")').text_content(timeout=30_000).strip()
                                    self.page.get_by_role("button", name=WORDS["Кнопка 'Добавить' в popup окне"]).first.click()
                                    return True

                                except (TimeoutError, Error):
                                    # Кнопка 'Отменить'
                                    try:
                                        cancel_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Отменить'в popup окне"])
                                        cancel_button.first.click(timeout=30_000)
                                        sleep(2)
                                        return False
                                    except (TimeoutError, Error):
                                        raise BaseBrowserError
                            
                            if __upload():
                                tmp_val += 1
                                break
                            else:
                                continue
                continue

            else:
                def _upload_data():
                    """Загрузка документа"""
                    _step = 0
                    _attempt = 10
                    while _attempt > _step:
                        _step += 1

                        if _step + 1 == _attempt:
                            handle_browser_error(
                                logger=self.logger,
                                error_message=f"Не смог прикрепить приложения спустя \"{_step}\" попыток!",
                                page=self.page,
                                user_name=self.user_name
                            )

                        try:
                            # Добавить файл
                            container = self.page.locator(f'h2:has-text("Приложения к обращению")').locator('xpath=../..')
                            container.locator(f'button:has-text("{WORDS["Кнопка 'Добавить файл'"]}")').click(timeout=30_000)
                            sleep(2)

                            # Загрузка файла
                            self.page.locator(WORDS["JS для загрузки файла"]).first.set_input_files(str(file), timeout=30_000)
                            sleep(5)

                            # Кнопка 'Добавить'
                            self.page.get_by_role("button", name=WORDS["Кнопка 'Добавить' в popup окне"]).first.click(timeout=30_000)
                            sleep(1)
                        except (TimeoutError, Error):
                            try:
                                self.page.reload(timeout=60_000)
                            except (TimeoutError, Error):
                                continue
                            continue

                        try:
                            # Надпись 'Необходимо прикрепить файл'
                            self.page.locator(".help-block").text_content(timeout=30_000).strip()

                            # Кнопка 'Отменить'
                            cancel_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Отменить'в popup окне"])
                            cancel_button.first.click(timeout=30_000)
                            sleep(2)
                            continue
                        except (TimeoutError, Error):
                            return True

                if _upload_data():
                    continue
        
        self.logger.info("Приложения успешно прикреплены!")


    def _state_duty_receipt(self):
        """Процесс, связанный с секцией 'Уплата госпошлины'"""

        self.logger.info("Устанавливаю чекбокс 'Квитанция об уплате государственной пошлины'")

        try:
            # Чекбокс 'Квитанция об уплате государственной пошлины'
            self.page.locator('input[type="checkbox"][name="Tax_Free"]').first.set_checked(True, timeout=5_000)

            # Кнопка 'Добавить файл'
            container = self.page.locator('h2:has-text("Уплата госпошлины")').locator('xpath=../..')
            container.locator(f'button:has-text("{WORDS["Кнопка 'Добавить файл'"]}")').click()
        except (TimeoutError, Error):
            raise BaseBrowserError

        self.logger.info("Добавляю файл госпошлины...")
        path_to_apps_dir = self.path_to_packages_dir / self.client.lawsuit_id / APPS_DIR
        file_1 = path_to_apps_dir / "Квитанция об уплате госпошлины.pdf"
        file_2 = path_to_apps_dir / "Квитанция об уплате госпошлины.pdf.sig"


        __step = 0
        __attempt = 10
        while __attempt > __step:
            __step += 1

            if __step + 1 == __attempt:
                handle_browser_error(
                    logger=self.logger,
                    error_message=f"Не смог прикрепить \"Расчет суммы требований\" спустя \"{__step}\" попыток!",
                    page=self.page,
                    user_name=self.user_name
                )
            
            def _upload():
                """Загрузка"""
                try:
                    # Загружаем "file_1" = Квитанция об уплате госпошлины.pdf
                    self.page.locator(WORDS["JS для загрузки файла"]).first.set_input_files(str(file_1), timeout=10_000)
                    sleep(2)
                    # Загружаем "file_2" = Квитанция об уплате госпошлины.pdf.sig
                    self.page.locator(WORDS["JS для загрузки файла"]).first.set_input_files(str(file_2), timeout=10_000)
                    sleep(2)
                except (TimeoutError, Error):
                    return False

                try:
                    # Надпись 'Файл подписан УКЭП' при приклеплении *.sig файла
                    self.page.locator('.form-group span:has-text("Файл подписан УКЭП")').text_content(timeout=2_000).strip()
                    self.page.get_by_role("button", name=WORDS["Кнопка 'Добавить' в popup окне"]).first.click()
                    return True

                except (TimeoutError, Error):
                    # Кнопка 'Отменить'
                    try:
                        cancel_button = self.page.get_by_role("button", name=WORDS["Кнопка 'Отменить'в popup окне"])
                        cancel_button.first.click(timeout=10_000)
                        sleep(2)
                        return False
                    except (TimeoutError, Error):
                        raise BaseBrowserError


            if _upload():
                break
            else:
                try:
                    container = self.page.locator('h2:has-text("Уплата госпошлины")').locator('xpath=../..')
                    container.locator(f'button:has-text("{WORDS["Кнопка 'Добавить файл'"]}")').click()
                except (TimeoutError, Error):
                    raise BaseBrowserError
        
        self.logger.info("Файл ГосПошлины успешно прикреплен!")


    # XXX: Отправка обращения, в проде быть аккуратнее, т.к. там появляется номер обращения, который нужно сохранить!
    # Отменить отправку нельзя
    def _create_an_appeal(self):
        """Процесс, связанный с отправкой обращения"""

        _step = 0
        _attempt = 10
        while _attempt > _step:
            _step += 1

            if _step + 1 == _attempt:
                handle_browser_error(
                    logger=self.logger,
                    error_message=f"Не смог отправить итоговое обращение спустя \"{_step}\" попыток!",
                    page=self.page,
                    user_name=self.user_name
                )

            try:
                try:
                    self.page.locator('button:has-text("Сформировать обращение")').click(timeout=10_000)
                    self.page.locator('button:has-text("Сформировать обращение")').click(timeout=10_000)
                except (TimeoutError, Error):
                    pass
                self.page.locator('button:has-text("Отправить")').click(timeout=10_000)

                get_number = self.page.locator("label:has-text(\"Номер\") + .col-sm-6 div").text_content().strip()

                date_and_time_send = self.page.locator("label:has-text(\"Дата и время отправки\") + .col-sm-6 div").text_content().strip()

                logo = self.page.locator("a.nav-logo").first
                logo.click()
                break
            except (TimeoutError, Error):
                try:
                    self.page.reload()
                except (TimeoutError, Error):
                    raise BaseBrowserError
                continue


        CourtActions.change_status(
            lawsuit_id=self.client.lawsuit_id,
            status = db_models.Status.COMPLETED,
            result_number = get_number,
            date_and_time_gus=date_and_time_send
            )
        # TODO: удаляем пакет документов
        shutil.rmtree(str(Path(self.path_to_packages_dir / self.client.lawsuit_id)), ignore_errors=True)

    def start_serving(self):
        """Порядок запуска методов"""

        clients = list(self._get_clients())
        clients_total = len(clients)
        self.logger.info(f"Найдено клиентов для обработки: \"{clients_total}\"")

        for client in clients:
            self.client = ClientData.from_dict(client)
            self.logger.info(f"Работаю с клиентом \"{self.client.lawsuit_id}\"")

            CourtActions.change_status(
                lawsuit_id=self.client.lawsuit_id,
                status=db_models.Status.PROCESSING
            )

            def _submission_documents():
                """Логика подачи"""
                _step = 0
                _attempt = 3
                while _step <= _attempt:

                    if _step + 1 == _attempt:
                        return False

                    cleared = CleaningDrafts(
                        page=self.page,
                        user_name=self.user_name,
                        logger=self.logger,
                        logger_path=self.logger_path
                    ).start_cleaning_drafts()

                    if not cleared:
                        self.logger.warning("Не удалось очистить черновики, пропускаю клиента...")
                        return False
                        
                    success = self._submit_client_documents()
                    
                    if success:
                        return True
                    else:
                        _step += 1
                    
            if _submission_documents():
                continue
            else:
                CourtActions.change_status(
                    lawsuit_id=self.client.lawsuit_id,
                    status=db_models.Status.ERROR,
                    error_msg="Слишком много попыток подать клиента, пропускаю его"
                )
                # TODO: удаляем пакет документов
                shutil.rmtree(str(Path(self.path_to_packages_dir / self.client.lawsuit_id)), ignore_errors=True)
        
        return True

    def _submit_client_documents(self) -> bool:
        """
        Один атомарный проход всех шагов подачи документов.
        Бросает исключение при любой ошибке — это будет перехвачено в ретраях.

        True - всё ок, False - всё не ок
        """
        try:
            self._click_submit_appeal()
            # Представитель + индекс и адрес
            self._click_representative_button()
            # Доверенность
            self._click_document_confirming_authority_button()
            # Данные заявителя
            self._click_applicants_details()
            # Данные участника
            self._click_participants_details()
            # Выбор суда
            self._court_selection()
            # Суть обращения
            self._essence_of_appeal()
            # Приложения
            self._appendices_to_appeal()
            # ГосПошлина
            self._state_duty_receipt()
            # Отправка
            self._create_an_appeal()

            return True
        except BaseBrowserError:
            return False
