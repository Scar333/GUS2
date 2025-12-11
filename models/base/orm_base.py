import os
import datetime
import sqlalchemy
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import DeclarativeBase, declared_attr

#определение типов
type Row = sqlalchemy.orm.state.InstanceState

DATABASE_DIR = os.getenv('DATABASE_DIRECTORY') if os.getenv('DATABASE_DIRECTORY') \
    else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, 'database'))

if not os.path.exists(DATABASE_DIR):
                os.makedirs(DATABASE_DIR)

class Base(DeclarativeBase):
    """Абстрактный класс для моделей sqlalchemy ORM

    Args:
        DeclarativeBase (_type_): базовый класс

    """
    __abstract__ = True
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    created_on = Column(DateTime, default=func.now())
    updated_on = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    @declared_attr
    def __tablename__(cls) -> str:
        
        """Автоматически формирует наименование таблицы на основе имени создаваемого класса

        Returns:
            str: имя таблицы
        """
        characters = [f"_{char.lower()}" if char.isupper()  else char.lower() for char in cls.__name__]
        return "".join(characters).lstrip("_")


    @classmethod
    def _row_to_dict(cls, row: Row) -> dict:
        """Преобразовывает строку записи бд в словарь с наименованием полей без символа "_" на конце

        Args:
            row (Row): запись таблицы

        Returns:
            dict: словарь с наименованиями полей и значениями
        """
        return_dict = {}
        for key, val in cls.__dict__.items():
            if isinstance(val, sqlalchemy.orm.attributes.InstrumentedAttribute):
                return_dict[key.rstrip("_")] = getattr(row, key)

        return return_dict


    @classmethod
    def _rows_to_dict(cls, rows: list[Row]) -> list[dict]:
        """Преобразовывает список строк записей бд в список со словарем

        Args:
            rows (list[Row]): список записей таблицы

        Returns:
            list[dict]: список со словарем с наименованиями полей и значениями
        """
        rows_to_dict = []
        for row in rows:
            rows_to_dict.append(cls._row_to_dict(row))
        return rows_to_dict

