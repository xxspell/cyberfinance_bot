import json
import traceback

import aiohttp
import asyncio
import time

from utils.config import load_config
from utils.generator import Utils, headers_base, get_random_user_agent
from utils.logging import logger
from utils.time import minutes_until

class CyberFinance:
    def __init__(self, user_id, proxy, i):
        self.user_id = user_id
        self.i = i
        self.access_token = None
        self.message_prefix = f"[{i}][{self.user_id}] "
        self.message_suffix = None
        self.proxy = proxy
        self.crack_time = None
        self.user_agent = get_random_user_agent()


    def _suffix(self, request):
        response_data = json.loads(request)
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
        self.message_suffix = f"-- B: {balance} | SP: {squad_points} SU: {squad_user_count} SR: {squad_rank} N: {squad_title}| Next claim: {minutes_until(crack_time)} min."
    async def _get(self, url, headers=None, data=None):
        for attempt in range(10):
            try:
                async with aiohttp.ClientSession() as session:
                    headers['User-Agent'] = self.user_agent
                    async with session.get(url, headers=headers, proxy=self.proxy) as response:
                        response_text = await response.text()
                       # logger.debug(f"{self.message_prefix} GET - {url}", response=response_text, status=response.status)
                        return response_text, response.status
            except aiohttp.ClientProxyConnectionError:
                pass
            except aiohttp.client_exceptions.ClientHttpProxyError:
                pass
            except aiohttp.ClientResponseError:
                pass
            except aiohttp.ClientError:
                pass
            await asyncio.sleep(5)
        return None, None

    async def _post(self, url, headers=None, data=None):
        for attempt in range(10):
            try:
                async with aiohttp.ClientSession() as session:
                    headers['User-Agent'] = self.user_agent
                    async with session.post(url, headers=headers, data=data, proxy=self.proxy) as response:
                        response_text = await response.text()
                        # logger.debug(f"{self.message_prefix} POST - {url}", response=response_text, status=response.status)
                        return response_text, response.status
            except aiohttp.ClientProxyConnectionError:
                pass
            except aiohttp.client_exceptions.ClientHttpProxyError:
                pass
            except aiohttp.ClientResponseError:
                pass
            except aiohttp.ClientError:
                pass
            await asyncio.sleep(5)
        return None, None

    async def init_game(self):
        payload = json.dumps({
            "query_id": Utils.generate_random_string(20),
            "user": {
                "id": self.user_id,
                "first_name": Utils.generate_random_string(5),
                "last_name": Utils.generate_random_string(5),
                "username": Utils.generate_random_string(7),
                "language_code": "ru",
                "allows_write_to_pm": True
            },
            "auth_date": int(time.time()),
            "hash": Utils.generate_random_hash(64)
        })
        headers = headers_base
        request, code = await self._post('https://api.cyberfinance.xyz/api/v1/game/init', headers=headers, data=payload)
        # print(code, request)
        if code == 200 or code == 201:
            self.access_token = json.loads(request)['message']['accessToken']
            # logger.debug(f"{self.message_prefix} Logged")
            return request
        elif code == 400:
            logger.error(f"{self.message_prefix} 400 error not logged {self.message_suffix}", request=request, code=code)
            return False
        elif code == 403:
            logger.error(f"{self.message_prefix} 403 error not logged  {self.message_suffix}", request=request, code=code)
            return False



    async def apply_boost(self, boost_type):
        if not self.access_token:
            await self.init_game()

        headers = headers_base
        headers['authorization'] = f'Bearer {self.access_token}'

        if boost_type == "hammer":
            payload = {
                'boostType': 'HAMMER'
            }
        elif boost_type == "egg":
            payload = {
                'boostType': 'EGG'
            }
        else:
            logger.error(f"{self.message_prefix} value err")

        request, code = await self._post('https://api.cyberfinance.xyz/api/v1/mining/boost/apply', headers=headers, data=json.dumps(payload))
        if code == 200 or code == 201:
            return True, request
        elif code == 400:
            return False, request
        elif code == 401:
            # Если получен код 401, повторно вызываем функцию apply_boost
            logger.error(f"{self.message_prefix} Got 401 error. Retrying... {request}")
            await asyncio.sleep(10)
            await self.init_game()
            return await self.apply_boost(boost_type)

    async def connect_to_squad(self, squad_uuid):
        if not self.access_token:
            await self.init_game()

        headers = headers_base
        headers['authorization'] = f'Bearer {self.access_token}'

        url = f'https://api.cyberfinance.xyz/api/v1/squad/connect/{squad_uuid}'
        request, code = await self._get(url, headers=headers)
        if code == 200 or code == 201:
            return True, request
        elif code == 401:
            # Если получен код 401, повторно вызываем функцию apply_boost
            logger.error(f"{self.message_prefix} connect Got 401 error. Retrying... {request}")
            await asyncio.sleep(10)
            await self.init_game()
            return await self.connect_to_squad(squad_uuid)

    async def get_game_data(self):
        if not self.access_token:
            await self.init_game()

        headers = headers_base
        headers['authorization'] = f'Bearer {self.access_token}'

        request, code = await self._get('https://api.cyberfinance.xyz/api/v1/game/mining/gamedata', headers=headers)
        if code == 200 or code == 201:
            self._suffix(request)

            return True, request
        elif code == 401:
            # Если получен код 401, повторно вызываем функцию apply_boost
            logger.error(f"{self.message_prefix} gamedata Got 401 error. Retrying... {request}")
            await asyncio.sleep(10)
            await self.init_game()
            return await self.get_game_data()

    async def claim_reward(self):
        if not self.access_token:
            await self.init_game()

        headers = headers_base
        headers['authorization'] = f'Bearer {self.access_token}'

        request, code = await self._get('https://api.cyberfinance.xyz/api/v1/mining/claim', headers=headers)
        if code == 200:
            mining_data, code = await self.get_game_data()
            logger.info(f"{self.message_prefix} Claimed {self.message_suffix}")
            return True
        elif code == 401:
            # Если получен код 401, повторно вызываем функцию apply_boost
            logger.error(f"{self.message_prefix} claim Got 401 error. Retrying... {request} ")
            await asyncio.sleep(10)
            await self.init_game()
            return await self.claim_reward()
        else:
            mining_data, _code = await self.get_game_data()
            logger.error(f"{self.message_prefix} Got {code} error. ", mining_data=mining_data, _code=_code, request=request)
            return False


async def start_farming(user_id, proxy, task_number):
    count = 1
    error_count = 1
    config_data = load_config("config.json")
    squad_id = config_data.get("squad_id")
    await asyncio.sleep(task_number * 0.1)
    logger.debug(f"Start | {task_number} | {proxy} | {user_id}")
    cf = CyberFinance(user_id, proxy, task_number)
    try:

        await cf.init_game()
        await cf.connect_to_squad(squad_id)
        await cf.get_game_data()

    except:
        pass
    while True:
        try:
            timestamp = cf.crack_time
            current_time = time.time()

            try:
                timestamp = cf.crack_time
                current_time = time.time()

                if timestamp is not None and timestamp > current_time:
                    await asyncio.sleep(timestamp - current_time)
            except TypeError as e:
                print(f"Error: {e}. Get game gata")
                await cf.get_game_data()
                # Можно выполнить какие-то дополнительные действия здесь

            await cf.claim_reward()
            count =+ 1
            # logger.info(f"{cf.message_prefix} While {count} complete {cf.message_suffix}")
        except Exception as e:

            logger.error(f"{cf.message_prefix} An error occurred: {e}. Retrying in {10 * error_count} secs...")
            logger.error(traceback.format_exc())
            await asyncio.sleep(10 * error_count)
            error_count = + 1

