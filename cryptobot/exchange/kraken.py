import asyncio
import hashlib
import hmac
import logging
import time
from urllib.parse import urlencode

import aiohttp
import krakenex
from cryptobot import const

from . import BaseExchange

logger = logging.getLogger(__name__)


class KrakenMixin:
    mapping_pair = (
        ('BTCUSD', 'XXBTZUSD'),
        ('LTCUSD', 'XLTCZUSD'),
        ('ETHUSD', 'XETHZUSD'),
        ('ETCUSD', 'XETCZUSD'),
        ('ETHBTC', 'XETHXXBT'),
        ('LTCBTC', 'XLTCXXBT'),
        ('ZECUSD', 'XZECZUSD'),
        ('XMRUSD', 'XXMRZUSD'),
        ('DASHUSD', 'DASHUSD'),
    )

    local2kraken = {
        l: r
        for (l, r) in mapping_pair
    }

    kraken2local = {
        l: r
        for (l, r) in mapping_pair
    }

    def pair_local2kraken(self, name):
        assert name in self.local2kraken, name
        return self.local2kraken[name]

    def pair_kraken2local(self, name):
        assert name in self.kraken2local, name
        return self.kraken2local[name]

    pass


class Kraken(BaseExchange, KrakenMixin):
    title = 'Kraken'
    name = 'kraken'
    protocol = BaseExchange.REST

    async def process_subscribe_pair(self, pair, value):
        min_size = self._env.cfg['pairs'].get(pair, 2)

        bid = ask = bid_size = ask_size = 0
        for item in value['asks']:
            if float(item[1]) > min_size:
                ask = float(item[0])
                ask_size = float(item[1])
                break

        for item in value['bids']:
            if float(item[1]) > min_size:
                bid = float(item[0])
                bid_size = float(item[1])
                break

        if not bid or not ask:
            return

        await self.on_currency_update(
            pair=pair,
            bid_size=bid_size, bid=bid,
            ask_size=ask_size, ask=ask,
        )

    async def produce_subscribe_pair(self, pair: str):
        logger.info("Subscribe to {} ticker".format(pair))
        while self._env.loop.is_running():
            try:
                remote_pair = self.pair_local2kraken(pair)
                result = await self.rest_call(
                    '/public/Depth', 'GET',
                    pair=remote_pair
                )
                assert result['result'], result
                await self.process_subscribe_pair(pair, result['result'][remote_pair])
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

        async def get_balance(self):
            pass


export = Kraken
