import random
from itertools import cycle
from better_proxy import Proxy
from os.path import isdir
import asyncio
from os import listdir
from os import mkdir
from os.path import exists
from sys import stderr


from core import create_sessions, start_farming, import_sessions
from database import on_startup_database
# from utils import monkeypatching


async def main() -> None:
    await on_startup_database()

    match user_action:
        case 1:
            await create_sessions()

            print('Сессии успешно добавлены')

        case 2:

            session_folder = input("Введите путь к папке с сессиями: ")
            proxy_file = input("Введите путь к файлу с прокси: ")

            await import_sessions(session_folder, proxy_file)

        case 3:
            random.shuffle(session_files)
            tasks: list = [
                asyncio.create_task(coro=start_farming(session_name=current_session_name, task_number=index))
                for index, current_session_name in enumerate(session_files)
            ]

            await asyncio.gather(*tasks)



        case _:
            print('Действие выбрано некорректно')


if __name__ == '__main__':
    if not exists(path='sessions'):
        mkdir(path='sessions')

    session_files: list[str] = [current_file[:-8] if current_file.endswith('.session')
                                else current_file for current_file in listdir(path='sessions')
                                if current_file.endswith('.session') or isdir(s=f'sessions/{current_file}')]

    print(f'Обнаружено {len(session_files)} сессий')

    user_action: int = int(input('\n1. Создать сессию'
                                 '\n2. Импортировать сессии и прокси'
                                 '\n3. Запустить бота с существующих сессий'
                                 '\nВыберите ваше действие: '))
    print()

    # try:
    #     import uvloop
    #
    #     uvloop.run(main())
    #
    # except ModuleNotFoundError:
    asyncio.run(main())

    input('\n\nPress Enter to Exit..')