import functools
import time
from typing import Callable, Any


def retry_with_notification(max_attempts: int = 5, delay: float = 1.0):
    """
    Декоратор для повторного выполнения функции с уведомлением при всех неудачных попытках
    
    Args:
        max_attempts: максимальное количество попыток
        delay: задержка между попытками в секундах
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            errors = []
            
            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    print(f"Функция {func.__name__} выполнена успешно с попытки {attempt + 1}")
                    return result
                except Exception as e:
                    errors.append(f"Попытка {attempt + 1}: {str(e)}")
                    print(f"Попытка {attempt + 1} не удалась: {str(e)}")
                    
                    if attempt < max_attempts - 1:
                        print(f"⏳ Ожидание {delay} секунд перед следующей попыткой...")
                        time.sleep(delay)
            
            # Если все попытки неудачные
            error_message = f"Функция {func.__name__} не выполнена после {max_attempts} попыток.\nОшибки:\n" + "\n".join(errors)
            send_notification(error_message)
            raise Exception(error_message)
        
        return wrapper
    return decorator

def send_notification(message: str) -> None:
    # TODO: Прикрутить Rocket!
    """Функция для отправки уведомления"""
    print(f"🔔 УВЕДОМЛЕНИЕ: {message}")
