import os
import shutil

from core.browser.base.base import BaseBrowser
from core.browser.regular_serve import RegularServe
from database.database import CourtActions
from core.browser.base.error_handler import handle_critical_error
# from core.browser.site_monitor import SiteMonitor, safe_navigate
from utils._logger import CustomLogger
from datetime import datetime
from utils import complete_package_documents, signed_files
# from core.data_unloading_from_RMC import get_data_from_RMC

# from config import PATH_TO_RMC_CONFIG
from datetime import datetime
from pathlib import Path

import requests

from database.database import CourtActions, CourtActionsArchive
from models.database.db_models import Status
from utils._logger import CustomLogger


BASE_URL = "https://rmc.lcgdc.ru"
API_KEY = "76EB641E-D7D2-40DC-A439-2FC24B3823FC"

HEADERS = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}
SSL_VERIFY = False

# Создаем логгер для основного процесса
date_now = datetime.now().strftime("%d.%m.%Y___%H-%M-%S")
_logger = CustomLogger(custom_name_log_file=f"resendrmc_{date_now}")
main_logger = _logger.start_initialization()
main_logger_path = _logger.get_full_path_to_log_file()

def register_sent(
        registry_number: int,
        current_day: str,
        lawsuits: list[dict],
        logger= main_logger,
        logger_path= main_logger_path,
        ):
    url = BASE_URL + "/api/ElectronicSubmissionByRobot/RegisterSent"
    payload = {
        "printRegisterId": registry_number,
        "registerSentDate": current_day,
        "lawsuits": lawsuits
    }

    ####
    import json
    with open(f"{registry_number}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)
    ####

    try:
        requests.post(url, headers=HEADERS, json=payload, verify=SSL_VERIFY, timeout=120)

    except Exception as ex:
        logger.info(f"{ex}")

def send_data_to_rmc(
        registry: str,
        logger= main_logger,
        logger_path= main_logger_path,
        ) -> bool:
    logger.info(f"Получаю данные реестра для \"{registry}\"...")
    registry_data: list[dict] = CourtActionsArchive.get_actions_from_register(rmc_register_num=registry)

    # tmp_list = []
    # for client in registry_data:
    #     if client.get("rmc_register_num") == "36392":
    #         tmp_list.append(client)

    logger.info(f"Успешно получил данные в количестве \"{len(registry_data)}\" шт.")

    logger.info("Формирую json для отправки в РМЦ...")
    lawsuits = []
    for client in registry_data:
        if client.get("status") == Status.COMPLETED:
            lawsuits.append({
                "lawsuitId": int(client.get("lawsuit_id")),
                "successResult": {
                    "sentNumber": client.get("result_number"),
                    "lawsuitSentDate": client.get("date_uploaded_docs_on_gas").isoformat() + '+07:00'
                    }
            })
        elif client.get("status") == Status.ERROR:
            lawsuits.append({
                "lawsuitId": int(client.get("lawsuit_id")),
                "errorResult": {"errors": [client.get("error_msg")]}
            })
        else:
            lawsuits.append({
                "lawsuitId": int(client.get("lawsuit_id")),
                "errorResult": {"errors": [client.get("error_msg")]}
            })

    logger.info("Json сформирован и готов к отправке!")

    logger.info("Отправляю данные в РМЦ...")
    registry_number = int(registry_data[0].get("rmc_register_num"))
    logger.info(registry_number)
    current_day = datetime.utcnow().strftime("%Y-%m-%d")
    register_sent(
        registry_number=registry_number,
        current_day=current_day,
        lawsuits=lawsuits,
        logger=logger,
        logger_path=logger_path,
        )
    logger.info("Данные успешно отправлены!")

send_data_to_rmc(registry='36591')