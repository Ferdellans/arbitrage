import asyncio
import json
import logging
import time
from collections import defaultdict
from urllib.parse import urlencode

import aiohttp

import websockets
from cryptobot import const
from cryptobot.db import table_trade_history
from cryptobot.common.manager import BaseManager

logger = logging.getLogger(__name__)


class WebsocketMixin:
    WEBSOCKET = const.WEBSOCKET

    def __init__(self):
        self.ws = None
        self.subscribed_pairs = []
        self.is_running = False

    async def ws_recv(self):
        return json.loads(await self.ws.recv())

    async def ws_send(self, data):
        return await self.ws.send(json.dumps(data))

    async def ws_consumer(self):
        while self.is_running:
            message = await self.ws_recv()
            await self.consumer(message)

    async def transport_check(self):
        await self.ws.ping()

    async def run_websocket(self, **kwargs):
        assert self.config.get('websocket', None)
        endpoint = self.config['websocket']
        logger.info('{} run'.format(self.title))

        async def connect():

            async with websockets.connect(endpoint, **kwargs) as ws:
                self.ws = ws

                result = await self.authorization()

                if not result:
                    return
                self.is_running = True

                consumer_task = asyncio.ensure_future(self.ws_consumer())
                producer_task = asyncio.ensure_future(self._producer())
                periodical_task = asyncio.ensure_future(self._periodical())

                done, pending = await asyncio.wait(
                    [consumer_task, producer_task, periodical_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()

        while self.env.loop.is_running():
            try:
                logger.info('{} connect'.format(self.title))
                await connect()
            except:
                logger.exception("Error")
            finally:
                logger.info('{} sleep'.format(self.title))
                await asyncio.sleep(30)
                logger.info('{} reconnect'.format(self.title))
                self.ws = None
                self.subscribed_pairs = []


class RestMixin:
    REST = const.REST
    signature_key = 'token'

    def get(self, endpoint, json=True, tbs=None, **kwargs):
        return self.rest_call(endpoint, method='get', json=json, tbs=tbs, **kwargs)

    def post(self, endpoint, json=True, tbs=None, **kwargs):
        return self.rest_call(endpoint, method='post', json=json, tbs=tbs, **kwargs)

    def sign(self, tbs, kwargs):
        raise NotImplemented

    async def rest_call(self, endpoint, method, json=True, tbs=None, **kwargs):
        if tbs:
            kwargs = self.sign(tbs, kwargs)
        url = self.config['rest'] + endpoint

        with aiohttp.ClientSession() as session:
            if method.lower() == 'get':
                qs = urlencode(kwargs)
                url = url + '?' + qs
                logger.debug("http request {}".format(url))
                call = session.get(url)
            elif json:
                logger.debug("http request json {} {}".format(url, kwargs))
                call = session.post(url, data=kwargs)
            else:
                qs = urlencode(kwargs)
                logger.debug("http request {} qs".format(url, qs))
                call = session.post(url, data=qs, headers={'Content-Type': 'application/x-www-form-urlencoded'})

            async with call as resp:
                if json:
                    fn = resp.json
                else:
                    fn = resp.text
                return await fn()

    async def run_rest(self, **kwargs):
        logger.info('{} run'.format(self.title))
        self.is_running = True
        while self.env.loop.is_running():
            producer_task = asyncio.ensure_future(self._producer())
            periodical_task = asyncio.ensure_future(self._periodical())

            done, pending = await asyncio.wait(
                [producer_task, periodical_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()
        self.is_running = False


class BaseExchange(WebsocketMixin, RestMixin):
    is_running = False
    periodical_interval = 60

    def __init__(self, env: dict, config: dict):
        self._env = self.env = env
        self.config = config
        self.key = config['key']
        self.secret = config['secret']
        self.queue = asyncio.Queue()
        self.subscribed_pairs = list()
        self.pairs = defaultdict(dict)
        self.ws = None

    @property
    def title(self):
        raise NotImplemented

    name = title

    async def consumer(self, message):
        logger.info("{} skip read {}".format(self.title, message))

    async def periodical(self):
        logger.info("{} skip periodical".format(self.title))

    async def transport_check(self):
        return

    async def _periodical(self):
        while self.is_running:
            try:
                await self.transport_check()
                await self.periodical()
            except:
                logger.exception("Error")
            finally:
                await asyncio.sleep(self.periodical_interval)

    async def _producer(self):
        while self.is_running:
            message = await self.queue.get()
            action = message.pop('action')
            fn = getattr(self, 'produce_{}'.format(action), None)
            if not fn:
                logger.info("{} skip write {}, producer not found".format(self.title, message))
                continue
            asyncio.ensure_future(fn(**message))

    async def schedule_fetch_currency(self, pair):
        if pair not in self.subscribed_pairs:
            self.subscribed_pairs.append(pair)
            await self.queue.put({'action': const.SUBSCRIBE_PAIR, 'pair': pair})
        period = time.time() - self.config.get('period', 60)
        if pair in self.pairs and 'time' in self.pairs[pair] and self.pairs[pair]['time'] > period:
            return self.pairs[pair]

    async def run(self):
        logger.info('Run {} client for {}'.format(self.protocol, self.title))
        if self.protocol == const.WEBSOCKET:
            await self.run_websocket()
        elif self.protocol == const.REST:
            await self.run_rest()
        else:
            raise NotImplemented

    async def on_currency_update(self, pair: str, bid_size: float, ask_size: float, bid: float, ask: float):
        assert isinstance(bid_size, float), bid_size
        assert isinstance(ask_size, float), ask_size
        assert isinstance(bid, float), bid
        assert isinstance(ask, float), ask
        assert isinstance(pair, str), pair
        item = {
            'bid_size': bid_size,
            'ask_size': ask_size,
            'bid': bid,
            'ask': ask,
        }
        self.pairs[pair] = dict(item, time=time.time())

        async with self.env.db.acquire() as conn:
            insert = table_trade_history.insert().values(exchange=self.name, pair=pair, **item)
            await conn.execute(insert)
        message = "{} Update pair: {} — bid: {}, ask: {}".format(self.title, pair, bid, ask)
        logger.debug(message)

    async def place_order(self, pair: str, operation: str, amount: float, price: float = 0) -> bool:
        raise NotImplemented()

    # todo: test
    async def get_balance(self):
        raise NotImplemented()

    protocol = title


class ExchangeManager(BaseManager):
    CACHE = {}
    RUN = {}
    import_mask = "cryptobot.exchange.{}"

    def get(self, name: str):
        cls = super(ExchangeManager, self).get(name)
        assert cls, [cls, name]
        assert cls.name == name, name
        if name not in self.RUN:
            inst = cls(self._env, self._env.cfg['exchanges'][name])
            asyncio.ensure_future(inst.run())
            self.RUN[name] = inst
        return self.RUN[name]
