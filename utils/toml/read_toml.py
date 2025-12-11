"""Чтение TOML-конфига и перевода в dict."""

from __future__ import annotations

import subprocess
import time
import tomllib
from pathlib import Path
from typing import Any

from notification._rocket_chat import RocketChat
from utils._logger import CustomLogger


def get_data_from_toml(path_to_toml_file: str | Path, logger: CustomLogger = None, logger_path: str = None) -> dict[str, Any]:
    """Чтение *.toml файла.

    Args:
        path_to_toml_file (str | Path): Путь до *.toml файла.
        logger (CustomLogger): Объект логгера.
        logger_path (str): Путь до файла логгера.

    Returns:
        dict[str, Any]: Словарь с данными, полученный из *.toml файла. 
    """
    count = 0
    max_count = 3
    while True:
        count += 1

        try:
            path_to_file = Path(path_to_toml_file).expanduser()
            with path_to_file.open("rb") as file:
                return tomllib.load(file)
        except Exception as ex:
            if count == max_count:
                if logger:
                    logger.error(
                        f"Произошла ошибка при чтении файла {path_to_toml_file!r}!\n"
                        f"Ошибка: {ex}"
                        "Дальнейшая работа не будет продолжена, т.к. это важный файл!"
                    )
                    RocketChat().send_message(
                        status="error",
                        att=logger_path,
                        desc="Файл с логом"
                        )
                else:
                    print(f"Произошла ошибка при чтении файла {path_to_toml_file!r}!\nОшибка:\n{ex}")

                path_file = Path(logger_path).name
                new_user_name = "_".join(path_file.split("_")[0:2])
                subprocess.Popen(
                    [
                        fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\venv\Scripts\python.exe",
                        fr"C:\Users\gaspravo-crypto-usr\Documents\GAS_Justice\core\restart\tmp_restart\update_status.py",
                        "--user_name", new_user_name,
                        "--status", "error"
                    ],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )

                exit(1)
            
            else:
                time.sleep(60*3)
