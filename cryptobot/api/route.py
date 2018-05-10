# -*- coding: utf-8 -*-

import logging

from aiohttp import web

from attrdict import AttrDict

from .handlers import handler_session


logger = logging.getLogger(__name__)


def make_app(env: AttrDict) -> web.Application:
    app = web.Application()
    app['env'] = env
    app.router.add_route('GET', '/session', handler_session)
    return app


async def configure(env: AttrDict):
    handler = make_app(env).make_handler()
    srv = await env.loop.create_server(handler, env.cfg['http']['ip'], env.cfg['http']['port'])
    # return srv, handler
    return env
