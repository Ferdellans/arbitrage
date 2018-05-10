import asyncio
import logging
from collections import defaultdict
from time import time

from cryptobot import const

from . import BaseStrategy

logger = logging.getLogger(__name__)

LAST_SEND = defaultdict(int)


class Arbitrage(BaseStrategy):
    title = 'Arbitrage'

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    def __init__(self, name, env, config):
        super().__init__(name, env, config)
        self.pairs = defaultdict(dict)

    async def update_ticker(self):
=======
    async def update_ticker(self):
        self.pairs = defaultdict(dict)
>>>>>>> 115ca544ed61eecbc7442405e22bdd33be0bf931
=======
    async def update_ticker(self):
        self.pairs = defaultdict(dict)
>>>>>>> 115ca544ed61eecbc7442405e22bdd33be0bf931
=======
    async def update_ticker(self):
        self.pairs = defaultdict(dict)
>>>>>>> 115ca544ed61eecbc7442405e22bdd33be0bf931
=======
    async def update_ticker(self):
        self.pairs = defaultdict(dict)
>>>>>>> 115ca544ed61eecbc7442405e22bdd33be0bf931
=======
    async def update_ticker(self):
        self.pairs = defaultdict(dict)
>>>>>>> 115ca544ed61eecbc7442405e22bdd33be0bf931
        for pair in self.config['pairs']:
            for exchange_name in self.config['exchanges']:
                exchange = self._env.exchange_manager.get(exchange_name)
                self.pairs[pair][exchange.name] = await exchange.schedule_fetch_currency(pair)

    async def make_order(self):
        logger.info("Finding best exchange")
        for (pair, pair_exchanges) in self.pairs.items():
            bid_volume = biggest_bid_exchange = biggest_bid = None
            ask_volume = lower_ask_exchange = lower_ask = None

            for (exchange_name, price) in pair_exchanges.items():
                if not price:
                    continue
                if not biggest_bid or (price['bid']) > biggest_bid:
                    biggest_bid = price['bid']
                    bid_volume = price['bid_size']
                    biggest_bid_exchange = exchange_name
                if not lower_ask or price['ask'] < lower_ask:
                    lower_ask = price['ask']
                    ask_volume = price['ask_size']
                    lower_ask_exchange = exchange_name

            if not biggest_bid_exchange or not lower_ask_exchange:
                continue

            volume = ask_volume if ask_volume and ask_volume < bid_volume else bid_volume
            bid_exchange_inst = self._env.exchange_manager.get(biggest_bid_exchange)
            ask_exchange_inst = self._env.exchange_manager.get(lower_ask_exchange)
            fee = bid_exchange_inst.config.get('fee', 0.95)

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> 115ca544ed61eecbc7442405e22bdd33be0bf931
=======
>>>>>>> 115ca544ed61eecbc7442405e22bdd33be0bf931
=======
>>>>>>> 115ca544ed61eecbc7442405e22bdd33be0bf931
=======
>>>>>>> 115ca544ed61eecbc7442405e22bdd33be0bf931
            # exchange = self._env.exchange_manager.get(exchange_name)
            # todo: get_balance()
            # asyncio.ensure_future(exchange.get_balance())

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> 115ca544ed61eecbc7442405e22bdd33be0bf931
=======
>>>>>>> 115ca544ed61eecbc7442405e22bdd33be0bf931
=======
>>>>>>> 115ca544ed61eecbc7442405e22bdd33be0bf931
=======
>>>>>>> 115ca544ed61eecbc7442405e22bdd33be0bf931
=======
>>>>>>> 115ca544ed61eecbc7442405e22bdd33be0bf931
            exchange_order_on = self._base_config['exchanges'][exchange_name].get('order_on', None)

            if biggest_bid_exchange != lower_ask_exchange and lower_ask < (biggest_bid * fee):
                bonus = (biggest_bid * fee) - lower_ask
                volume_avg = ((biggest_bid + lower_ask) / 2) * volume
                default_order_on = self.config.get('order_on', None)
                order_on = exchange_order_on if exchange_order_on else default_order_on

                # todo: get_balance()
                if volume > order_on:
                    logger.info('Volume: {} is greater then order_on limit: {}'.format(volume, order_on))
                    return

                def get_amount(order_on, volume, price):
                    if order_on:
                        if order_on / price < volume:
                            return order_on / price
                    return volume

                diff = 100 - (lower_ask / (biggest_bid / 100))
                message = "Pair is {}, diff is {:.2f}% ({:.2f} per coin), volume size is {}/{}. " \
                          "Price: bid ({}) on {}, ask ({}) on {}.".format(
                    pair, diff, bonus, round(volume), round(volume_avg),
                    biggest_bid, biggest_bid_exchange, lower_ask, lower_ask_exchange
                )
                logger.info(message)
                period = getattr(self._env.cfg.telegram, 'period', 300)
                if LAST_SEND[pair] < (time() - period) and self._env.cfg.telegram.active:
                    await self._env.bot.sendMessage(self._env.cfg.telegram.channel, message)
                    LAST_SEND[pair] = time()

                buy_fn = ask_exchange_inst.place_order(
                    pair=pair,
                    amount=get_amount(order_on, volume, lower_ask),
                    price=lower_ask,
                    operation=const.BUY
                )
                sell_fn = bid_exchange_inst.place_order(
                    pair=pair,
                    amount=get_amount(order_on, volume, biggest_bid),
                    price=biggest_bid,
                    operation=const.SELL
                )
                asyncio.ensure_future(sell_fn)
                asyncio.ensure_future(buy_fn)
        pass


export = Arbitrage
