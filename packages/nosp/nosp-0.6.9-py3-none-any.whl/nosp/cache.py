import sys
from typing import Optional, Callable, Any, Dict, TypeVar, Generic

from loguru import logger

from nosp.config import RedisConfig
from nosp.database import Redis
from nosp.utils import get_md5


class CacheBaseModel:
    def __init__(self):
        self._on_change: Optional[Callable[[str, str], None]] = None
        self._on_get: Optional[Callable[[str], str]] = None
        self._live = False

    def __init_subclass__(cls):
        cls._on_change: Optional[Callable[[str, str], None]] = None
        cls._on_get: Optional[Callable[[str], str]] = None
        cls._live = False

    def on_change(self, callback: Callable[[str, str], None]) -> None:
        """注册变更回调"""
        self._on_change = callback

    def on_get(self, callback: Callable[[str], str]) -> None:
        """注册Get回调"""
        self._on_get = callback

    def __setattr__(self, key: str, value: Any):
        super().__setattr__(key, value)
        if not key.startswith("_") and hasattr(self, '_on_change') and self._on_change is not None:
            self._on_change(key, str(value))

    def __getattribute__(self, key: str) -> Any:
        if key.startswith("_"):
            return super().__getattribute__(key)

        if hasattr(self, '_live') and self._live and hasattr(self, '_on_change') and self._on_get is not None:
            try:
                return self._on_get(key)
            except Exception as e:
                logger.warning(f"on_get({key}) failed: {e}")

        return super().__getattribute__(key)

    def set(self, data: Dict[str, Any]):
        annotations = self.__class__.__annotations__
        for k, v in data.items():
            if k in annotations:
                setattr(self, k, v)

    def get(self) -> Dict[str, str]:
        return {
            k: str(getattr(self, k))
            for k in self._class__.__annotations__
            if hasattr(self, k)
        }


T = TypeVar('T', bound=CacheBaseModel)


class Cache(Generic[T]):
    def __init__(self, cfg: RedisConfig, db=15, data_type=None, live=False,key=None):
        self.key = key if key else get_md5(sys.modules.get("__main__").__file__)
        self.redis = Redis.simple(cfg, db=db)
        self.data: Optional[T] = None
        if data_type is not None:
            self.data: Optional[T] = data_type()
            self._load()
            self.data._live = live


    def _save_to_redis(self, key, value):
        """私有方法：保存数据到 Redis"""
        try:
            self.redis.r.hset(self.key, key, value)
        except Exception as e:
            logger.warning(f"Save failed: {e}")

    def _on_get(self, key: str) -> str:
        print(key)
        return self.redis.r.hget(self.key, key)

    def _load(self):
        if self.data is None:
            return None
        data = self.redis.r.hgetall(self.key)
        if data and isinstance(data, dict):
            try:
                self.data.set(data)
            except Exception as e:
                logger.warning(f"Load failed: {e}")
        self.data.on_change(self._save_to_redis)
        self.data.on_get(self._on_get)
        return None

    def get(self, key: str) -> str:
        return self.redis.r.hget(self.key, key)

    def set(self, key: str, value):
        return self.redis.r.hset(self.key, key, value)