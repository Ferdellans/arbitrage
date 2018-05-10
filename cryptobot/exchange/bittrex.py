import asyncio
import hashlib
import hmac
import logging
import time
from urllib.parse import urlencode

import aiohttp

from cryptobot import const

from . import BaseExchange

logger = logging.getLogger(__name__)


class BittrexMixin:
    def pair_local2bittrex(self, name):
        """ BTCUSD -> BTC-USD"""

        def usd_to_usdt(sym):
            if sym == 'USD':
                return 'USDT'
            return sym

        fsym, tsym = usd_to_usdt(name[0:3]), usd_to_usdt(name[3:])
        return '{}-{}'.format(tsym, fsym).upper()

    def pair_bittrex2local(self, name):
        """ ok_sub_spotbtc_usd_trade -> BTCUSD"""

        def usd_to_usdt(sym):
            if sym == 'USD':
                return 'USDT'

        fsym = name.replace('_', '')[9:12]
        tsym = name.replace('_', '')[12:15]
        return "{}{}".format(fsym, tsym).upper()

    pass


class Bittrex(BaseExchange, BittrexMixin):
    title = 'Bittrex'
    name = 'bittrex'
    protocol = BaseExchange.REST

    async def process_subscribe_pair(self, pair, buy, sell):
        bid = ask = bid_size = ask_size = 0
        min_size = self._env.cfg['pairs'].get(pair, 2)

        for item in buy or []:
            if item['Quantity'] < min_size:
                continue
            bid_size = item['Quantity']
            bid = item['Rate']
            break

        for item in sell or []:
            if item['Quantity'] < min_size:
                continue
            ask_size = item['Quantity']
            ask = item['Rate']
            break

        if not bid or not ask:
            return

        await self.on_currency_update(
            pair=pair,
            bid_size=float(bid_size), bid=float(bid),
            ask_size=float(ask_size), ask=float(ask),
        )

    async def produce_subscribe_pair(self, pair: str):
        logger.info("Subscribe to {} ticker".format(pair))
        while self._env.loop.is_running():
            try:
                result = await self.rest_call(
                    '/public/getorderbook', 'GET',
                    tbs=None,
                    type='both',
                    market=self.pair_local2bittrex(pair)
                )
                if not result['success']:
                    return
                # assert result['success'], [result, pair]
                await self.process_subscribe_pair(pair, **result['result'])
            except:
                logger.exception("Error update")
            finally:
                await asyncio.sleep(self.config.get('interval', 5))

    async def rest_call(self, endpoint, method, json=True, tbs=None, **kwargs):
        url = self.config['rest'] + endpoint
        nonce = str(int(time.time() * 1000))

        with aiohttp.ClientSession() as session:
            url += '?apikey=' + self.config['key'] + "&nonce=" + nonce + '&'
            url += urlencode(kwargs)

            signature = hmac.new(self.config['secret'].encode(),
                                 url.encode(),
                                 hashlib.sha512).hexdigest()

            headers = {"apisign": signature}
            call = session.get(url, headers=headers)

            async with call as resp:
                return await resp.json()

    async def place_order(self, pair: str, operation: str, amount: float, price: float = 0) -> bool:
        assert operation in [const.SELL, const.BUY]
        pair = self.pair_local2bittrex(pair)

        result = await self.get(
            '/market/buylimit' if operation == const.BUY else '/market/selllimit',
            market=pair,
            rate=price,
            quantity=amount,
            tbs=['apikey', 'nonce', 'market', 'rate', 'quantity']
        )
        if not result['success']:
            logger.error(
                "Error make order — {}/{} for {} * {} (extra: {})"
                    .format(pair, operation, amount, price if price else 'auto', result)
            )
            return
        order_id = result['order_id']
        logger.info("Successful place order {} — {}/{} for {} * {}"
                    .format(order_id, pair, operation, amount, price if price else 'auto'))


export = Bittrex
