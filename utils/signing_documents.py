import subprocess
from pathlib import Path

from config import PATH_TO_CRYPTCP
from database import CourtActions
from models import db_models
from models.database import db_models

from .final_assembly import process_main_folder
from ._logger import CustomLogger


DEFAULT_TIMEOUT = 5
CERT_IN_REGISTRE = ["Солонарь_Анастасия", "Борисевич_Инна", "Герасимчук_Кристина"]

def get_thumbprint(user_name: str, logger: CustomLogger) -> str:
    """Ищет подписанта и его ключ для подписи.

    Args:
        user_name (str): Подписант.

    Returns:
        str: Ключ.
    """
    thumbprint = db_models.User.__members__.get(user_name)
    if not thumbprint:
        logger.error(f"Не смог найти подписанта {user_name!r}")
        # TODO: Тут уведомление + завершение работы
        pass
    return thumbprint.value


def run_cryptcp_sign(
        thumbprint: str,
        path_to_folder: str | Path,
        logger: CustomLogger,
        pin: bool = False
        ) -> None:
    """Подпись файлов в директории (Подписывает все файлы в директории).

    Args:
        thumbprint (str): Код подписи.
        path_to_folder (str | Path): Путь до папки, где лежат файлы для подписи.
        pin (bool): Для сертификатов в реестре.
    """

    path_to_save_sig_file = str(Path(path_to_folder).resolve())

    lawsuit_id = Path(path_to_save_sig_file).name

    command = [str(PATH_TO_CRYPTCP), "-signf"]
    command += ["-dir", path_to_save_sig_file]
    command += ["-uMy", "-thumbprint", thumbprint]
    command += ["*"]
    command.append("-cert")
    command.append("-nochain")
    command += ["-fext", ".sig"]

    if pin:
        command += ["-pin", "12345678"]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='cp866',
            cwd=path_to_save_sig_file,
            timeout=DEFAULT_TIMEOUT
        )
    except subprocess.TimeoutExpired:
        logger.error(f"Таймаут ожидания cryptcp ({DEFAULT_TIMEOUT} с). Процесс убит.")
        # TODO: Завершение работы + уведомление
        CourtActions.change_status(
            lawsuit_id=lawsuit_id,
            status = db_models.Status.ERROR,
            error_msg="Не смог подписать файлы, из-за таймаута!"
            )
    except Exception as ex:
        logger.error(f"Ошибка запуска cryptcp! Ошибка:\n{ex}")
        # TODO: Завершение работы + уведомление
        CourtActions.change_status(
            lawsuit_id=lawsuit_id,
            status = db_models.Status.ERROR,
            error_msg="Не смог подписать файлы, из-за непредвиденной ошибки!"
            )

    try:
        ok = (result.returncode == 0)
        if not ok:
            logger.error(
                "cryptcp завершился с ошибкой, код=%s\nstdout:\n%s\nstderr:\n%s" %
                (result.returncode, result.stdout.strip(), result.stderr.strip())
            )
            CourtActions.change_status(
                lawsuit_id=lawsuit_id,
                status = db_models.Status.ERROR,
                error_msg="Не смог подписать файлы, из-за непредвиденной ошибки!"
                )
            # TODO: Завершение работы + уведомление
        else:
            if result.stdout.strip() or result.stderr.strip():
                # TODO: Удалить принт в проде
                # logger.info("stdout:\n%s\nstderr:\n%s" % (result.stdout.strip(), result.stderr.strip()))
                CourtActions.change_status(lawsuit_id=lawsuit_id, status=db_models.Status.DOCS_SIGNED)
    except UnboundLocalError:
        logger.error("Не смог запустить подпись файлов, т.к. процесс был запущен не через vSphere!")
        CourtActions.change_status(
            lawsuit_id=lawsuit_id,
            status = db_models.Status.ERROR,
            error_msg="Не смог подписать файлы, из-за запуска не из под vSphere!"
            )
    except Exception as ex:
        logger.error(f"Произошла непредвиденная ошибка при подписи файлов, сам процесс не отработал! Ошибка:\n{ex}")
        CourtActions.change_status(
            lawsuit_id=lawsuit_id,
            status = db_models.Status.ERROR,
            error_msg="Не смог подписать файлы, из-за непредвиденной ошибки"
            )


# XXX: Подпись работает только через vSphere, иначе будут ошибки!
# Ошибки влияют только на локальную БД.
def signed_files(path_to_folder: Path | str, user_name: str, logger: CustomLogger):

    path_to_folder = Path(path_to_folder)
    thumbprint = get_thumbprint(user_name=user_name, logger=logger)

    folders = [_folder for _folder in path_to_folder.iterdir() if path_to_folder.is_dir()]

    pin = False
    if user_name in CERT_IN_REGISTRE:
        pin = True

    for folder in folders:
        run_cryptcp_sign(
            thumbprint=thumbprint,
            path_to_folder=folder,
            logger=logger,
            pin=pin
            )
    
    process_main_folder(path_to_folder=path_to_folder, logger=logger)
