import time


def minutes_until(timestamp):
    current_time = time.time()  # Текущее время в секундах с начала эпохи
    remaining_time = timestamp - current_time
    remaining_minutes = remaining_time / 60  # Переводим секунды в минуты
    return int(remaining_minutes)