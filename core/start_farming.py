import asyncio
import random
import aiocfscrape
import time
import traceback
from urllib.parse import unquote, quote
import socks
from telethon import TelegramClient
from telethon import functions
import aiohttp
from better_proxy import Proxy
from aiohttp_proxy import ProxyConnector
from urllib.parse import unquote, parse_qs, urlencode
from database import actions as db_actions
from pyuseragents import random as random_useragent
import json
from database.actions import set_field_by_name, get_tg_web_data_by_name, check_and_rename_column
from exceptions import InvalidSession
from utils import config
from utils.config import exclude_tasks
from utils.generator import headers_base as headers
from utils.logging import logger
from utils.time import minutes_until


def access_token_required(func):
    async def wrapper(self, *args, **kwargs):
        if not self.access_token:
            # Вызываем функцию get_access_token только если access_token пустой
            self.access_token = await self.get_access_token(*args, **kwargs)
        # Возвращаем результат выполнения исходной функции
        return await func(self, *args, **kwargs)

    return wrapper


class Farming:
    def __init__(self,
                 session_name: str, task_number: int):
        self.session_name: str = session_name
        self.access_token = None
        self.session_proxy = None
        self.message_suffix = None
        self.task_number = task_number
        self.is_valid_tg_web_data = True
        self.client = None

    async def _suffix(self, request):
        try:
            response_data = request
            mining_data = response_data['message'].get('miningData', {})
            user_data = response_data['message'].get('userData', {})
            squad_data = response_data['message'].get('squadData', {})

            crack_time = mining_data.get('crackTime')

            balance = user_data.get('balance')

            squad_statistic = squad_data.get('statistic', {})
            squad_title = squad_data['title']
            squad_points = squad_statistic.get('points')
            squad_user_count = squad_statistic.get('userCount')
            squad_rank = squad_statistic.get('rank')
            self.crack_time = crack_time
            self.message_suffix = f"|| B: {balance} | SP: {squad_points} SU: {squad_user_count} SR: {squad_rank} N: {squad_title}| Next claim: {minutes_until(crack_time)} min."

        except Exception as e:
            logger.error(f"{self.task_number} | {self.session_name} | prefix | Error print information account - {e}")

    @access_token_required
    async def claim_reward(self, client: aiocfscrape.CloudflareScraper) -> dict:
        client = self.client
        try:
            client.headers['Authorization']: str = f'Bearer {self.access_token}'
            r: aiocfscrape.CloudflareScraper = await client.get(
                url='https://api.cyberfin.xyz/api/v1/mining/claim',
                verify_ssl=False, proxy=self.session_proxy if self.session_proxy else None)

            if r.status == 200 or r.status == 201:
                logger.info(
                    f'{self.task_number} | {self.session_name} | mining_claim[{r.status}] | mining claim complete')
                return await r.json(content_type=None)

            elif r.status == 401:
                logger.error(f'{self.task_number} | {self.session_name} | mining_claim[{r.status}] | Session expired')
                self.access_token = None
                await self.get_access_token(client)

            elif r.status == 404:
                logger.error(
                    f'{self.task_number} | {self.session_name} | mining_claim[{r.status}] | mining claim not found')

            else:
                if await r.text() in "Just a moment...":
                    logger.error(
                        f'{self.task_number} | {self.session_name} | mining_claim[{r.status}] | Cloudflare - Just a moment...')
                    self.client = aiocfscrape.CloudflareScraper()
                    await asyncio.sleep(50)
                logger.error(
                    f'{self.task_number} | {self.session_name} | mining_claim[{r.status}] | Unknown response when mining claim , '
                    f'Response: {await r.text()}')
                await asyncio.sleep(10)
                # continue
        except Exception as error:
            logger.error(
                f'{self.task_number} | {self.session_name} | mining_claim[] | Unknown error when mining claim: {error}')

    @access_token_required
    async def upgrade_boost(self, client: aiocfscrape.CloudflareScraper) -> dict:
        client = self.client
        try:
            data = {
                'boostType': 'HAMMER'
            }
            client.headers['Authorization']: str = f'Bearer {self.access_token}'
            r: aiocfscrape.CloudflareScraper = await client.post(
                url='https://api.cyberfin.xyz/api/v1/mining/boost/apply',
                verify_ssl=False, json=data, proxy=self.session_proxy if self.session_proxy else None)

            if r.status == 200 or r.status == 201:
                logger.info(
                    f'{self.task_number} | {self.session_name} | upgrade_boost[{r.status}] | Hammer upgrade complete')
                return await r.json(content_type=None)

            elif r.status == 401:
                logger.error(f'{self.task_number} | {self.session_name} | upgrade_boost[{r.status}] | Session expired')
                self.access_token = None
                await self.get_access_token(client)

            elif r.status == 404:
                logger.error(
                    f'{self.task_number} | {self.session_name} | upgrade_boost[{r.status}] | Hammer upgrade not found')

            else:
                if await r.text() in "Just a moment...":
                    logger.error(
                        f'{self.task_number} | {self.session_name} | mining_claim[{r.status}] | Cloudflare - Just a moment...')
                    self.client = aiocfscrape.CloudflareScraper()
                    await asyncio.sleep(50)
                logger.error(
                    f'{self.task_number} | {self.session_name} | upgrade_boost[{r.status}] | Unknown response when Hammer upgrade, '
                    f'Response: {await r.text()}')
                await asyncio.sleep(10)
                # continue

        except Exception as error:
            logger.error(
                f'{self.task_number} | {self.session_name} | upgrade_boost[] | Unknown error when Hammer upgrade: {error}')

    @access_token_required
    async def check_boosts_and_upgrade(self, client: aiocfscrape.CloudflareScraper, user_balance):
        client = self.client
        try:
            client.headers['Authorization']: str = f'Bearer {self.access_token}'
            r: aiocfscrape.CloudflareScraper = await client.get(
                url='https://api.cyberfin.xyz/api/v1/mining/boost/info',
                verify_ssl=False, proxy=self.session_proxy if self.session_proxy else None)

            if r.status == 200 or r.status == 201:
                data = await r.json(content_type=None)
                message = data.get('message', {})
                logger.info(
                    f'{self.task_number} | {self.session_name} | boosts[{r.status}] | Boost information received')
                if message:
                    hammer_price = message.get(
                        'hammerPrice')  # Предположим, что у вас есть переменная с балансом пользователя
                    if user_balance is not None:
                        if int(user_balance) >= int(hammer_price):
                            await self.upgrade_boost(client)

            elif r.status == 401:
                logger.error(f'{self.task_number} | {self.session_name} | boosts[{r.status}] | Session expired')
                self.access_token = None
                await self.get_access_token(client)

            elif r.status == 404:
                logger.error(f'{self.task_number} | {self.session_name} | boosts[{r.status}] | Boost not found')

            else:
                if await r.text() in "Just a moment...":
                    logger.error(
                        f'{self.task_number} | {self.session_name} | mining_claim[{r.status}] | Cloudflare - Just a moment...')
                    self.client = aiocfscrape.CloudflareScraper()
                    await asyncio.sleep(50)
                logger.error(
                    f'{self.task_number} | {self.session_name} | boosts[{r.status}] | Unknown response when receiving boosts, '
                    f'Response: {await r.text()}')
                await asyncio.sleep(10)
                # continue



        except Exception as error:
            logger.error(
                f'{self.task_number} | {self.session_name} | boosts[] | Unknown error when receiving boosts: {error}')
            traceback.print_exc()

    @access_token_required
    async def complete_mission(self, client: aiocfscrape.CloudflareScraper, mission_uuid: str) -> dict:
        client = self.client
        try:
            client.headers['Authorization']: str = f'Bearer {self.access_token}'
            r: aiocfscrape.CloudflareScraper = await client.patch(
                url=f'https://api.cyberfin.xyz/api/v1/gametask/complete/{mission_uuid}',
                verify_ssl=False, proxy=self.session_proxy if self.session_proxy else None)

            if r.status == 200 or r.status == 201:
                logger.info(
                    f'{self.task_number} | {self.session_name} | complete_gametask[{r.status}] | Mission complete')
                return await r.json(content_type=None)

            elif r.status == 401:
                logger.error(
                    f'{self.task_number} | {self.session_name} | complete_gametask[{r.status}] | Session expired')
                self.access_token = None
                await self.get_access_token(client)

            elif r.status == 404:
                logger.error(
                    f'{self.task_number} | {self.session_name} | complete_gametask[{r.status}] | Mission not found')

            else:
                if await r.text() in "Just a moment...":
                    logger.error(
                        f'{self.task_number} | {self.session_name} | mining_claim[{r.status}] | Cloudflare - Just a moment...')
                    self.client = aiocfscrape.CloudflareScraper()
                    await asyncio.sleep(50)
                else:
                    logger.error(
                        f'{self.task_number} | {self.session_name} | complete_gametask[{r.status}] | Unknown response when complete mission, '
                        f'Response: {await r.text()}')
                    await asyncio.sleep(10)
                # continue



        except Exception as error:
            logger.error(
                f'{self.task_number} | {self.session_name} | complete_gametask[] | Unknown error when complete mission: {error}')

    @access_token_required
    async def check_missions_and_complete(self, client: aiocfscrape.CloudflareScraper):
        client = self.client
        try:
            client.headers['Authorization']: str = f'Bearer {self.access_token}'
            r: aiocfscrape.CloudflareScraper = await client.get(
                url='https://api.cyberfin.xyz/api/v1/gametask/all',
                verify_ssl=False, proxy=self.session_proxy if self.session_proxy else None)

            if r.status == 200 or r.status == 201:
                logger.info(
                    f'{self.task_number} | {self.session_name} | gametask[{r.status}] | Missions information received')
                data = await r.json(content_type=None)
                for item in data['message']:
                    if not item['isCompleted'] and item['isActive']:
                        uuid = item['uuid']
                        if uuid not in exclude_tasks:
                            await self.complete_mission(client, uuid)
                        else:
                            pass
                            # logger.info(
                            #     f'{self.task_number} | {self.session_name} | gametask[{r.status}] | UUID matches an excluded task, skipping the mission.')

            elif r.status == 401:
                logger.error(f'{self.task_number} | {self.session_name} | gametask[{r.status}] | Session expired')
                self.access_token = None
                await self.get_access_token(client)

            elif r.status == 404:
                logger.error(f'{self.task_number} | {self.session_name} | gametask[{r.status}] | Missions not found')

            else:
                if await r.text() in "Just a moment...":
                    logger.error(
                        f'{self.task_number} | {self.session_name} | mining_claim[{r.status}] | Cloudflare - Just a moment...')
                    self.client = aiocfscrape.CloudflareScraper()
                    await asyncio.sleep(50)
                logger.error(
                    f'{self.task_number} | {self.session_name} | gametask[{r.status}] | Unknown response when receiving game data, '
                    f'Response: {await r.text()}')
                await asyncio.sleep(10)
                # continue



        except Exception as error:
            logger.error(
                f'{self.task_number} | {self.session_name} | gametask[] | Unknown error when connecting a squad: {error}')

    @access_token_required
    async def connect_to_squad(self,
                               client: aiocfscrape.CloudflareScraper, squad_uuid: str) -> dict:
        client = self.client
        while True:
            try:
                client.headers['Authorization']: str = f'Bearer {self.access_token}'
                r: aiocfscrape.CloudflareScraper = await client.get(
                    url=f'https://api.cyberfin.xyz/api/v1/squad/connect/{squad_uuid}',
                    verify_ssl=False, proxy=self.session_proxy if self.session_proxy else None)

                if r.status == 200 or r.status == 201:
                    logger.info(f'{self.task_number} | {self.session_name} | squad[{r.status}] | Squad connect')
                    return await r.json(content_type=None)

                elif r.status == 401:
                    logger.error(f'{self.task_number} | {self.session_name} | squad[{r.status}] | Session expired')
                    self.access_token = None
                    await self.get_access_token(client)

                elif r.status == 404:
                    logger.error(f'{self.task_number} | {self.session_name} | squad[{r.status}] | Squad not found')

                else:
                    if await r.text() in "Just a moment...":
                        logger.error(
                            f'{self.task_number} | {self.session_name} | mining_claim[{r.status}] | Cloudflare - Just a moment...')
                        self.client = aiocfscrape.CloudflareScraper()
                        await asyncio.sleep(50)
                    logger.error(
                        f'{self.task_number} | {self.session_name} | squad[{r.status}] | Unknown response when receiving game data, '
                        f'Response: {await r.text()}')
                    await asyncio.sleep(10)
                    # continue



            except Exception as error:
                logger.error(
                    f'{self.task_number} | {self.session_name} | squad[] | Unknown error when connecting a squad: {error}')

    @access_token_required
    async def get_game_data(self,
                            client: aiocfscrape.CloudflareScraper) -> dict:
        client = self.client
        if self.access_token is False:
            return False
        while True:
            try:
                client.headers['Authorization']: str = f'Bearer {self.access_token}'
                r: aiocfscrape.CloudflareScraper = await client.get(
                    url='https://api.cyberfin.xyz/api/v1/game/mining/gamedata',
                    verify_ssl=False, proxy=self.session_proxy if self.session_proxy else None)

                if r.status == 200 or r.status == 201:

                    result = await r.json(content_type=None)
                    await self._suffix(request=result)
                    logger.info(
                        f'{self.task_number} | {self.session_name} | gamedata[{r.status}] | Game data received {self.message_suffix}')
                    return result

                elif r.status == 401:
                    logger.error(f'{self.task_number} | {self.session_name} | gamedata[{r.status}] | Session expired')
                    self.access_token = None
                    await self.get_access_token(client)


                else:
                    if await r.text() in "Just a moment...":
                        logger.error(
                            f'{self.task_number} | {self.session_name} | mining_claim[{r.status}] | Cloudflare - Just a moment...')
                        self.client = aiocfscrape.CloudflareScraper()
                        await asyncio.sleep(50)
                    logger.error(
                        f'{self.task_number} | {self.session_name} | gamedata[{r.status}] | Unknown response when receiving game data, '
                        f'Response: {await r.text()}')
                    await asyncio.sleep(10)
                    # continue



            except Exception as error:
                logger.error(
                    f'{self.task_number} | {self.session_name} | gamedata[] | Unknown error while retrieving game data: {error}')

    async def get_access_token(self,
                               client: aiocfscrape.CloudflareScraper) -> str:
        client = self.client
        while True:
            r: None = None
            tg_web_data: str = await self.get_tg_web_data(session_proxy=self.session_proxy)
            if tg_web_data is False:
                return False

            try:
                r: aiocfscrape.CloudflareScraper = await client.post(url='https://api.cyberfin.xyz/api/v1/game/initdata/',
                                                              json={
                                                                  'initData': json.dumps(tg_web_data)
                                                              },
                                                              verify_ssl=False, proxy=self.session_proxy if self.session_proxy else None)
                logger.critical(await r.json)
                self.access_token = (await r.json(content_type=None))['message']['accessToken']
                logger.info(f'{self.task_number} | {self.session_name} | initdata[{r.status}] | Received access token')
                return self.access_token

            except Exception as error:
                if r:
                    logger.error(
                        f'{self.task_number} | {self.session_name} | Unknown error while retrieving Access Token: {error}, '
                        # f'{self.task_number} | {self.session_name} | Request body: "initData": {tg_web_data}, '
                        f'ответ: {await r.text()}')

                    if r.status == 403:
                        self.is_valid_tg_web_data = False
                    await asyncio.sleep(30)

                else:
                    logger.error(
                        f'{self.task_number} | {self.session_name} | Unknown error while retrieving Access Token: {error}')
                    traceback.print_exc()
                    await asyncio.sleep(30)

    async def get_tg_web_data(self,
                              session_proxy: str | None) -> str | None:
        RETRY_DELAY_MULTIPLIER = 2
        INITIAL_RETRY_DELAY = 10  # seconds
        retry_delay = INITIAL_RETRY_DELAY



        # Check if tg_web_data is valid
        if self.is_valid_tg_web_data:
            tg_web_data = await get_tg_web_data_by_name(session_name=self.session_name)

            if tg_web_data:
                self.tg_web_data = tg_web_data
                logger.info(
                    f"{self.task_number} | {self.session_name} | is valid? {self.is_valid_tg_web_data} | Use tg_web_data from db - {tg_web_data}.")
                return self.tg_web_data
            else:
                logger.info(
                    f"{self.task_number} | {self.session_name} | is valid? {self.is_valid_tg_web_data} | Generate tg_web_data...")
        else:
            logger.info(
                f"{self.task_number} | {self.session_name} | is valid? {self.is_valid_tg_web_data} | tg_web_data invalid...")





        while True:

            try:
                if session_proxy:
                    try:
                        proxy: Proxy = Proxy.from_str(
                            proxy=session_proxy
                        )

                        proxy_dict = dict(proxy_type=socks.SOCKS5, addr=proxy.host, port=proxy.port,
                                          username=proxy.login, password=proxy.password)
                        logger.info(f"{self.task_number} | {self.session_name} | {str(proxy)} | Run")
                        # await check_and_rename_column(self.session_name)


                        client = TelegramClient(session=f"sessions/{self.session_name}",
                                                api_id=config.api_id,
                                                api_hash=config.api_hash,
                                                device_model=config.device,
                                                app_version=config.app_version,
                                                lang_code=config.system_lang_pack,
                                                system_lang_code=config.system_lang_pack, proxy=proxy_dict)

                        try:
                            await client.connect()

                            # Проверяем, успешно ли прошла авторизация
                            if not await client.is_user_authorized():
                                logger.error(
                                    f"{self.task_number} | {self.session_name} | Authorization failed for session {self.session_name}.")
                                await client.disconnect()
                                await asyncio.sleep(500)
                                return False

                            # await client.send_message(entity='psychoopatientt', message=mm, reply_to=161)
                            # Если авторизация прошла успешно, получаем информацию о текущем пользователе
                            logger.info(
                                f"{self.task_number} | {self.session_name} | Authorized successfully for session {self.session_name}")
                            result = await client(functions.messages.RequestWebViewRequest(
                                peer='cyberfinBot',
                                bot='cyberfinBot',
                                platform='windows',
                                from_bot_menu=False,
                                url='https://game.cyberfin.xyz/',
                            ))
                            auth_url: str = result.url
                        except Exception as e:
                            logger.error(
                                f"{self.task_number} | {self.session_name} | Failed to authorize for session {self.session_name}: {e}")
                            await client.disconnect()
                            return False

                        auth_url: str = result.url
                        await client.disconnect()
                        
                        print(auth_url)
                        # Извлекаем часть фрагмента после "#"
                        fragment = auth_url.split('#')[-1]

                        # Декодируем URL-кодированные символы
                        decoded_fragment = unquote(fragment)

                        # Парсим параметры в словарь
                        params = parse_qs(decoded_fragment)

                        # Удаляем 'tgWebAppVersion' и 'tgWebAppPlatform'
                        params.pop('tgWebAppVersion', None)
                        params.pop('tgWebAppPlatform', None)

                        # Удаляем 'tgWebAppData=' префикс и объединяем параметры в строку
                        cleaned_fragment = decoded_fragment.replace('tgWebAppData=', '')
                        cleaned_params = parse_qs(cleaned_fragment)

                        # Объединяем параметры в строку без удаленных ключей
                        final_params = {k: v for k, v in cleaned_params.items() if k not in ['tgWebAppVersion', 'tgWebAppPlatform']}
                        final_string = urlencode(final_params, doseq=True)

                        # Log the updated tg_web_data
                        logger.debug(f"{self.task_number} | {self.session_name} | tg_web_data | {final_string}")

                        # Update the field with the new tg_web_data
                        await set_field_by_name(session_name=self.session_name, field_name="tg_web_data", field_value=final_string)

                        return final_string
                    except Exception as e:
                        logger.error(
                            f"{self.task_number} | {self.session_name} | {e} Retry in {retry_delay} seconds...")
                        traceback.print_exc()
                        await asyncio.sleep(retry_delay)
                        retry_delay *= RETRY_DELAY_MULTIPLIER

                    # await client.send_message(entity='cyberfinBot',
                    #                           message='/start')
                    # noinspection PyTypeChecker

                    # result = await session(functions.messages.RequestWebViewRequest(
                    #     peer='cyberfinBot',
                    #     bot='cyberfinBot',
                    #     platform='windows',
                    #     from_bot_menu=False,
                    #     url='https://game.cyberfin.xyz/',
                    # ))


            except InvalidSession as error:
                raise error

            except Exception as error:
                logger.error(
                    f'{self.task_number} | {self.session_name} | Неизвестная ошибка при авторизации: {error}. Пробую снова через {retry_delay} секунд..')
                traceback.print_exc()
                await asyncio.sleep(retry_delay)
                retry_delay *= RETRY_DELAY_MULTIPLIER

    async def start_farming(self):
        session_proxy: str = await db_actions.get_session_proxy_by_name(session_name=self.session_name)
        try:
            self.session_proxy = session_proxy.strip()

        except Exception as e:
            logger.error(f"{self.task_number} | {self.session_name} | {e}")
            self.session_proxy = session_proxy


        client =  aiocfscrape.CloudflareScraper()
        self.client = client
        while True:

            game_data = await self.get_game_data(client=client)

            if game_data is False:
                print(game_data)
                return

            mining_data = game_data['message'].get('miningData', {})

            timestamp = mining_data.get('crackTime')

            user_data = game_data['message'].get('userData', {})

            balance = user_data.get('balance')

            squad_data = game_data['message'].get('squadData', {})
            request_data_info = game_data['message'].get('requestDataInfo', {})
            code = game_data.get('code')

            balance = user_data.get('balance')

            squad_data = game_data.get('message', {}).get('squadData')
            if squad_data is not None:
                if config.squad_uuid != squad_data.get('uuid'):
                    await self.connect_to_squad(client=client, squad_uuid=config.squad_uuid)
            else:
                await self.connect_to_squad(client=client, squad_uuid=config.squad_uuid)

            await self.check_missions_and_complete(client=client)

            # await self.check_boosts_and_upgrade(client=client, user_balance=balance)

            current_time = time.time()

            if timestamp is not None and timestamp > current_time:
                await asyncio.sleep(timestamp - current_time)
                logger.info(
                    f"{self.task_number} | {self.session_name} | Sleep. Next claim: {minutes_until(timestamp)} min.")
                await self.claim_reward(client=client)
            else:
                logger.info(f"{self.task_number} | {self.session_name} | Timestamp is in the past. Claiming.")
                await self.claim_reward(client=client)


async def start_farming(session_name: str, task_number: int) -> None:
    try:
        await asyncio.sleep(task_number * config.startup_delay)
        await Farming(session_name=session_name, task_number=task_number).start_farming()

    except InvalidSession:
        logger.error(f'{task_number} | {session_name} | Invalid Session')
