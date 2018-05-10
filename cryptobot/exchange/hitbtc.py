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


class HitBTC(BaseExchange):
    title = 'HitBTC'
    name = 'hitbtc'
    protocol = BaseExchange.WEBSOCKET

    async def consumer(self, message: dict):
        if 'MarketDataSnapshotFullRefresh' in message:
            return await self.consume_full_refresh(**message['MarketDataSnapshotFullRefresh'])
        elif 'MarketDataIncrementalRefresh' in message:
            return await self.consume_full_refresh(**message['MarketDataIncrementalRefresh'])

        else:
            """ Skip unknown message and log"""
            logger.info("Skip read message {}".format(message))

        pass

    async def consume_full_refresh(self, symbol: str, ask: list, bid: list, **kw):
        if not ask or not bid:
            return
        await self.on_currency_update(
            pair=symbol,
            bid_size=float(ask[0]['size']), bid=float(bid[0]['price']),
            ask_size=float(bid[0]['size']), ask=float(ask[0]['price']),
        )

    async def produce_subscribe_pair(self, pair: str):
        self.pairs[pair] = dict()
        pass

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

            if method.lower() == 'get':
                call = session.get(url, headers=headers)
            else:
                call = session.post(url, headers=headers)

            async with call as resp:
                return await resp.json()

    async def place_order(self, pair: str, operation: str, amount: float, price: float = 0) -> bool:
        assert operation in [const.SELL, const.BUY]
        return

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

    async def get_balance(self):
        pass

    async def authorization(self):
        logger.info('skip')
        return True


export = HitBTC
