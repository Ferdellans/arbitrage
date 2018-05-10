import hashlib
import hmac
import logging
import time
from base64 import b64encode
from json import dumps

import aiohttp

from cryptobot import const

from . import BaseExchange

logger = logging.getLogger(__name__)


class Bitfinex(BaseExchange):
    title = 'Bitfinex'
    name = 'bitfinex'
    protocol = BaseExchange.WEBSOCKET

    def __init__(self, env:
        self.channels = {}
        dict, config

    async def consumer(self, message: dict):
        if isinstance(message, dict):
            """ Try to handle event """

            event_name = message.pop('event')
            fn = getattr(self, 'consume_{}'.format(event_name), None)
            if not fn:
                logger.info("Skip read event {}".format(message))
                return
            await fn(**message)

        elif isinstance(message, list) and len(message) == 2 and len(message[1]) == 10:
            """ Try to handle channel message """

            chanId = message[0]
            fn = self.channels.get(chanId, None)
            if not fn:
                logger.info("Skip read channel update {}".format(message))
                return
            await fn(*message[1:])

        elif isinstance(message, list) and len(message) == 2 and message[1] == 'hb':
            """ Skip ping """
            return

        elif isinstance(message, list) and len(message) == 3:
            """ Skip info """
            return

        else:
            """ Skip unknown message and log"""
            logger.info("Skip read message {}".format(message))

        pass

    def gen_update_pair_fn(self, pair: str):
        """
            BID float   Price of last highest bid
            BID_SIZE    float   Size of the last highest bid
            ASK float   Price of last lowest ask
            ASK_SIZE    float   Size of the last lowest ask
            DAILY_CHANGE    float   Amount that the last price has changed since yesterday
            DAILY_CHANGE_PERC   float   Amount that the price has changed expressed in percentage terms
            LAST_PRICE  float   Price of the last trade.
            VOLUME  float   Daily volume
            HIGH    float   Daily high
            LOW float
        """
        min_size = self._env.cfg['pairs'].get(pair, 2)

        async def fn(ticker: list):
            (bid, bid_size, ask, ask_size, _, _, _, _, _, _) = ticker
            if bid_size < min_size or ask_size < min_size:
                return

            await self.on_currency_update(
                pair=pair,
                bid_size=float(bid_size), bid=float(bid),
                ask_size=float(ask_size), ask=float(ask),
            )

        return fn

    async def consume_subscribed(self, chanId: int, pair: str, **kw):
        logger.info("Subscribed to {}".format(pair))
        self.channels[chanId] = self.gen_update_pair_fn(pair)

    async def produce_subscribe_pair(self,  pair: str):
        logger.info("Subscribe to {} ticker".format(pair))
        payload = {
            "event": "subscribe",
            "channel": "ticker",
            "pair": pair
        }
        await self.ws_send(payload)

    async def rest_call(self, endpoint, method, json=True, tbs=None, **kwargs):
        url = self.config['rest'] + endpoint

        with aiohttp.ClientSession() as session:
            kwargs = dict({
                'request': '/v1' + endpoint,
                'nonce': str(time.time() * 1000000),
                'exchange': 'bitfinex',
            }, **dict([[key, str(value)] for (key, value) in kwargs.items()]))
            payload = dumps(kwargs)
            payload = b64encode(payload.encode())
            auth_sig = hmac.new(self.config['secret'].encode(), payload, hashlib.sha384).hexdigest()
            logger.debug("http request {}".format(url))
            headers = {
                'X-BFX-APIKEY': self.config['key'],
                'X-BFX-PAYLOAD': payload.decode(),
                'X-BFX-SIGNATURE': auth_sig
            }
            call = session.post(url, headers=headers)

            async with call as resp:
                return await resp.json()

    async def place_order(self, pair: str, operation: str, amount: float, price: float=0) -> bool:
        assert operation in [const.SELL, const.BUY]

        result = await self.post(
            '/order/new',
            api_key=self.config['key'],
            symbol=pair,
            side=operation,
            type='exchange market',
            price=price,
            amount=amount
        )
        if 'message' in result:
            logger.error(
                "Error make order — {}/{} for {} * {} (extra: {})"
                .format(pair, operation, amount, price if price else 'auto', result)
            )
            return
        order_id = result['order_id']
        logger.info("Succesful place order {} — {}/{} for {} * {}"
                    .format(order_id, pair, operation, amount, price if price else 'auto'))

    async def authorization(self):
        logger.info('auth')
        nonce = str(int(time.time() * 1000000))
        auth_string = 'AUTH' + nonce
        auth_sig = hmac.new(self.config['secret'].encode(),
                            auth_string.encode(), hashlib.sha384).hexdigest()

        result = await self.ws_recv()
        if result['version'] != 2:
            raise NotImplemented

        payload = {
            'event': 'auth',
            'apiKey': self.key,
            'authSig': auth_sig,
            'authPayload': auth_string,
            'authNonce': nonce
        }
        await self.ws_send(payload)

        result = await self.ws_recv()
        if result['status'] == 'FAILED':
            logger.info('auth error codeId is {}, msg is {}'.format(result['code'], result['msg']))
            return False

        return True


export = Bitfinex
