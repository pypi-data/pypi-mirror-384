import collections
import pathlib
import sqlite3
from typing import Optional
from structlog import BoundLogger

from .base import DBClient
from zenx.settings import Settings



class MemoryDB(DBClient):
    name = "memory"
    required_settings = []


    def __init__(self, logger: BoundLogger, settings: Settings) -> None:
        super().__init__(logger, settings)
        self.dq = collections.deque(maxlen=self.settings.DQ_MAX_SIZE)


    async def open(self) -> None:
        pass


    async def _connect(self) -> None:
        pass


    async def insert(self, id: str, spider: str, **kwargs) -> bool:
        unique_id = f"{spider}_{id}"
        if unique_id in self.dq:
            self.logger.debug("exists", id=unique_id, db=self.name)
            return False
        self.dq.append(unique_id)
        self.logger.debug("inserted", id=unique_id, db=self.name)
        return True


    async def exists(self, id: str, spider: str) -> bool:
        unique_id = f"{spider}_{id}"
        return unique_id in self.dq
    

    async def close(self) -> None:
        pass


class SqliteDB(DBClient):
    name = "sqlite"
    required_settings = ["DB_PATH"]
    
    
    async def open(self) -> None:
        for setting in self.required_settings:
            if not getattr(self.settings, setting):
                raise ValueError(f"Missing required setting: {setting}")
        try:
            pathlib.Path(self.settings.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
            await self._connect()
        except Exception:
            self.logger.exception("db_open_failed", db=self.name)
            raise


    async def _connect(self) -> None:
        self.conn = sqlite3.connect(self.settings.DB_PATH)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS items (id TEXT PRIMARY KEY, spider TEXT)")
        self.logger.info("connected", db=self.name)


    async def insert(self, id: str, spider: str, **kwargs) -> bool:
        unique_id = f"{spider}_{id}"
        self.cursor.execute("INSERT OR IGNORE INTO items (id, spider) VALUES (?, ?)", (unique_id, spider))
        self.conn.commit()
        if self.cursor.rowcount == 0:
            return False
        self.logger.debug("inserted", id=unique_id, db=self.name)
        return True


    async def exists(self, id: str, spider: str) -> bool:
        unique_id = f"{spider}_{id}"
        self.cursor.execute("SELECT COUNT(*) FROM items WHERE id = ?", (unique_id,))
        return self.cursor.fetchone()[0] > 0


    async def close(self) -> None:
        if self.conn:
            self.conn.close()
        


try:
    import redis.asyncio as redis

    class RedisDB(DBClient): # type: ignore [reportRedeclaration]
        name = "redis"
        required_settings = ["DB_HOST", "DB_PORT"]
        
        
        def __init__(self, logger: BoundLogger, settings: Settings) -> None:
            super().__init__(logger, settings)
            self.r: Optional[redis.Redis] = None
            self._record_expiry_sec = self.settings.REDIS_RECORD_EXPIRY_SECONDS

    
        async def open(self) -> None:
            for setting in self.required_settings:
                if not getattr(self.settings, setting):
                    raise ValueError(f"Missing required setting: {setting}")
            try:
                await self._connect()
            except Exception:
                self.logger.exception("db_open_failed", db=self.name)
                raise


        async def _connect(self) -> None:
            self.logger.debug("connecting", db=self.name)
            pool = redis.ConnectionPool(
                host=self.settings.DB_HOST,
                port=self.settings.DB_PORT,
                password=self.settings.DB_PASS,
                socket_timeout=5,
                socket_connect_timeout=5,
                decode_responses=True,
            )
            self.r = redis.Redis(connection_pool=pool)
            await self.r.ping()
            self.logger.info("connected", db=self.name)


        async def insert(self, id: str, spider: str, **kwargs) -> bool:
            expiry_sec = kwargs.get("expiry_sec", self._record_expiry_sec)
            unique_id = f"{spider}_{id}"
            result = await self.r.set(unique_id, 1, ex=expiry_sec, nx=True)
            if result:
                self.logger.debug("inserted", id=unique_id, db=self.name)
                return True
            else:
                self.logger.debug("exists", id=unique_id, db=self.name)
                return False


        async def exists(self, id: str, spider: str) -> bool:
            unique_id = f"{spider}_{id}"
            return bool(await self.r.exists(unique_id))
        

        async def close(self) -> None:
            if self.r:
                await self.r.aclose()

except ModuleNotFoundError:
    # proxy pattern
    class RedisDB(DBClient):
        name = "redis"
        required_settings = []
        
        _ERROR_MESSAGE = (
            f"The '{name}' component is disabled because the required dependencies are not installed. "
            "Please install it to enable this feature:\n\n"
            "  pip install 'zenx[redis]'"
        )

        def __init__(self, *args, **kwargs):
            raise ImportError(self._ERROR_MESSAGE)
        
        async def open(self) -> None: pass
        async def _connect(self) -> None: pass
        async def insert(self, id: str, spider: str, **kwargs) -> bool: return False
        async def exists(self, id: str, spider: str) -> bool: return False
        async def close(self) -> None: pass
