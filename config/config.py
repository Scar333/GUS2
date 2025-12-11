"""Общие настройки проекта ГАСП"""

from __future__ import annotations

from pathlib import Path

PATH_TO_CONFIG_DIR =  Path(__file__).parent.resolve()

PATH_TO_PUBLIC_FOLDER = Path(r"\\lime.local\dfs\Disk_S\Взаимодействие\ДСВ - ДАР\ГАСП")

PATH_TO_JSON_THUMBPRINTS = PATH_TO_CONFIG_DIR / "thumbprints" / "thumbprints.json"

PATH_TO_RMC_CONFIG = PATH_TO_CONFIG_DIR / "rmc" / "config.toml"

PATH_TO_CRYPTCP = PATH_TO_CONFIG_DIR.parent / "auxiliary_programs" / "cryptcp.x64.exe"

PATH_TO_SCREENSHOTS = PATH_TO_CONFIG_DIR.parent / "screenshots"

# TODO: Путь до данных заявителей
PATH_TO_APPLICANTS_DETAILS = Path(r"\\lime.local\dfs\Disk_S\Взаимодействие\ДСВ - ДАР\ГАСП\Данные_Заявителя\config.toml")
