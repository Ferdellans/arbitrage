from cryptobot.common.manager import BaseManager


class BaseCurrency:
    @property
    def title(self):
        raise NotImplemented

    symbol = title


class CurrencyManager(BaseManager):
    CACHE = {}
    import_mask = "cryptobot.currency.{}"
