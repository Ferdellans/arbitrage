import asyncio
import hashlib
import json
import logging
import time

from cryptobot import const
from cryptobot.common.compress import inflate

from . import BaseExchange

logger = logging.getLogger(__name__)


class OKCoinMixin:

    def pair_local2okcoin(self, name):
        """ BTCUSD -> btc_usd"""
        fsym, tsym = name[0:3], name[3:]
        return '{}_{}'.format(tsym, fsym).lower()

    def pair_okcoin2local(self, name):
        """ ok_sub_spotbtc_usd_trade -> BTCUSD"""
        fsym = name.replace('_', '')[9:12]
        tsym = name.replace('_', '')[12:15]
        return "{}{}".format(tsym, fsym).upper()
    pass


class OKCoin(BaseExchange, OKCoinMixin):
    title = 'OKCoin'
    name = 'okcoin'
    signature_key = 'sign'
    periodical_interval = 3
    protocol = BaseExchange.WEBSOCKET

    async def ws_recv(self):
        data = await self.ws.recv()
        try:
            return json.loads(data)
        except:
            return json.loads(inflate(data))

    async def ws_consumer(self):
        while self.is_running:
            messages = await self.ws_recv()
            if not isinstance(messages, list):
                messages = [messages]
            for message in messages:
                asyncio.ensure_future(self.consumer(message))

    async def consumer(self, message: dict):
        assert isinstance(message, dict), message
        if 'channel' not in message:
            return
        channel_name = message.pop('channel')

        fn = getattr(self, 'consume_{}'.format(channel_name), None)
        if fn:
            await fn(**message['data'])
            return
        fn = self.channels.get(channel_name, None)
        if fn:
            await fn(message['data'])
            return
        logger.info("Skip read channel_name {}".format(channel_name))

    async def produce_ping(self):
        logger.debug("ping")
        payload = {
            'event': 'ping',
        }
        await self.ws_send(payload)

    async def periodical(self):
        await self.produce_ping()

    def gen_update_pair_fn(self, pair: str):
        async def fn(data: list):
            bid = self.pairs[pair].get('bid')
            ask = self.pairs[pair].get('ask')
            min_size = self._env.cfg['pairs'].get(pair, 2)
            bid_size = 0
            ask_size = 0
            for item in data:
                if float(item[2]) < min_size:
                    continue
                if item[-1] == 'bid':
                    _, bid, bid_size, _, _ = item
                else:
                    _, ask, ask_size, _, _ = item
            if not bid or not ask:
                return
            await self.on_currency_update(
                pair=pair,
                bid_size=float(bid_size), bid=float(bid),
                ask_size=float(ask_size), ask=float(ask),
            )

        return fn

    async def consume_addChannel(self, result: bool, channel: str, **kw):
        pair = self.pair_okcoin2local(channel)
        logger.info("Subscribed to {}".format(pair))
        self.channels[channel] = self.gen_update_pair_fn(pair)

    async def produce_subscribe_pair(self, pair: str):
        logger.info("Subscribe to {} ticker".format(pair))
        pair = self.pair_local2okcoin(pair)
        payload = {
            'event': 'addChannel',
            'channel': 'ok_sub_spot{}_trades'.format(pair),
            'binary': 'true'
        }
        await self.ws_send(payload)

    def sign(self, tbs, kwargs):
        secret_key = self.config['secret']
        qs = '&'.join(['{}={}'.format(key, kwargs[key]) for key in sorted(tbs)]) + '&secret_key=' + secret_key
        signature = hashlib.md5(qs.encode()).hexdigest().upper()
        kwargs[self.signature_key] = signature
        return kwargs

    async def place_order(self, pair: str, operation: str, amount: float, price: float=0) -> bool:
        assert operation in [const.SELL, const.BUY]
        pair = self.pair_local2okcoin(pair)
        tbs = ['api_key', 'symbol', 'type', 'price', 'amount']

        result = await self.post(
            '/trade.do',
            tbs=tbs,
            api_key=self.config['key'],
            symbol=pair,
            type='{}_market'.format(operation),
            price=price,
            json=False,
            amount=amount
        )

        result = json.loads(result)
        if 'error_code' in result:
            logger.error(
                "Error make order — {}/{} for {} * {} (extra: {})"
                .format(pair, operation, amount, price if price else 'auto', result)
            )
            return
        order_id = result['order_id']
        logger.info("Succesful place order {} — {}/{} for {} * {}"
                    .format(order_id, pair, operation, amount, price if price else 'auto'))

    async def authorization(self) -> bool:
        logger.info('skip auth')
        self.channels = {}
        return True


export = OKCoin
