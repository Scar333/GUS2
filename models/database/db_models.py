import json
from enum import StrEnum

from config import PATH_TO_JSON_THUMBPRINTS


class Status(StrEnum):
    """Статусы пакета документов по реестру"""

    CREATED = "Создано"
    DOCS_ADDED = "Недостающие документы добавлены"
    DOCS_SIGNED = "Документы подписаны"
    DOCS_FORMED = "Пакет документов полностью сформирован"

    PROCESSING = "В обработке"
    COMPLETED = "Завершено"
    ERROR = "Ошибка"
    ERROR_RMC = "Ошибка в РМЦ"


class ActivityType(StrEnum):
    """Тип активности"""
    INDEXATION = "Индексация"
    NORMAL = "Обычная подача"
    PARSING = "Парсинг ГАСП"


User = StrEnum("User", json.load(open(PATH_TO_JSON_THUMBPRINTS, encoding="utf-8")))
