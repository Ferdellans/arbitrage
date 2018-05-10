import aiopg
import aiopg.sa
import sqlalchemy as sa

from attrdict import AttrDict

metadata = sa.MetaData()


table_trade_history = sa.Table(
    'trade_history',
    metadata,
    sa.Column('time', sa.Integer, primary_key=True),
    sa.Column('exchange', sa.String(255)),
    sa.Column('pair', sa.String(255)),
    sa.Column('bid', sa.Float),
    sa.Column('ask', sa.Float),
    sa.Column('bid_size', sa.Float),
    sa.Column('ask_size', sa.Float),
)

async def configure(env: AttrDict):
    dsn = env.cfg.dsn
    env.db = await aiopg.sa.create_engine(dsn)
    return env
