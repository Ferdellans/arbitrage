import hashlib
import hmac
import json
import logging
import time

from cryptobot.common.compress import deflate
from cryptobot.common.compress import inflate
from websockets.client import WebSocketClientProtocol

from . import BaseExchange

logger = logging.getLogger(__name__)


class Poloniex(BaseExchange):
    title = 'Poloniex'
    name = 'poloniex'
    protocol = BaseExchange.WEBSOCKET

    async def run_websocket(self):
        return await super(Poloniex, self).run_websocket(subprotocols=['wamp.2.json'])

    async def recv(self):
        data = await self.ws.recv()
        import ipdb
        ipdb.set_trace()

    async def send(self, payload):
        print(self, 'send', payload)
        data = deflate(json.dumps(payload))
        data = await self.ws.send(data)
        import ipdb
        ipdb.set_trace()

    async def consumer(self, message: dict):
        if isinstance(message, dict):
            event_name = message.pop('event')
            fn = getattr(self, 'consume_{}'.format(event_name), None)
            if not fn:
                logger.info("Skip read event {}".format(message))
                return
            await fn(ws, **message)
        elif isinstance(message, list) and len(message) == 2 and len(message[1]) == 10:
            chanId = message[0]
            fn = self.channels.get(chanId, None)
            if not fn:
                logger.info("Skip read channel update {}".format(message))
                return
            await fn(ws, *message[1:])
        elif isinstance(message, list) and len(message) == 2 and message[1] == 'hb':
            return
        elif isinstance(message, list) and len(message) == 3:
            return
        else:
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
        async def fn(ticker: list):
            (bid, bid_size, ask, ask_size, _, _, _, _, _, _) = ticker
            self.pairs[pair] = {'bid': bid, 'ask': ask, 'time': time.time()}
            logger.info("Update pair: {} — bid: {}, ask: {}".format(pair, bid, ask))

        return fn

    async def consume_subscribed(self, chanId: int, pair: str, **kw):
        logger.info("Subscribed to {}".format(pair))
        self.channels[chanId] = self.gen_update_pair_fn(pair)

    async def produce_subscribe_pair(self, pair: str):
        logger.info("Subscribe to {} ticker".format(pair))
        payload = {
            "event": "subscribe",
            "channel": "ticker",
            "pair": pair
        }
        await self.send(payload)

    async def authorization(self):
        logger.info('auth')
        nonce = str(int(time.time() * 1000000))
        auth_string = 'AUTH' + nonce
        auth_sig = hmac.new(self.config['secret'].encode(),
                            auth_string.encode(), hashlib.sha384).hexdigest()

        # result = json.loads(await self.recv())
        # if result['version'] != 2:
        #     raise NotImplemented

        payload = {
            'event': 'auth',
            'apiKey': self.key,
            'authSig': auth_sig,
            'authPayload': auth_string,
            'authNonce': nonce
        }
        import ipdb
        ipdb.set_trace()
        await self.send(payload)

        result = json.loads(await self.recv())
        if result['status'] == 'FAILED':
            logger.info('auth error codeId is {}, msg is {}'.format(result['code'], result['msg']))
            return False

        self.channels = {}
        return True


export = Poloniex
