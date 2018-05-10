import telepot.aio
from attrdict import AttrDict


async def configure(env: AttrDict):
    token = env.cfg.telegram.token
    env.bot = telepot.aio.Bot(token)
    return env
