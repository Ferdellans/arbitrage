import importlib


class BaseManager:
    @property
    def import_mask(self):
        raise NotImplemented

    CACHE = import_mask

    def __init__(self, env: dict):
        self._env = env

    def get(self, name: str):
        assert name, name

        if name not in self.CACHE:
            try:
                module = importlib.import_module(self.import_mask.format(name.lower()))
                self.CACHE[name] = module.export
            except ModuleNotFoundError:
                self.CACHE[name] = None
        return self.CACHE[name]
