from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ClientData:
    """Модель для клиентов с 'обычной подачей'"""
    activity_type: str
    client_actual_address: str
    client_actual_index: str
    client_birth_place: str
    client_birthday: str
    client_code: str
    client_father_name: str
    client_first_name: str
    client_gender: str
    client_inn: str
    client_issue_by: str
    client_issue_on: str
    client_last_name: str
    client_number: str
    client_phone: str
    client_reg_address: str
    client_registration_index: str
    client_series: str
    client_snils: str
    court_action_id: str
    court_name: str
    created_on: datetime
    date_uploaded_docs_on_gas: str
    error_msg: str
    id: str
    lawsuit_id: str
    missing_docs_added: str
    owner: str
    package_of_docs_checked: str
    project: str
    region_name: str
    register_id: str
    result_number: str
    rmc_register_num: str
    status: str
    updated_on: datetime

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClientData":
        """Преобразователь данных для модели.

        Args:
            data (dict[str, Any]): Данные клиента.

        Returns:
            ClientData: Модель данных.
        """
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                processed_data[key] = value
            else:
                processed_data[key] = str(value) if value is not None else None
        return cls(**processed_data)
