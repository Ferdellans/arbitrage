# -*- coding: utf-8 -*-
import asyncio
import logging

import click
from attrdict import AttrDict
from .. import bot
from .. import db
from ..api import route


logger = logging.getLogger(__name__)


@click.group()
def api_group():
    pass


async def configure(env: AttrDict):
    env = await bot.configure(env)
    env = await db.configure(env)
    env = await route.configure(env)


@api_group.command()
@click.pass_context
def api(ctx, test):
    """Run api """
    env = AttrDict()
    env.cfg = ctx.obj['cfg']
    loop = env.loop = asyncio.get_event_loop()
    env.loop.create_task(configure(env))
    loop.run_forever()
