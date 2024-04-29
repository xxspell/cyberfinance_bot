import asyncio
import itertools
import random

from core.main import start_farming


async def run(user_ids_file, proxies_file):
    user_ids = []
    proxies = []

    # Загрузка идентификаторов пользователей из файла
    with open(user_ids_file, 'r') as f:
        user_ids = [line.strip() for line in f.readlines()]
        random.shuffle(user_ids)


    # Загрузка прокси из файла
    with open(proxies_file, 'r') as f:
        proxies = [line.strip() for line in f.readlines()]
        random.shuffle(proxies)
    print(f"Loaded {len(proxies)} proxies, {len(user_ids)} ids")

    # Создание экземпляров CyberFinance для каждого пользователя и прокси
    tasks = []
    task_number = 1
    proxy_cycle = itertools.cycle(proxies)
    for user_id in user_ids:
        proxy = next(proxy_cycle)
        task = asyncio.create_task(start_farming(user_id, proxy, task_number))  # Пример вызова одного из методов

        tasks.append(task)
        task_number += 1

    # Параллельное выполнение всех задач
    results = await asyncio.gather(*tasks)



async def main():
    art = """
         /)              /) ,                       /)       
 _      (/_  _  __      //   __   _  __   _   _    (/_ ____/_
(__(_/_/_) _(/_/ (_    /(__(_/ (_(_(_/ (_(___(/_  /_) (_) (__
  .-/                 /)                                     
 (_/                 (/                                      
"""
    print(art)
    await run("user_ids.txt", "proxies.txt")

asyncio.run(main())