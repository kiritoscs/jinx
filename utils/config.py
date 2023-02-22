import yaml


class Config(object):
    """配置文件加载"""
    def __init__(self, config_path: str):
        self._fp = config_path
        self.config = None
        self._load()

    def _load(self):
        with open(self._fp, "r") as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)

    def get(self, module: str = None, key: str = None, default=None):
        if not module:
            if not key:
                return self.config or {}
            return self.config.get(key, default)
        if not key:
            return self.config.get(module, {})
        return self.config.get(module, {}).get(key, default)
