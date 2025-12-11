from core.browser.base.base import BaseBrowser
from core.browser.regular_serve import RegularServe
from database.database import CourtActions
from core.browser.base.error_handler import handle_critical_error
# from core.browser.site_monitor import SiteMonitor, safe_navigate
from utils._logger import CustomLogger
from datetime import datetime
from utils import complete_package_documents, signed_files
from core.rmc.data_unloading_from_RMC import get_data_from_RMC
from core.rmc.sending_data_to_RMC import send_data_from_rmc

# from config import PATH_TO_RMC_CONFIG

def main():
    """Основная функция для запуска процесса подачи документов"""

    user_name = "Солонарь_Анастасия"

    # Создаем логгер для основного процесса
    date_now = datetime.now().strftime("%d.%m.%Y___%H-%M-%S")
    _logger = CustomLogger(custom_name_log_file=f"{user_name}_{date_now}")
    main_logger = _logger.start_initialization()
    main_logger_path = _logger.get_full_path_to_log_file()

    activity_type = "Обычная подача"
    # Скачивание реестра из РМЦ
    final_path_to_folder = get_data_from_RMC(
        user_name=user_name,
        activity_type=activity_type,
        logger=main_logger,
        logger_path=main_logger_path
        )
    # final_path_to_folder = fr"S:\Взаимодействие\ДСВ - ДАР\ГАСП\{user_name}\Интел\Пакеты"
    complete_package_documents(
       path_to_folder=final_path_to_folder,
       logger=main_logger,
       logger_path=main_logger_path
        )
    signed_files(path_to_folder=final_path_to_folder, user_name=user_name, logger=main_logger)
    
    #Изменение статуса 'В обработке' на 'Пакет документов полностью сформирован'
    # actions = CourtActions.get_actions(owner=user_name, completed_processing=False)
    # action_in_processing = [action for action in actions if action.get('status') == 'В обработке']
    # for action in action_in_processing:
    #     CourtActions.change_status(lawsuit_id=action['lawsuit_id'], status='Пакет документов полностью сформирован')

    # Инициализация браузера
    # browser = BaseBrowser(user_name)
    
    # Создаем логгер для основного процесса
    # date_now = datetime.now().strftime("%d.%m.%Y___%H-%M-%S")
    # _logger = CustomLogger(custom_name_log_file=f"{user_name}_{date_now}")
    # main_logger = _logger.start_initialization()
    # main_logger_path = _logger.get_full_path_to_log_file()
    
    try:
        # path_to_packages = fr"\\lime.local\dfs\Disk_S\Взаимодействие\ДСВ - ДАР\ГАСП\{user_name}\Лайм\Пакеты"
        
        # regular_serve = RegularServe(
        #     page=browser.page,
        #     path_to_packages_dir=final_path_to_folder,
        #     user_name=user_name,
        #     logger=main_logger,
        #     logger_path=main_logger_path
        # )

        # Запускаем процесс подачи документов с автоматической обработкой ошибок
        success = True
        # success = regular_serve.start_serving()

        if success:
            main_logger.info("Все документы поданы успешно!")
            send_data_from_rmc(
                user_name=user_name,
                logger=main_logger,
                logger_path=main_logger_path
            )
            to_archived = CourtActions._flush_to_archive(user_name)
            main_logger.info(f"Переместил и удалил клиентов в размере \"{to_archived}\" шт.")
        else:
            main_logger.error("Не удалось подать все документы")
        
        return success
        
    except Exception as ex:
        handle_critical_error(
            logger=main_logger,
            logger_path=main_logger_path,
            error_message="Произошла непредвиденная ошибка!",
            exception=ex,
            page=browser.page,
            user_name=user_name
        )


if __name__ == "__main__":
    # Запускаем основной процесс
    main()
