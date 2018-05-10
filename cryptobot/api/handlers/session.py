# -*- coding: utf-8 -*-
from aiohttp import web

# from ...schema import configRequest
# from ...schema import validate


# @validate(configRequest)
async def handler_session(request: web.Request, data: dict):
    env = request.app['env']
    return web.json_response({}, status=200)
