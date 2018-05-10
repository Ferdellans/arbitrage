# -*- coding: utf-8 -*-
import asyncio
import logging

import click
from attrdict import AttrDict
from .. import db
from .. import bot
from .. import currency
from .. import exchange
from .. import strategy


logger = logging.getLogger(__name__)


@click.group()
def execute_group():
    pass


async def configure(env: AttrDict):
    env = await db.configure(env)
    env = await bot.configure(env)
    logger.info("Run strategy {}".format(env.strategy.title))
    env.loop.create_task(env.strategy.run())


def check_strategy(ctx: click.core.Context, param: str, value: str):
    cfg = ctx.obj['cfg']
    valid_names = cfg['strategies'].keys()
    if value not in valid_names:
        raise click.exceptions.BadOptionUsage(
            "Unknown strategy name (allow only {})".format(','.join(valid_names)), ctx
        )
    strategy_cfg = cfg['strategies'][value]

    if not strategy.StrategyManager(None).get(strategy_cfg['type']):
        raise click.exceptions.BadOptionUsage(
            "Strategy {} not found (allow only {})".format(value, ','.join(valid_names)), ctx
        )
    return value


@execute_group.command()
@click.option('--test', is_flag=True, default=False)
@click.argument('strategy_name', callback=check_strategy)
@click.pass_context
def execute(ctx, test, strategy_name):
    """Execute strategy"""
    env = AttrDict()
    env.cfg = ctx.obj['cfg']
    env.currency_manager = currency.CurrencyManager(env)
    env.exchange_manager = exchange.ExchangeManager(env)
    env.strategy_manager = strategy.StrategyManager(env)
    strategy_cfg = env.cfg['strategies'][strategy_name]
    strategy_cls = env.strategy_manager.get(strategy_cfg['type'])
    env.strategy = strategy_cls(name=strategy_name, env=env, config=env.cfg['strategies'][strategy_name])

    loop = env.loop = asyncio.get_event_loop()
    env.loop.create_task(configure(env))
    loop.run_forever()
