import datetime
from collections import defaultdict

import pandas as pd
import sqlalchemy
from sqlalchemy import (DDL, JSON, Boolean, Column, DateTime, Integer, String,
                        and_, create_engine, event, func)
from sqlalchemy.orm import Session

from models import db_models

from .base.orm_base import DATABASE_DIR, Base


#определение типов
type Row = sqlalchemy.orm.state.InstanceState


#заголовки из реестра РМЦ
headers_rmc = [
    'register_id',
    'lawsuit_id',
    'court_name',
    'region_name',
    'client_last_name',
    'client_first_name',
    'client_father_name',
    'client_birthday',
    'client_gender',
    'client_birth_place',
    'client_series',
    'client_number',
    'client_issue_on',
    'client_issue_by',
    'client_code',
    'client_snils',
    'client_inn',
    'client_registration_index',
    'client_reg_address',
    'client_actual_index',
    'client_actual_address',
    'client_phone',

]


class CourtActions(Base):
    """Судебные подачи
    """
    court_action_id = Column(String, index=True)        #id подачи локальный
    lawsuit_id = Column(Integer)                        #id подачи РМЦ
    status = Column(String)                             #статус подачи
    rmc_register_num = Column(String)                   #номер реестра РМЦ
    rmc_register_vars = Column(JSON)                    #параметры из реестра
    owner = Column(String)                              #пользователь, от кого подаём
    project = Column(String)                            #проект
    activity_type = Column(String)                      #тип активности (Индексация/Обычная подача/Парсинг ГАС)
    package_of_docs_checked = Column(Boolean)           #пакет документов проверен
    missing_docs_added = Column(Boolean)                #недостающие документы добавлены
    date_uploaded_docs_on_gas = Column(DateTime)        #дата загрузки документов
    result_number = Column(String)                      #номер подачи из ГАС
    error_msg = Column(String)                          #текст ошибки


    @classmethod
    def append(cls, rmc_register_num:str, owner:db_models.User, 
               project:str, activity_type:db_models.ActivityType, **data) -> str:
        """Построчное добавление данных

        Args:
            rmc_register_num (str): номер реестра РМЦ
            owner (db_models.User): владелец
            project (str): проект
            activity_type (db_models.ActivityType): тип активности
            
            **data: данные из реестра РМЦ (headers_rmc), хранятся в поле с форматом json

        Returns:
            str: возвращает id созданной записи (court_action_id)
        """
        #сброс данных в архив
        #cls._flush_to_archive()
        with Session(autoflush=False, bind=engine) as db:
            #создается новая запись
            rmc_vars = {}
            for var in headers_rmc:
                val = data.get(var).strftime("%d.%m.%Y %H:%M:%S") if isinstance(
                    data.get(var), (pd.Timestamp, datetime.datetime)) else data.get(var)
                rmc_vars[var] = val
            row = cls(
                lawsuit_id = data.get('lawsuit_id'),
                status = db_models.Status.CREATED,
                rmc_register_num=rmc_register_num,
                rmc_register_vars = rmc_vars,
                owner = owner,
                project = project,
                activity_type = activity_type
                    )
            db.add(row)
            db.commit()
            return str(row.court_action_id)
        
        
    @classmethod
    def append_bulk(cls, 
                    rmc_register_num:str,
                    owner:str,
                    project:str,
                    activity_type:str,
                    data_list:list[dict],
                    ) -> int:
        """Массовое добавление данных 
        
        Args:
            
            rmc_register_num (str): номер реестра РМЦ
            owner (db_models.User): владелец
            project (str): проект
            activity_type (db_models.ActivityType): тип активности
                
            data_list(list): данные упакованные в list, ожидается массив с даннымии из реестра РМЦ

        Returns:
            int: количество созданных записей
        """
        #сброс данных в архив
        #cls._flush_to_archive()
        with Session(autoflush=False, bind=engine) as db:
            rows = []
            for data in data_list:
                rmc_vars = {}
                for var in headers_rmc:
                    val = data.get(var).strftime("%d.%m.%Y %H:%M:%S") if isinstance(
                        data.get(var), (pd.Timestamp, datetime.datetime)) else data.get(var)
                    rmc_vars[var] = val
                rows.append(
                    cls(
                    lawsuit_id = data.get('lawsuit_id'),
                    status = db_models.Status.CREATED,
                    rmc_register_num=rmc_register_num,
                    rmc_register_vars = rmc_vars,
                    owner = owner,
                    project = project,
                    activity_type = activity_type
                        )
                )
            db.bulk_save_objects(rows)
            db.commit()
            return len(rows)


    @classmethod
    def get_actions(cls, owner:db_models.User|None=None,
                   status: db_models.Status|None=None,
                   rmc_register_num:str|None=None,
                   project:str|None=None,
                   completed_processing=False,
                   ) -> list[dict]|None:
        """Возвращает записи из таблицы в формате словаря по активному реестру
        Если заполнен owner (и project) фильтрация будет по owner (и project)
        Если заполнен rmc_register_num  фильтрация будет по rmc_register_num 

        Args:
            owner (db_models.User | None, optional): владелец реестра подачи РМЦ. Defaults to None.
            rmc_register_num (str | None, optional): номер реестра РМЦ. Defaults to None.
            project (str | None, optional): проект. Defaults to None.

        Returns:
            list[dict]|None: список словарей где ключ - название поля
        """

        with Session(autoflush=False, bind=engine) as db:
            if owner:
                if status:
                    filt = and_(cls.status==status, cls.owner==owner)
                else:
                    active_reg=cls.get_active_register(owner=owner,  project=project)
                    if completed_processing:
                        filt = and_(cls.rmc_register_num!=active_reg, cls.owner==owner) if active_reg \
                            else cls.owner==owner

                    else:
                        filt = cls.rmc_register_num==active_reg

            elif rmc_register_num:
                filt = cls.rmc_register_num==rmc_register_num
            else:
                return None
            result = []
            if rows:=db.query(cls).filter(filt).all():
                for row in rows:
                    data = cls._row_to_dict(row)
                    data.update(row.rmc_register_vars)
                    data.pop('rmc_register_vars')
                    result.append(data)
                return result

        
    @classmethod
    def get_action(cls, lawsuit_id:int|None=None, court_action_id:str|None=None) -> dict|None:
        """Возвращает записи из таблицы в формате словаря
        фильтрация происходит по одному из значений lawsuit_id или court_action_id

        Args:
            court_action_id (str): id записи

        Returns:
            dict|None: словарь где ключ - название поля
        """
        if not any([lawsuit_id, court_action_id]):
            return None
        with Session(autoflush=False, bind=engine) as db:
            if row:=db.query(cls).filter(
                        cls.lawsuit_id==lawsuit_id if lawsuit_id else \
                                        cls.court_action_id==court_action_id ).first():
                data = cls._row_to_dict(row)
                data.update(row.rmc_register_vars)
                data.pop('rmc_register_vars')
                return data


    @classmethod
    def get_actions_from(cls, date:datetime.datetime) -> list:
        """Возвращает записи из таблицы в формате словаря с даты date
        
        Args:
            date (datetime.datetime): период с которого будут возвращены данные

        Returns:
            list[dict]|None: список словарей где ключ - название поля
        """
        with Session(autoflush=False, bind=engine) as db:
            result = []
            if rows:=db.query(cls).filter(cls.created_on>=date).all():
                for row in rows:
                    data = cls._row_to_dict(row)
                    data.update(row.rmc_register_vars)
                    data.pop('rmc_register_vars')
                    result.append(data)
            return result
    

    @classmethod
    def get_actions_updated_after(cls, date:datetime.datetime) -> list:
        """Возвращает записи из  таблицы в формате словаря обновленные после даты date
        
        Args:
            date (datetime.datetime): период с которого будут возвращены данные

        Returns:
            list[dict]|None: список словарей где ключ - название поля
        """
        with Session(autoflush=False, bind=engine) as db:
            result = []
            if rows:=db.query(cls).filter(cls.updated_on>=date).all():
                for row in rows:
                    data = cls._row_to_dict(row)
                    data.update(row.rmc_register_vars)
                    data.pop('rmc_register_vars')
                    result.append(data)
            return result
    
    @classmethod
    def get_active_register(cls, owner:db_models.User,
                   project:str|None=None,
                   ) -> str|None:
        """Проверяет наличие активных подач по статусам записей

        Args:
            owner (db_models.User): сотрудник владелец подачи
            project (str | None, optional): проект. Defaults to None.

        Returns:
            str|None: номер реестра РМЦ при наличии активной подачи, иначе None
        """
        with Session(autoflush=False, bind=engine) as db:
            filt = and_(cls.owner==owner, cls.project==project, 
                            cls.status.not_in([db_models.Status.COMPLETED, db_models.Status.ERROR])) if project else \
                    and_(cls.owner==owner, cls.status.not_in([db_models.Status.COMPLETED, db_models.Status.ERROR, db_models.Status.ERROR_RMC]))

            if row:=db.query(cls).filter(filt).first():
                return str(row.rmc_register_num)
        return None


    @classmethod
    def is_active(cls, owner:db_models.User,
                   project:str|None=None) -> bool:
        """Проверяет активна ли подача по сотруднику

        Args:
            owner (db_models.User): сотрудник владелец подачи
            project (str | None, optional): проект. Defaults to None.

        Returns:
            bool: флаг активной подачи
        """
        return True if cls.get_active_register(owner=owner, project=project) else False

    
    @classmethod
    def get_progress(cls, owner:db_models.User,
                   project:str|None=None) -> dict|None:
        """Информация по подаче в разрезе статтусов и количества подач по статусам,
            если подача активна

        Args:
            owner (db_models.User): сотрудник - владелец подачи
            project (str | None, optional): проект. Defaults to None.

        Returns:
            dict|None: данные в следующем формате {
                    'Создано':int,
                    'Пакет документов проверен':int,
                    'Недостающие документы добавлены':int,
                    'В обработке':int,
                    'Завершено':int,
                    'Ошибка':int,
                    'Итого':int,
            }
        """
        with Session(autoflush=False, bind=engine) as db:
            register_num = cls.get_active_register(owner=owner, project=project)
            if not register_num:
                return None
            all_count = db.query(cls).filter(cls.rmc_register_num==register_num).count()
            progress_struct=db.query(cls.status, func.count(cls.status).label('count')
                                         ).filter(cls.rmc_register_num==register_num
                                                  ).group_by(cls.status).all()
            progress_structure = {row.status:row.count for row in progress_struct}
            progress_structure_extend = {str(i):0 for i in db_models.Status}
            progress_structure_extend.update(progress_structure)
            progress_structure_extend.update({'Итого':all_count})
            return progress_structure_extend
        
    
    @classmethod
    def change_status(cls, status:db_models.Status, 
                      court_action_id:int|None=None, 
                      lawsuit_id:int|None=None,
                      result_number:str|None=None,
                      error_msg:str|None=None,
                      date_and_time_gus:str|None=None,
                      ) -> bool:
        """Меняет статус записи, 
        если статус меняется на 'Пакет документов проверен' в поле package_of_docs_checked проставляется True
        если статус меняется на 'Недостающие документы добавлены' в поле missing_docs_added проставляется True
        если статус меняется на Завершено в поле date_uploaded_docs_on_gas проставляется текущая дата и время
                                 в поле result_number проставляется номер подачи С ГАС  
        если статус меняется на 'Ошибка' в поле error_msg проставляется текст 

        Args:
            court_action_id (str): id записи
            lawsuit_id (str): id записи из РМЦ
            status (db_models.Status): статус на который будет смена
            result_number (str): номер полученный с ГАС
            error_msg (str): текст ошибки

        Returns:
            bool: True при удачной смене статуса 
        """
        if not any([lawsuit_id, court_action_id]):
            return False
        with Session(autoflush=False, bind=engine) as db:
            filt = cls.court_action_id==court_action_id if court_action_id else \
                                                        cls.lawsuit_id==lawsuit_id
            if row:=db.query(cls).filter(filt).first():
                row.status = status
                if status==db_models.Status.COMPLETED:
                    row.date_uploaded_docs_on_gas=datetime.datetime.strptime(date_and_time_gus, "%d.%m.%Y %H:%M:%S")
                    row.result_number=result_number if result_number else row.result_number
                elif status==db_models.Status.DOCS_FORMED:
                    row.package_of_docs_checked=True
                elif status==db_models.Status.DOCS_ADDED:
                    row.missing_docs_added=True
                elif status==db_models.Status.ERROR or status==db_models.Status.ERROR_RMC:
                    row.error_msg=error_msg if error_msg else row.error_msg
                db.commit()
                return True
            return False
    
    
    @classmethod
    def _flush_to_archive(cls, owner:db_models.User) -> int|None:
        """Перемещает данные по сотруднику в архивную таблицу 

        Args:
            rows (_type_): строки которые будут перемещены

        Returns:
            int: количество пперемещенных строк
        """
        active_register = cls.get_active_register(owner=owner)
        with Session(autoflush=False, bind=engine) as db:
            filt = and_(cls.owner==owner, cls.rmc_register_num!=active_register) if active_register else (cls.owner==owner)
            if rows:=db.query(cls).filter(filt).all():
                cnt_del = CourtActionsArchive.bulk_input(rows)
                for row in rows:
                    db.delete(row)
                db.commit()
                return cnt_del


                

#триггер для создания id подачи
trigger_court_actions = DDL("""
    CREATE TRIGGER set_court_actions_id_after_insert 
    AFTER INSERT ON court_actions
    FOR EACH ROW
    WHEN NEW.court_action_id IS NULL
    BEGIN
        UPDATE court_actions SET court_action_id = 'CA-' || unixepoch(created_on) ||'-'|| NEW.id  WHERE id = NEW.id;
    END;
""")
event.listen(CourtActions.__table__, 'after_create', trigger_court_actions)



# создаем движок SqlAlchemy
engine = create_engine(fr"sqlite:///{DATABASE_DIR}/CourtActions.db")

# создаем таблицы
CourtActions.__table__.create(engine, checkfirst=True)


class CourtActionsArchive(Base):
    """Архив
    """
    
    court_action_id = Column(String)        #id подачи локальный
    lawsuit_id = Column(Integer)                        #id подачи РМЦ
    status = Column(String)                             #статус подачи
    rmc_register_num = Column(String)                   #номер реестра РМЦ
    rmc_register_vars = Column(JSON)                    #параметры из реестра
    owner = Column(String)                              #пользователь, от кого подаём
    project = Column(String)                            #проект
    activity_type = Column(String)                      #тип активности (Индексация/Обычная подача/Парсинг ГАС)
    package_of_docs_checked = Column(Boolean)           #пакет документов проверен
    missing_docs_added = Column(Boolean)                #недостающие документы добавлены
    date_uploaded_docs_on_gas = Column(DateTime)        #дата загрузки документов
    result_number = Column(String)                      #номер подачи из ГАС
    error_msg = Column(String)                          #текст ошибки
    created_on = Column(DateTime)
    updated_on = Column(DateTime)
    
    @classmethod
    def bulk_input(cls, data:list[Row]) -> int:
        """Сохраняет данные в архивную таблицу

        Args:
            data (list[Row]): данные

        Returns:
            int: количество новых строк
        """
        with Session(autoflush=False, bind=engine_archive) as db:
            new_rows = []
            for old_row in data:
                new_rows.append(
                    cls(
                        court_action_id = old_row.court_action_id,
                        lawsuit_id = old_row.lawsuit_id,
                        status = old_row.status,
                        rmc_register_num = old_row.rmc_register_num,
                        rmc_register_vars = old_row.rmc_register_vars,
                        owner = old_row.owner,
                        project = old_row.project,
                        activity_type = old_row.activity_type,
                        package_of_docs_checked = old_row.package_of_docs_checked,
                        missing_docs_added = old_row.missing_docs_added,
                        date_uploaded_docs_on_gas = old_row.date_uploaded_docs_on_gas,
                        result_number = old_row.result_number,
                        error_msg = old_row.error_msg,
                        created_on = old_row.created_on,
                        updated_on = old_row.updated_on
                        )
                )
            db.bulk_save_objects(new_rows)
            db.commit()
            return len(data)
        

    @classmethod
    def get_action(cls, lawsuit_id:int|None=None, court_action_id:str|None=None) -> dict|None:
        """Возвращает записи из таблицы в формате словаря
        фильтрация происходит по одному из значений lawsuit_id или court_action_id

        Args:
            court_action_id (str): id записи

        Returns:
            dict|None: словарь где ключ - название поля
        """
        if not any([lawsuit_id, court_action_id]):
            return None
        with Session(autoflush=False, bind=engine_archive) as db:
            if row:=db.query(cls).filter(
                        cls.lawsuit_id==lawsuit_id if lawsuit_id else \
                                        cls.court_action_id==court_action_id ).first():
                data = cls._row_to_dict(row)
                data.update(row.rmc_register_vars)
                data.pop('rmc_register_vars')
                return data


    @classmethod
    def get_actions_from(cls, date:datetime.datetime) -> list:
        """Возвращает записи из таблицы в формате словаря с даты date
        
        Args:
            date (datetime.datetime): период с которого будут возвращены данные

        Returns:
            list[dict]|None: список словарей где ключ - название поля
        """
        with Session(autoflush=False, bind=engine_archive) as db:
            result = []
            if rows:=db.query(cls).filter(cls.created_on>=date).all():
                for row in rows:
                    data = cls._row_to_dict(row)
                    data.update(row.rmc_register_vars)
                    data.pop('rmc_register_vars')
                    result.append(data)
            return result


    @classmethod
    def get_actions_updated_after(cls, date:datetime.datetime) -> list:
        """Возвращает записи из  таблицы в формате словаря обновленные после даты date
        
        Args:
            date (datetime.datetime): период с которого будут возвращены данные

        Returns:
            list[dict]|None: список словарей где ключ - название поля
        """
        with Session(autoflush=False, bind=engine_archive) as db:
            result = []
            if rows:=db.query(cls).filter(cls.updated_on>=date).all():
                for row in rows:
                    data = cls._row_to_dict(row)
                    data.update(row.rmc_register_vars)
                    data.pop('rmc_register_vars')
                    result.append(data)
            return result


    @classmethod
    def get_actions_from_register(cls, rmc_register_num:str,
                   ) -> list[dict]|None:
        """Возвращает записи из таблицы в формате словаря по реестру

        Args:
            rmc_register_num (str | None, optional): номер реестра РМЦ. Defaults to None.

        Returns:
            list[dict]|None: список словарей где ключ - название поля
        """
        with Session(autoflush=False, bind=engine_archive) as db:
            filt = cls.rmc_register_num==rmc_register_num
            result = []
            if rows:=db.query(cls).filter(filt).all():
                for row in rows:
                    data = cls._row_to_dict(row)
                    data.update(row.rmc_register_vars)
                    data.pop('rmc_register_vars')
                    result.append(data)
                return result

# создаем движок SqlAlchemy
engine_archive = create_engine(fr"sqlite:///{DATABASE_DIR}/ArchiveCourtActions.db")

# создаем таблицы
CourtActionsArchive.__table__.create(engine_archive, checkfirst=True)