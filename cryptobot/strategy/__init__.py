import asyncio
import logging

from cryptobot.common.manager import BaseManager

logger = logging.getLogger(__name__)


class BaseStrategy:

    def __init__(self, name, env, config):
        self.config = config
        self._env = env
        self._base_config = env.cfg

    async def run(self):
        asyncio.ensure_future(self.update_ticker_schedule())
        asyncio.ensure_future(self.make_order_schedule())
        asyncio.ensure_future(self.expire_order_schedule())
        asyncio.ensure_future(self.transfer_schedule())
        if hasattr(self, '_run'):
            await self._run()

    @property
    def title(self):
        raise NotImplemented

    def make_schedule(name, interval=5):
        async def schedule(self):
            if not hasattr(self, name):
                logger.info("Skip {}.{}_schedule".format(self.title, name))
                return
            while self._env.loop.is_running():
                try:
                    await getattr(self, name)()
                except:
                    logger.exception("Error on {}".format(name))
                await asyncio.sleep(interval)
        return schedule

    update_ticker_schedule = make_schedule('update_ticker')
    make_order_schedule = make_schedule('make_order')
    transfer_schedule = make_schedule('transfer')
    expire_order_schedule = make_schedule('expire_order')


class StrategyManager(BaseManager):
    CACHE = {}
    import_mask = "cryptobot.strategy.{}"
