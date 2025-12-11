import json
import socket
from os import getlogin
from pathlib import Path
from typing import Literal

from rocketchat.api import RocketChatAPI

# Путь к файлу конфигурации по умолчанию
current_script_dir = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = current_script_dir.parent / "config" / "rocket_config.json"


def format_message(status: str) -> str:
    """Форматирование сообщения.

    Args:
        status (Optional[str], optional): Статус сообщения ("start", "done", "error").

    Returns:
        str: Отформатированное сообщение.
    """
    # TODO: Менять под свои нужды
    username_rocket = "@purdyshev.rv ,"
    name_robot = "Робот ГАСП"

    if status == "start":
        msg = "Робот начал свою работу! ✅"
    elif status == "done":
        msg = "Робот завершил свою работу! ✅"
    elif status == "error":
        msg = "Произошла ошибка в работе робота! ⚠️"
    else:
        msg = ""

    return (
        f"{username_rocket}\r\n\r\n"
        f"🤖 Робот: `{name_robot}`\r\n"
        f"📝 УЗ: `{getlogin()}`\r\n"
        f"💻 Имя сервера: `{socket.gethostname()}`\r\n"
        f"💻 IP сервера: `{socket.gethostbyname(socket.gethostname())}`\r\r\n"
        f"⚡️ Статус: `{msg}`\r\n"
    )


def get_config_data(config_path: Path) -> dict[str, str] | FileNotFoundError:
    """Получение данных для подключения из JSON-файла.

    Args:
        config_path (Path): Путь к JSON-файлу конфигурации.

    Returns:
        dict[str, str]: Словарь с параметрами подключения (id_room, username, password, domain).

    Raises:
        FileNotFoundError: Если указанный файл конфигурации не найден.
    """
    try:
        with open(config_path, "r", encoding="UTF-8") as config_file:
            return json.load(config_file)

    except FileNotFoundError as fnfe:
        raise FileNotFoundError("Не смог найти JSON-файл конфигурации для Rocket.Chat!") from fnfe


class RocketChat:
    """Класс для работы с Rocket.Chat"""

    def __init__(self, path_to_config: str = DEFAULT_CONFIG_PATH) -> None:
        """Инициализация параметров.

        Args:
            path_to_config (str, optional): Путь до JSON-файла. Defaults to DEFAULT_CONFIG_PATH.
        """

        config: dict[str, str] = get_config_data(path_to_config)

        self.id_room: str = config["id_room"]
        self.rocket_chat = RocketChatAPI(
            settings={
                "username": config["username"],
                "password": config["password"],
                "domain": config["domain"]
            }
        )

    @staticmethod
    def _is_response_successful(resp: dict) -> bool:
        """Проверка статуса отправки сообщения.

        Args:
            resp (dict): Словаь ответа запроса.

        Returns:
            bool: True - если сообщение корректно отправилось, иначе False.
        """
        return resp.get("success", False)

    def _send_message_with_attachment(self, msg: str, att: str, desc: str) -> bool:
        """Отправка сообщения с вложением.

        Args:
            msg (str): Текст сообщения.
            att (str): Путь до файла.
            desc (str): Подпись файла.

        Returns:
            bool: True - если сообщение корректно отправилось, иначе False.
        """
        resp = self.rocket_chat.upload_file(
            message=msg,
            description=desc,
            room_id=self.id_room,
            file=att,
        )
        return self._is_response_successful(resp=resp)

    def _send_message_without_attachment(self, msg: str) -> bool:
        """Отправка сообщения без вложения.

        Args:
            msg (str): Текст сообщения.

        Returns:
            bool: True - если сообщение корректно отправилось, иначе False.
        """
        resp = self.rocket_chat.send_message(message=msg, room_id=self.id_room)
        return self._is_response_successful(resp=resp)

    def send_message(self,
                     status: Literal["start", "done", "error"],
                     att: str = None, desc: str = None) -> bool | ValueError:
        """Отправка сообщения.

        Args:
            status (Literal[str]): Статус сообщения ("start", "done", "error").
            att (str, optional): Путь до файла. Defaults to None.
            desc (str, optional): Подпись файла. Defaults to None.

        Raises:
            ValueError: Если передан файл (att), то описание (desc) обязательно, и наоборот.

        Returns:
            bool | ValueError: True - если сообщение корректно отправилось, иначе False или ошибка.
        """
        if (desc and not att) or (att and not desc):
            raise ValueError("Если передан файл (att), то описание (desc) обязательно, и наоборот.")
        msg = format_message(status=status)
        if att and desc:
            return self._send_message_with_attachment(msg, att, desc)
        return self._send_message_without_attachment(msg)
