import pyrogram
from better_proxy import Proxy
from telethon import TelegramClient
from utils import config
from utils.logging import logger
import socks
from database import actions as db_actions


async def create_sessions() -> None:
    while True:
        session_name: str = input('\nВведите название сессии (для выхода нажмите Enter): ')

        if not session_name:
            return

        while True:
            proxy_str: str = input('Введите Proxy (type://user:pass@ip:port // type://ip:port, для использования без '
                                   'Proxy нажмите Enter): ').replace('https://', 'http://')

            if proxy_str:
                try:
                    proxy: Proxy = Proxy.from_str(
                        proxy=proxy_str
                    )

                    # proxy_dict: dict = {
                    #     'proxy_type': proxy.protocol,
                    #     'addr': proxy.host,
                    #     'port': proxy.port,
                    #     'username': proxy.login,
                    #     'password': proxy.password
                    # }

                    proxy_dict = dict(proxy_type=socks.SOCKS5, addr=proxy.host, port=proxy.port, username=proxy.login,
                                 password=proxy.password)

                except ValueError:
                    logger.error(f'Неверно указан Proxy, повторите попытку ввода')

                else:
                    break

            else:
                proxy: None = None
                proxy_dict: None = None
                break
        # logger.info(proxy_dict)
        async with TelegramClient(session=f"sessions/{session_name}",
                                  api_id=config.api_id,
                                  api_hash=config.api_hash,
                                  device_model=config.device,
                                  app_version=config.app_version,
                                  lang_code=config.system_lang_pack,
                                  system_lang_code=config.system_lang_pack, proxy=proxy_dict) as client:

            user_data = await client.get_me()

        logger.info(f'Успешно добавлена сессия {user_data.username} | {user_data.first_name} {user_data.last_name}')

        await db_actions.add_session(session_name=session_name,
                                     session_proxy=str(proxy))