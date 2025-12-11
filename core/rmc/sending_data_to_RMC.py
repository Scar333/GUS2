from datetime import datetime
from pathlib import Path

import requests

from database.database import CourtActions
from models.database.db_models import Status
from utils._logger import CustomLogger

from ..browser.base.error_handler import handle_critical_error

BASE_URL = "https://rmc.lcgdc.ru"
API_KEY = "76EB641E-D7D2-40DC-A439-2FC24B3823FC"

HEADERS = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}
SSL_VERIFY = False


def register_sent(
        registry_number: int,
        current_day: str,
        lawsuits: list[dict],
        logger: CustomLogger,
        logger_path: str | Path,
        user_name: str
        ):
    url = BASE_URL + "/api/ElectronicSubmissionByRobot/RegisterSent"
    payload = {
        "printRegisterId": registry_number,
        "registerSentDate": current_day,
        "lawsuits": lawsuits
    }
    import json
    with open(f"{registry_number}.json", "w", encoding="UTF-8") as file:
        json.dump(payload, file, indent=4, ensure_ascii=False)

    try:
        resp = requests.post(url, headers=HEADERS, json=payload, verify=SSL_VERIFY, timeout=120)
        logger.info(f"Ответ РМЦ: {resp.text}")
        logger.info(f"Статус код: {resp.status_code}")

    except Exception as ex:
        handle_critical_error(
            logger=logger,
            logger_path=logger_path,
            error_message="Произошла непредвиденная ошибка при отправки данных в РМЦ!",
            exception=ex,
            user_name=user_name
        )

def send_data_from_rmc(
        user_name: str,
        logger: CustomLogger,
        logger_path: str | Path
        ) -> bool:
    logger.info(f"Получаю данные реестра для \"{user_name}\"...")
    registry_data: list[dict] = CourtActions.get_actions(owner=user_name, completed_processing=True)

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

    logger.info("Отправляю данные в РМЦ по реестру")
    registry_number = int(registry_data[0].get("rmc_register_num"))
    current_day = datetime.utcnow().strftime("%Y-%m-%d")
    logger.info(f"Реестр РМЦ {str(registry_number)}")
    register_sent(
        registry_number=registry_number,
        current_day=current_day,
        lawsuits=lawsuits,
        logger=logger,
        logger_path=logger_path,
        user_name=user_name
        )
    logger.info("Данные успешно отправлены!")
