import shutil
from pathlib import Path

from database import CourtActions
from models.database import db_models

from ._logger import CustomLogger


APPS_DIR_NAME = "Приложения"


def is_pdf_or_sig(name_lower: str) -> bool:
    """Возвращает True для .pdf и .sig файлов.

    Args:
        name_lower (str): Наименование файла.

    Returns:
        bool: True, если файл .pdf или .sig, иначе False.
    """
    return name_lower.endswith(".pdf") or name_lower.endswith(".sig")


def checking_application_in_file(name_lower: str) -> bool:
    """Исключает файлы, где в названии есть слово "заявлен" (без учёта регистра).

    Args:
        name_lower (str): Наименование файла.

    Returns:
        bool: True, если есть "заявлен" в файле, иначе Fasle.
    """
    return "заявлен" in name_lower

def get_path_to_application_folder(folder: Path) -> Path:
    """Возвращает путь к подкаталогу "Приложения", создавая его при отсутствии.

    Args:
        folder (Path): Путь до директории с ID клиента в основной директории 'Пакеты'.

    Returns:
        Path: Путь к директории "Приложения".
    """
    apps = folder / APPS_DIR_NAME
    apps.mkdir(exist_ok=True)
    return apps


def unique_path(dst_path: Path) -> Path:
    """Если файл существует, добавляет суффикс "(moved N)" перед расширением."""
    if not dst_path.exists():
        return dst_path
    stem = dst_path.stem
    suffix = dst_path.suffix
    parent = dst_path.parent
    n = 1
    while True:
        candidate = parent / f"{stem} (moved {n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def process_main_folder(path_to_folder: str | Path, logger: CustomLogger) -> None:
    """Переносит PDF/SIG из каждой подпапки в подкаталог "Приложения",
    пропуская файлы, содержащие "заявлен" в имени.
    """

    logger.info("Начинаю процесс переноса всех файлов из каждой подпапки в подкаталог \"Приложения\"...")
    packages_dir = Path(path_to_folder)

    for child_folders in (_folder for _folder in packages_dir.iterdir() if _folder.is_dir()):
        lawsuit_id = child_folders.name
        apps_dir = get_path_to_application_folder(child_folders)

        moved = 0
        kept = 0

        for folder in (_folder for _folder in child_folders.iterdir() if _folder.is_file()):
            name_lower = folder.name.lower()

            if checking_application_in_file(name_lower) and is_pdf_or_sig(name_lower):
                kept += 1
                continue

            if is_pdf_or_sig(name_lower):
                dst = unique_path(apps_dir / folder.name)
                shutil.move(str(folder), str(dst))
                moved += 1
            
        CourtActions.change_status(lawsuit_id=lawsuit_id, status=db_models.Status.DOCS_FORMED)

    logger.info("Завершил процесс переноса всех файлов из каждой подпапки в подкаталог \"Приложения\"!")
