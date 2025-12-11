import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from core.browser.base.error_handler import SkipClient

from ._logger import CustomLogger

# Для отдельных логов
current_script_dir = Path(__file__).resolve().parent
path_to_log_decorator = current_script_dir.parent / "logs_decorator"
date_now = datetime.now().strftime("%d.%m.%Y___%H-%M-%S")
logger = CustomLogger(
    custom_path_to_folder=str(path_to_log_decorator),
    custom_name_log_file=f"retry_func_{date_now}",
)
log = logger.start_initialization()

def retry_func(attempts=5):
    """
    Декоратор для повторных попыток выполнения функции.
    
    Args:
        attempts (int): Количество попыток выполнения (по умолчанию 5).
    
    Returns:
        bool: True если функция выполнилась успешно, False если все попытки исчерпаны.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    func(*args, **kwargs)
                    log.info(f"Функция \"{func.__name__}\" выполнена успешно с попытки \"{attempt + 1}\"")
                    return True
                except Exception as ex:
                    if attempt == attempts - 1:
                        log.error(f"Все \"{attempts}\" попыток исчерпаны. Последняя ошибка:\n{ex}")
                        return False
                    log.warning(f"Попытка \"{attempt + 1}\" не удалась:\n{ex}\n\nПовтор через 5 секунд...")
                    time.sleep(5)
            
            return False
        
        return wrapper
    return decorator



def new_retry_func(attempts=5):
    """
    Декоратор для повторных попыток выполнения функции.
    
    Args:
        attempts (int): Количество попыток выполнения (по умолчанию 5).
    
    Returns:
        bool: True если функция выполнилась успешно, False если все попытки исчерпаны.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    func(*args, **kwargs)
                except SkipClient:
                    return False
                except Exception as ex:
                    if attempt == attempts - 1:
                        log.error(f"Все \"{attempts}\" попыток исчерпаны. Последняя ошибка:\n{ex}")
                        return False
                    log.warning(f"Попытка \"{attempt + 1}\" не удалась:\n{ex}\n\nПовтор через 5 секунд...")
                    time.sleep(5)
            
            return False
        
        return wrapper
    return decorator
