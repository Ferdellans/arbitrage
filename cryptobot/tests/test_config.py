from aiohttp.test_utils import AioHTTPTestCase

from attrdict import AttrDict
from hypothesis import given
from server.api.route import make_app
from server.schema import configResponse

from .strategies import ST_CLIENT_ID
from .strategies import ST_CLIENT_VERSION
from .strategies import ST_CONFIG_VERSION
from .strategies import ST_FAKE_CLEINT_ID
from .strategies import ST_RANDOM_JSON
from .strategies import ST_SCOPE
from .strategies import ST_TIMESTAMP
from .strategies import ST_TIMEZONE
from .strategies import ST_WHITELIST_VERSION


class ConfigTestCase(AioHTTPTestCase):

    async def get_application(self):

        class FakeCur():
            MAP = {
                'dev_api.set_val_status': (1, 1)
            }
            RESULT = None
            async def __aenter__(self, *args, **kw):
                return self

            async def __aexit__(self, *args, **kw):
                return self

            async def callproc(self, name, *args):
                self.RESULT = self.MAP[name]
                pass

            async def fetchone(self):
                return self.RESULT

        class FakeConn():
            async def __aenter__(self, *args, **kw):
                return self

            async def __aexit__(self, *args, **kw):
                return self

            def cursor(self):
                return FakeCur()

        class FakePool():
            def acquire(self):
                return FakeConn()

        env = AttrDict(pool=FakePool())
        return make_app(env)


class TestConfig(ConfigTestCase):
    @given(
        client_id=ST_CLIENT_ID,
        client_version=ST_CLIENT_VERSION,
        scope=ST_SCOPE,
        whitelist_version=ST_WHITELIST_VERSION,
        config_version=ST_CONFIG_VERSION,
        timestamp=ST_TIMESTAMP,
        timezone=ST_TIMEZONE,
    )
    def test_valid(self, **data):
        async def go():
            request = await self.client.post("/", json=data)
            assert request.status == 200
            result = await request.json()
            configResponse(**result).validate()
        self.loop.run_until_complete(go())

    @given(
        xconfig_version=ST_CONFIG_VERSION,
    )
    def test_need_config_version(self, **data):
        async def go():
            request = await self.client.post("/", json=data)
            assert request.status == 400
            result = await request.json()
            assert 'error' in result
            assert 'config_version' in result['error']
        self.loop.run_until_complete(go())

    @given(
        client_id=ST_FAKE_CLEINT_ID,
    )
    def test_to_big_but_fail(self, **data):
        async def go():
            request = await self.client.post("/", json=data)
            assert request.status == 400
            result = await request.json()
            assert 'error' in result
            assert 'client_id' in result['error']
        self.loop.run_until_complete(go())

    @given(ST_RANDOM_JSON)
    def test_should_not_die(self, data):
        async def go():
            request = await self.client.post("/", json=data)
            assert request.status in [400, 200]
        self.loop.run_until_complete(go())
