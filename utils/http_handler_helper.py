import calendar
import datetime
import statistics
import time

import pandas as pd
from dateutil.relativedelta import relativedelta

from database import CourtActions, CourtActionsArchive
from models import db_models

from .users import get_users

def user_is_active(owner:str, wait_time_out:bool=False):
    """Проверка активна ли подача по сотруднику
        если wait_time_out True проверка будет выполняться до тех пор пока не 
        будет получен положительный результат, но не более 60*5 секунд


    Args:
        owner (str): владелец загруженного реестра
        wait_time_out (bool): выполнять проверку в течение времени
    """
    if not wait_time_out:
        return CourtActions.is_active(owner=owner)
    
    for _ in range(60*5):
        time.sleep(1)
        if CourtActions.is_active(owner=owner):
            return True
    return False



def get_lawsuit_state(lawsuit_id:int) -> dict:
    if lawsuit:= CourtActionsArchive.get_action(lawsuit_id=lawsuit_id):# \ CourtActions.get_action(lawsuit_id=lawsuit_id)
                        #or CourtActionsArchive.get_action(lawsuit_id=lawsuit_id)
                        

        client_name = f'{lawsuit['client_last_name']} {lawsuit['client_first_name']} {lawsuit['client_father_name']}'
        response = {
            'error': None,
            'clientName': client_name.strip(),
            'state':lawsuit['status'], 
            'stateDescription':lawsuit['error_msg'], 
            'resultNum':lawsuit['result_number'], 
        }
        return response
    else:
        response = {
            'error': f'Не найдена подача с таким Id - {str(lawsuit_id)}',
            'clientName': None,
            'state': None, 
            'stateDescription':None, 
            'resultNum': None, 
        }
        return response


def get_users_submits_state() -> list:
    """Информация по подачам по каждому пользователю

    Returns:
        list: _description_
    """
    response = []
    users = get_users()
    for user in users:
        
        if actions:= CourtActions.get_actions(owner=user):
            register_num = actions[-1].get('rmc_register_num')
            project = actions[-1].get('project')
            #пакеты док-в в обработке
            packets_in_processing = [act for act in actions if act['status'] not in (db_models.Status.COMPLETED, 
                                                                                     db_models.Status.ERROR,
                                                                                     db_models.Status.ERROR_RMC,
                                                                                     )]
            #время окончания подач по каждому пакету док-в
            completed_times = [act['date_uploaded_docs_on_gas'] for act in actions if act['status'] in (db_models.Status.COMPLETED)]
            completed_times.sort()
            #среднее время подачи по последним 50 пакетам
            avg_secs_between_actions = statistics.mean([(time_-completed_times[enum-1]).seconds
                                        for enum, time_ in enumerate(completed_times)][1:][-50:]) \
                                            if completed_times and len(completed_times)>1 else 0
            #время оставшееся на обработку пакетов
            remaining_time = relativedelta(seconds=avg_secs_between_actions*len(packets_in_processing))
            
            response.append(
                {
                    'nameUser':user,
                    'numRegister':register_num,
                    'project':project,
                    'status':'Активен',
                    'sentToday':len(completed_times),
                    'lastSent':max(completed_times).strftime('%d.%m.%Y %H:%M:%S') if completed_times else None,
                    'packetsInQueue':len(packets_in_processing),
                    'howLongWait':f'~{remaining_time.days*24+remaining_time.hours}ч {remaining_time.minutes}м'
                    
                }
            )
            
        else:
            response.append(
                {
                    'nameUser':user,
                    'numRegister':None,
                    'project':None,
                    'status':'Ожидание',
                    'sentToday':None,
                    'lastSent':None,
                    'packetsInQueue':None,
                    'howLongWait':None
                }
            )
    return sorted(response, key=lambda item: item.get('status'))

    
def get_history_state(period:str) -> dict:
    results=[]
    intervals=[]
    actions=[]
    if period == 'Daily':
        intervals = [i for i in range(24)]
        start_date = datetime.datetime.combine(datetime.datetime.now(), datetime.time.min)
        #Приведение Новосибирского времен к UTC
        start_date = start_date-datetime.timedelta(hours=7)
        
    elif period == 'Weekly':
        intervals = [i for i in range(1,8)]
        start_date = datetime.datetime.today()+datetime.timedelta((1-datetime.datetime.now().isoweekday()))
        start_date = datetime.datetime.combine(start_date, datetime.time.min)
        #Приведение Новосибирского времен к UTC
        start_date = start_date-datetime.timedelta(hours=7)
        
    elif period == 'Monthly':
        now = datetime.datetime.now()
        _, monthrange = calendar.monthrange(now.year, now.month)
        intervals = [i for i in range(1,monthrange+1)]
        start_date = datetime.datetime.today()+datetime.timedelta((1-datetime.datetime.now().day))
        start_date = datetime.datetime.combine(start_date, datetime.time.min)
        #Приведение Новосибирского времен к UTC
        start_date = start_date-datetime.timedelta(hours=7)

    current_actions = CourtActions.get_actions_updated_after(start_date)
    history_actions = CourtActionsArchive.get_actions_updated_after(start_date)
    actions.extend(current_actions)
    actions.extend(history_actions)
    if actions:
        users = get_users()
        for user in users:
            user_acts = [act for act in actions if act['owner']==user]
            succes_acts= [act for act in user_acts if act['status']==db_models.Status.COMPLETED]
            failure_acts = [act for act in user_acts if act['status']==db_models.Status.ERROR]
            failure_rmc_acts = [act for act in user_acts if act['status']==db_models.Status.ERROR_RMC]
            
            succes_acts_in_intervals = {}
            failure_acts_in_intervals = {}
            failure_rmc_acts_in_intervals = {}
            for interval in intervals:
                if period == 'Daily':
                    succes_acts_in_intervals[interval] = len(list(filter(
                                            lambda act: act['updated_on'].replace(tzinfo=datetime.timezone.utc
                                                                                  ).astimezone(tz=None).hour==interval, succes_acts)))
                    failure_acts_in_intervals[interval] = len(list(filter(
                                            lambda act: act['updated_on'].replace(tzinfo=datetime.timezone.utc
                                                                                  ).astimezone(tz=None).hour==interval, failure_acts)))
                    failure_rmc_acts_in_intervals[interval] = len(list(filter(
                                            lambda act: act['updated_on'].replace(tzinfo=datetime.timezone.utc
                                                                                  ).astimezone(tz=None).hour==interval, failure_rmc_acts)))
                    intervals_str = [f'{str(i).zfill(2)}:00' for i in intervals]
                    
                elif period == 'Weekly':
                    succes_acts_in_intervals[interval] = len(list(filter(
                                            lambda act: act['updated_on'].replace(tzinfo=datetime.timezone.utc
                                                                                  ).astimezone(tz=None).isoweekday()==interval, succes_acts)))
                    failure_acts_in_intervals[interval] = len(list(filter(
                                            lambda act: act['updated_on'].replace(tzinfo=datetime.timezone.utc
                                                                                  ).astimezone(tz=None).isoweekday()==interval, failure_acts)))
                    failure_rmc_acts_in_intervals[interval] = len(list(filter(
                                            lambda act: act['updated_on'].replace(tzinfo=datetime.timezone.utc
                                                                                  ).astimezone(tz=None).isoweekday()==interval, failure_rmc_acts)))
                    intervals_str = [f'{str(i)}' for i in intervals]
                    
                elif period == 'Monthly':
                    succes_acts_in_intervals[interval] = len(list(filter(
                                            lambda act: act['updated_on'].replace(tzinfo=datetime.timezone.utc
                                                                                  ).astimezone(tz=None).day==interval, succes_acts)))
                    failure_acts_in_intervals[interval] = len(list(filter(
                                            lambda act: act['updated_on'].replace(tzinfo=datetime.timezone.utc
                                                                                  ).astimezone(tz=None).day==interval, failure_acts)))
                    failure_rmc_acts_in_intervals[interval] = len(list(filter(
                                            lambda act: act['updated_on'].replace(tzinfo=datetime.timezone.utc
                                                                                  ).astimezone(tz=None).day==interval, failure_rmc_acts)))
                    intervals_str = [f'{str(i)}' for i in intervals]
            results.append(
            {'user':user, 
             'countSubmit':{
                 'succes':list(succes_acts_in_intervals.values()), 
                 'failure':list(failure_acts_in_intervals.values()),
                 'failure_rmc':list(failure_rmc_acts_in_intervals.values())
                 }
             }
                    )
        all_succes = []
        all_failure = []
        all_failure_rmc = []
        for res in results:
            res_succes = res['countSubmit']['succes']
            res_failure = res['countSubmit']['failure']
            res_failure_rmc = res['countSubmit']['failure_rmc']
            
            all_succes = res_succes if all_succes==[] else [x + y for x, y in zip(res_succes, all_succes)]
            all_failure = res_failure if all_failure==[] else [x + y for x, y in zip(res_failure, all_failure)]
            all_failure_rmc = res_failure_rmc if all_failure_rmc==[] else [x + y for x, y in zip(res_failure_rmc, all_failure_rmc)]
            
        results.append(
            {'user':'Все', 
                'countSubmit':{
                    'succes':all_succes, 
                    'failure':all_failure,
                    'failure_rmc':all_failure_rmc,
                    }
                }
            )
        return {'intervals': intervals_str, 'results': results}
    return {'intervals': [], 'results':{'user':'Все', 
                                        'countSubmit':{
                                            'succes':[], 
                                            'failure':[],
                                            'failure_rmc':[],
                                            }
                }
            }
