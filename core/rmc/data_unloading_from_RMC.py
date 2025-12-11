import os
import re
import zipfile
from pathlib import Path
from typing import Any

import requests

from config import PATH_TO_PUBLIC_FOLDER, PATH_TO_RMC_CONFIG
from database import CourtActions
from models.database import db_models
from notification._rocket_chat import RocketChat
from utils import get_data_from_toml
from utils._logger import CustomLogger

RMC_CONFIG = get_data_from_toml(path_to_toml_file=PATH_TO_RMC_CONFIG)

INN_ORGANIZATIONS = {
    "5407977286": "Интел",
    "7724889891": "Лайм",
    # TODO: Это на будущее
    # "5407264020": "Конга"
}


def sanitize_folder_name(name: str) -> str:
    """Поиск имени проекта.

    Args:
        name (str): Данные для поиска.

    Returns:
        str: Наименование проекта.
    """
    invalid = r'[<>:"/\\|?*]'
    return re.sub(invalid, "_", name.strip())


# XXX: Если запустить функцию, то будут получены данные из РМЦ в виде номеров реестров.
# Повторно эти данные получить нельзя! (При тесте их лучше куда-нибудь записать)
def get_register_numbers(logger: CustomLogger, logger_path: str) -> list[int]:
    """Получение всех номеров реестров в РМЦ.

    Args:
        logger (CustomLogger): Объект логгера.
        logger_path (str): Путь до файла логгера.

    Returns:
        list[int]: Список номеров реестров.
    """
    url = RMC_CONFIG["base_url"] + RMC_CONFIG["endpoints"]["get_registers"]

    logger.info(f"Получаю все номера реестров из РМЦ по ссылке {url!r}")

    try:
        resp = requests.get(url, headers=RMC_CONFIG["headers"], verify=False)
        resp.raise_for_status()
        register_numbers = resp.json().get("printRegisterIds", [])
        logger.info(f"Успешно получил все номера реестров в количестве: {len(register_numbers)!r} шт.")
        logger.info(f"Номера реестров: {register_numbers!r}")
        return register_numbers
    except Exception as ex:
        logger.error(f"Произошла ошибка при получении номеров реестров через метод {url!r}\nОшибка:\n{ex}")
        RocketChat().send_message(
            status="error",
            att=logger_path,
            desc="Файл с логом"
        )
        exit(1)


# XXX: Если запустить функцию, то будет перевод реестра в другой статус в РМЦ, а также получение данных из РМЦ.
# Повторно изменить статус и получить данные нельзя!
# (При тесте, данные лучше куда-нибудь записать)
def start_submission(
        register_number: int,
        logger: CustomLogger,
        logger_path: str
        ) -> dict[str: Any] | None:
    """Перевод реестра в статус 'В процессе подачи' и получение данных из РМЦ по номеру реестра.

    Args:
        register_number (int): Номер реестра.
        logger (CustomLogger): Объект логгера.
        logger_path (str): Путь до файла логгера.

    Returns:
        dict[str: Any] | None: Данные по реестру, либо ничего.
    """
    url = RMC_CONFIG["base_url"] + RMC_CONFIG["endpoints"]["start_submission"]

    logger.info(f"Перевожу реестр № {register_number!r} в статус 'В процессе подачи', используя ссылку: {url!r}")

    try:
        resp = requests.post(url, headers=RMC_CONFIG["headers"], json={"printRegisterId": register_number}, verify=False)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"Получил данные по реестру № {register_number!r} в количестве {len(data["lawsuits"])!r} шт.")
        return data
    except Exception as ex:
        logger.error(f"Произошла ошибка при переводе реестра в статус 'В процессе подачи'! Ошибка:\n{ex}")
        RocketChat().send_message(
            status="error",
            att=logger_path,
            desc="Файл с логом"
        )
        exit(1)


# XXX: Если запустить функцию, то будет скачивание файлов из РМЦ.
# Повторно скачать нельзя, можно только через сотрудника, кто отправлял реестр.
# (При тесте, данные лучше куда-нибудь сохранить)
def download_files(
        url: str,
        out_path: Path | str,
        logger: CustomLogger,
        logger_path: str
        ) -> None:
    """Скачивание файлов из РМЦ.

    Args:
        url (str): URL для скачивания.
        out_path (Path | str): Путь до сохранения результатов.
        logger (CustomLogger): Объект логгера.
        logger_path (str): Путь до файла логгера.
    """
    logger.info("Начинаю загрузку документов из РМЦ...")
    try:
        resp = requests.get(url, headers=RMC_CONFIG["headers"], stream=True, verify=False)
        resp.raise_for_status()
        with open(out_path, "wb") as file:
            for chunk in resp.iter_content(8192):
                if chunk:
                    file.write(chunk)
        logger.info("Данные успешно скачены!")
    except Exception as ex:
        logger.error(f"Произошла ошибка при скачивании файлов из РМЦ!\nОшибка:\n{ex}")
        RocketChat().send_message(
            status="error",
            att=logger_path,
            desc="Файл с логом"
        )
        exit(1)


def extract_archive(
        archive_path: str | Path,
        dest_folder: str | Path,
        logger: CustomLogger,
        logger_path: str
        ) -> None:
    """Распаковка архива, скаченного из РМЦ.

    Args:
        archive_path (str | Path): Путь до архива.
        dest_folder (str | Path): Путь, куда извлекать файлы.
        logger (CustomLogger): Объект логгера.
        logger_path (str): Путь до файла логгера.
    """
    logger.info("Начинаю распаковку архива...")
    try:
        with zipfile.ZipFile(archive_path, "r") as zip:
            zip.extractall(dest_folder)
        os.remove(archive_path)
        logger.info("Архив успешно распакован!")
    except Exception as ex:
        logger.error(f"Произошла ошибка при распаковке архива!\nОшибка:\n{ex}")
        RocketChat().send_message(
            status="error",
            att=logger_path,
            desc="Файл с логом"
        )
        exit(1)


def save_data_in_db(
        data: dict[str: Any],
        register_number: int,
        user_name: str,
        activity_type: str,
        project_name: str
        ) -> None:
    """Сохранение данных в БД.

    Args:
        data (_type_): Словарь с данными.
        register_number (int): Номер реестра
        user_name (str): Имя пользователя, от кого забрали данные в РМЦ.
        activity_type (str): Тип, например, 'Индексация', 'Обычная подача', 'Парсинг ГАСП'
        project_name (str): Наименование проекта, например, 'Лайм', 'Интел'
    """

    lawsuits = data["lawsuits"]

    for lawsuit in lawsuits:
        court = lawsuit.get("court", {})
        client = lawsuit.get("client", {})

        CourtActions.append(
                        rmc_register_num=register_number,
                        owner=user_name,
                        project=project_name,
                        activity_type=activity_type,
                        register_id=register_number,
                        lawsuit_id=lawsuit.get("lawsuitId", ""),
                        court_name=court.get("name", ""),
                        region_name=court.get("regionName", ""),
                        client_last_name=client.get("lastName", ""),
                        client_first_name=client.get("firstName", ""),
                        client_father_name=client.get("fatherName", ""),
                        client_birthday=client.get("birthday", ""),
                        client_gender=client.get("gender", ""),
                        client_birth_place=client.get("birthPlace", ""),
                        client_series=client.get("series", ""),
                        client_number=client.get("number", ""),
                        client_issue_on=client.get("issueOn", ""),
                        client_issue_by=client.get("issueBy", ""),
                        client_code=client.get("code", ""),
                        client_snils=client.get("snils", ""),
                        client_inn=client.get("inn", ""),
                        client_registration_index=client.get("registrationIndex", ""),
                        client_reg_address=client.get("registrationAddressLine", ""),
                        client_actual_index=client.get("actualIndex", ""),
                        client_actual_address=client.get("actualAddressLine", ""),
                        client_phone=client.get("phoneNumber", ""),
                        )

        # TODO: Проверка на обязательные поля
        required_filed = [
            "lastName", "firstName", "fatherName", "birthday", "gender",
            "birthPlace", "registrationIndex", "registrationAddressLine",
            "actualIndex", "actualAddressLine", "series", "number", "issueOn",
            "issueBy", "code"
            ]

        missing_required = [field for field in required_filed if not client.get(field)]

        snils_or_inn = bool(client.get("snils") or client.get("inn"))

        if missing_required:
            CourtActions.change_status(
                lawsuit_id=lawsuit.get("lawsuitId"),
                status = db_models.Status.ERROR_RMC,
                error_msg=f"Нет обязательного поля: {', '.join(missing_required)}"
                )

        if not snils_or_inn:
            CourtActions.change_status(
                lawsuit_id=lawsuit.get("lawsuitId"),
                status = db_models.Status.ERROR_RMC,
                error_msg="Нет обязательного поля: snils or inn"
                )


def get_data_from_RMC(
        user_name: str,
        activity_type: str,
        logger: CustomLogger,
        logger_path: str
        ) -> str:
    """Получение данных из РМЦ.

    Args:
        user_name (str): Имя пользователя, от кого нужно забрать данные из РМЦ.
        activity_type (str): Тип, например, 'Индексация', 'Обычная подача', 'Парсинг ГАСП'
        logger (CustomLogger): Объект логгера.
        logger_path (str): Путь до файла логгера.

    Returns:
        str: Путь до папки с 'Пакетами'.
    """
    final_path_to_folder = None

    if (register_numbers := get_register_numbers(logger=logger, logger_path=logger_path)):

        for register_number in register_numbers:

            logger.info(f"Начинаю работу с реестром № {register_number!r} ...")

            if (data := start_submission(register_number=register_number, logger=logger, logger_path=logger_path)):

                cessionaryCompany = data.get("cessionaryCompany", {})
                inn = cessionaryCompany.get("inn", "")
                folder_name = (
                    INN_ORGANIZATIONS.get(inn)
                    or
                    sanitize_folder_name(
                        cessionaryCompany.get("fullName")
                        or
                        cessionaryCompany.get("shortName")
                        or
                        "Unknown"
                        )
                )

                if data.get("lawsuits"):
                    logger.info("Сохраняю данные в локальную БД...")
                    save_data_in_db(
                        data=data,
                        register_number=register_number,
                        user_name=user_name,
                        activity_type=activity_type,
                        project_name=folder_name
                    )

                url_file = data.get("fileToPrintDocumentUrl")
                if not url_file:
                    logger.warning(f"Нет ссылки на файл у реестра № {register_number!r}") # TODO: Тут ошибка в рокет!
                    continue

                final_path_to_folder = PATH_TO_PUBLIC_FOLDER / user_name / folder_name / "Пакеты"
                path_to_zip_archive = final_path_to_folder / f"register_{register_number}.zip"

                download_files(
                    url=url_file,
                    out_path=path_to_zip_archive,
                    logger=logger,
                    logger_path=logger_path
                    )
                extract_archive(
                    path_to_zip_archive,
                    final_path_to_folder,
                    logger=logger,
                    logger_path=logger_path
                    )
            else:
                continue
        return str(final_path_to_folder) # TODO: Если будет несколько реестров, вернет последний
    else:
        logger.warning("Нет данных в виде 'id' в РМЦ, завершаю работу!")
        exit(1)

    return final_path_to_folder
