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
from core.rmc.sending_data_to_RMC import send_data_from_rmc

# from config import PATH_TO_RMC_CONFIG

def main():

    user_name = "Евженко_Алена"

    # Создаем логгер для основного процесса
    date_now = datetime.now().strftime("%d.%m.%Y___%H-%M-%S")
    _logger = CustomLogger(custom_name_log_file=f"{user_name}_{date_now}")
    main_logger = _logger.start_initialization()
    main_logger_path = _logger.get_full_path_to_log_file()

    # activity_type = "Обычная подача"
    # Скачивание реестра из РМЦ
    # final_path_to_folder = get_data_from_RMC(
    #     user_name=user_name,
    #     activity_type=activity_type,
    #     logger=main_logger,
    #     logger_path=main_logger_path
    #     )
    final_path_to_folder = fr"S:\Взаимодействие\ДСВ - ДАР\ГАСП\{user_name}\Лайм\Пакеты"
    #complete_package_documents(
    #     path_to_folder=final_path_to_folder,
    #     logger=main_logger,
    #     logger_path=main_logger_path
    #     )
    #удаление sig подписей, перемещение файлов квитанций и расчетов
    for dirpath, _ , filenames in os.walk(final_path_to_folder):
        for filename in filenames:
            file = (os.path.join(dirpath, filename))
            if filename.endswith('.sig'):
                os.remove(file)
            elif dirpath.endswith('Приложения') and filename in ['Квитанция об уплате госпошлины.pdf',
                                                              'Расчет суммы требований.pdf']:
                shutil.move(
                    os.path.join(dirpath, filename),
                    os.path.join(dirpath,os.pardir, filename)
                )


    signed_files(path_to_folder=final_path_to_folder, user_name=user_name,logger=main_logger)
    
    


if __name__ == "__main__":
    # Запускаем основной процесс
    main()
