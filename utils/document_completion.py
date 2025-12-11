import shutil
import sqlite3
from pathlib import Path
from typing import Iterable

from config import PATH_TO_PUBLIC_FOLDER
from database import CourtActions
from models.database import db_models
from notification._rocket_chat import RocketChat

from ._logger import CustomLogger

# Имёна папок рядом с проектом
FOLDER_ATTACHMENTS_NAME = "Приложения"
FOLDER_STATEMENTS_NAME = "Заявления"
FOLDER_CALCULATIONS_NAME = "Расчеты"
FOLDER_POSTAL_REGISTRY = "Почтовый реестр"

# Итоговые имена файлов в пакете (логика «Лайм» из старого кода)
DEST_STATEMENT_NAME = "Заявление.pdf"
DEST_CALCULATION_NAME = "Расчет суммы требований.pdf"

# Базовая папка с учредительными документами
# FOLDER_FOUNDATION_DOCS_BASE = PATH_TO_PUBLIC_FOLDER / "Учредительные_Документы"


def _get_list_folders(path_to_folder: Path) -> Iterable[Path]:
    """Получение всех папок из директории 'Пакеты'.

    Args:
        path_to_folder (Path): Полный путь до директории 'Пакеты'.

    Returns:
        Iterable[Path]: Список путей.
    """
    if not path_to_folder.exists():
        return []
    return (folder for folder in path_to_folder.iterdir() if folder.is_dir())


def _copy_foundation_docs(
        src_dir: Path,
        dst_dir: Path,
        logger: CustomLogger,
        logger_path: str
        ) -> None:
    """Копирование учредительных документов.

    Args:
        src_dir (Path): Откуда копировать.
        dst_dir (Path): Куда копировать.
        logger (CustomLogger): Объект логгера.
        logger_path (str): Путь до файла логгера.
    """
    dst_dir.mkdir(parents=True, exist_ok=True)
    if not src_dir.exists():
        logger.error(f"Папка с учредительными документами не найдена: {src_dir!r}!")
        RocketChat().send_message(
            status="error",
            att=logger_path,
            desc="Файл с логом"
        )
        exit(1)
    for item in src_dir.iterdir():
        dst_path = dst_dir / item.name
        if item.is_dir():
            if dst_path.exists():
                shutil.rmtree(dst_path)
            shutil.copytree(item, dst_path)
        else:
            shutil.copy2(item, dst_path)


def _handle_lime(
        packages_dir: Path,
        project_dir: Path,
        logger: CustomLogger,
        logger_path: str
        ) -> None:
    """Комплектация пакетов по проекту 'Лайм'

    Args:
        packages_dir (Path): Полный путь до директории 'Пакеты'.
        project_dir (Path): Полный путь до директории с пользователем.
        logger (CustomLogger): Объект логгера.
        logger_path (str): Путь до файла логгера.
    """
    logger.info("Начинаю первичную комплектацию пакетов по проекту \"Лайм\"...")

    statements_dir = project_dir / FOLDER_STATEMENTS_NAME
    calculations_dir = project_dir / FOLDER_CALCULATIONS_NAME
    postal_registry_dir = packages_dir.parent / FOLDER_POSTAL_REGISTRY

    # TODO: Из-за доработки в РМЦ теперь уч. реды. не нужны, они генерируются в РМЦ
    # foundation_docs_dir = FOLDER_FOUNDATION_DOCS_BASE / project_dir.name

    if not statements_dir.exists() or not calculations_dir.exists():
        logger.error("Для проекта \"Лайм\" требуются папки \"Заявления\" и \"Расчеты\" рядом с папкой \"Пакеты\".")
        RocketChat().send_message(
            status="error",
            att=logger_path,
            desc="Файл с логом"
        )
        exit(1)

    for package_dir in _get_list_folders(packages_dir):
        pkg_name = package_dir.name
        statement_src = statements_dir / f"{pkg_name}.pdf"
        calc_src = calculations_dir / f"{pkg_name}.pdf"
        mail_src = postal_registry_dir / f"{pkg_name}.pdf"

        if mail_src.exists():
            logger.info(f"Для пакета № {pkg_name!r} есть почтовый реестр, копирую его...")
            shutil.copyfile(mail_src, package_dir / FOLDER_ATTACHMENTS_NAME / f"{FOLDER_POSTAL_REGISTRY}.pdf")

        if not statement_src.exists() or not calc_src.exists():
            logger.warning(f"Удаление неполной папки: {pkg_name!r}, т.к. нет обязательных файлов (расчет и заявления)!")
            CourtActions.change_status(
                lawsuit_id=pkg_name,
                status = db_models.Status.ERROR,
                error_msg="Не полный пакет документов! (Пакет удалён)"
                )
            shutil.rmtree(package_dir, ignore_errors=True)
            continue

        shutil.copyfile(statement_src, package_dir / DEST_STATEMENT_NAME)
        shutil.copyfile(calc_src, package_dir / DEST_CALCULATION_NAME)

        # TODO: Из-за доработки в РМЦ теперь уч. реды. не нужны, они генерируются в РМЦ
        # attachments_dir = package_dir / FOLDER_ATTACHMENTS_NAME
        # _copy_foundation_docs(
        #     foundation_docs_dir,
        #     attachments_dir,
        #     logger=logger,
        #     logger_path=logger_path
        #     )
        CourtActions.change_status(lawsuit_id=pkg_name, status = db_models.Status.DOCS_ADDED)


def _handle_intel(
        packages_dir: Path,
        project_dir: Path,
        logger: CustomLogger,
        logger_path: str
        ) -> None:
    """Комплектация пакетов по проекту 'Интел'

    Args:
        packages_dir (Path): Полный путь до директории 'Пакеты'.
        project_dir (Path): Полный путь до директории с пользователем.
        logger (CustomLogger): Объект логгера.
        logger_path (str): Путь до файла логгера.
    """
    logger.info("Начинаю первичную комплектацию пакетов по проекту \"Интел\"...")

    # TODO: Из-за доработки в РМЦ теперь уч. реды. не нужны, они генерируются в РМЦ
    # foundation_docs_dir = FOLDER_FOUNDATION_DOCS_BASE / project_dir.name
    statements_dir = project_dir / FOLDER_STATEMENTS_NAME
    calculations_dir = project_dir / FOLDER_CALCULATIONS_NAME

    for package_dir in _get_list_folders(packages_dir):

        attachments_dir = package_dir / FOLDER_ATTACHMENTS_NAME
        if not attachments_dir.exists():
            logger.warning(f"Удаление неполной папки: {package_dir!r}, т.к. нет обязательной папки \"Приложения\"!")
            CourtActions.change_status(
                lawsuit_id=package_dir.name,
                status = db_models.Status.ERROR,
                error_msg="Не полный пакет документов! (Пакет удалён)"
                )
            shutil.rmtree(package_dir, ignore_errors=True)
            continue

        mail_src = package_dir.parent.parent / FOLDER_POSTAL_REGISTRY / f"{package_dir.name}.pdf"

        if mail_src.exists():
            logger.info(f"Для пакета № {package_dir.name!r} есть почтовый реестр, копирую его...")
            shutil.copyfile(mail_src, package_dir / FOLDER_ATTACHMENTS_NAME / f"{FOLDER_POSTAL_REGISTRY}.pdf")

        # TODO: Комплектация как у Лайма
        pkg_name = package_dir.name
        statement_src = statements_dir / f"{pkg_name}.pdf"
        calc_src = calculations_dir / f"{pkg_name}.pdf"

        if statement_src.exists():
            shutil.copy2(statement_src, package_dir / DEST_STATEMENT_NAME)

        if calc_src.exists():
            shutil.copy2(calc_src, package_dir / DEST_CALCULATION_NAME)

        # TODO: Из-за доработки в РМЦ теперь уч. реды. не нужны, они генерируются в РМЦ
        # _copy_foundation_docs(
        #     foundation_docs_dir,
        #     attachments_dir,
        #     logger,
        #     logger_path
        #     )
        CourtActions.change_status(lawsuit_id=package_dir.name, status = db_models.Status.DOCS_ADDED)


def get_lawsuit_id_with_error(owner: str):
    lawsuit_id = []
    
    try:
        with sqlite3.connect(r"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\database\CourtActions.db") as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT lawsuit_id 
            FROM court_actions 
            WHERE status = ? AND owner = ?
            """
            
            cursor.execute(query, (db_models.Status.ERROR_RMC, owner))
            results = cursor.fetchall()
            
            lawsuit_id = [row[0] for row in results]
            
    except sqlite3.Error as e:
        print(f"Ошибка при работе с SQLite: {e}")
    
    return lawsuit_id

def complete_package_documents(
        path_to_folder: str | Path,
        logger: CustomLogger,
        logger_path: str
        ) -> None:
    """Первичная комплектация 'Пакетов'.

    Args:
        path_to_folder (str | Path): Полный путь до директории 'Пакеты'.
        logger (CustomLogger): Объект логгера.
        logger_path (str): Путь до файла логгера.
    """
    packages_dir = Path(path_to_folder)

    project_dir = packages_dir.parent
    project_name = project_dir.name
    owner = project_dir.parent.name

    lawsuit_ids = get_lawsuit_id_with_error(owner=owner)
    if lawsuit_ids:
        for lawsuit_id in lawsuit_ids:
            shutil.rmtree(packages_dir / str(lawsuit_id), ignore_errors=True)

    if project_name == "Лайм":
        _handle_lime(
            packages_dir=packages_dir,
            project_dir = project_dir,
            logger=logger,
            logger_path=logger_path
            )
    elif project_name == "Интел":
        _handle_intel(
            packages_dir,
            project_dir,
            logger=logger,
            logger_path=logger_path
            )
    else:
        logger.warning(f"Неизвестный проект: {project_name!r}")
        RocketChat().send_message(
            status="error",
            att=logger_path,
            desc="Файл с логом"
        )
        exit(1)