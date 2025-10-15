import asyncio
import json
import redis.asyncio as redis

from zenx.exceptions import NoSessionAvailable
from .base import SessionManager
from .types import Session
from zenx.utils import get_time



class MemorySessionManager(SessionManager):
    name = "memory"


    async def init_session_pool(self) -> None:
        while self.session_pool.qsize() < self.settings.SESSION_POOL_SIZE:
            session = self.client.create_session(**self.session_init_args)
            await self.put_session(session)
        self.logger.info("initialized", session_pool_size=self.session_pool.qsize(), session_manager=self.name)


    async def get_session(self) -> Session:
        try:
            session = await asyncio.wait_for(self.session_pool.get(), timeout=10.0)
            return session
        except asyncio.TimeoutError:
            self.logger.info("timeout", session_pool_size=self.session_pool.qsize(), session_manager=self.name)
            raise NoSessionAvailable()


    async def put_session(self, session: Session) -> None:
        self.session_pool.put_nowait(session)


    async def close_session(self, session: Session) -> None:
        await session.close()


    async def replace_session(self, session: Session, reason: str = "") -> Session:
        await self.close_session(session)
        new_session = self.client.create_session(**self.session_init_args)
        self.logger.debug("replaced_session", old=session.id, new=new_session.id, reason=reason, age=(get_time() - session.created_at)/1000, requests=session.requests)
        return new_session



class RedisSessionManager(SessionManager):
    name = "redis"


    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.r = redis.Redis(host=self.settings.DB_HOST, port=self.settings.DB_PORT, password=self.settings.DB_PASS, decode_responses=True, socket_timeout=30)
    
    
    async def _create_blueprint(self) -> None:
        # trigger blueprint creation
        msg = json.dumps({"type": "message", "data": "blueprint_create"})
        await self.r.lpush(self.settings.REDIS_MESSAGE_QUEUE, msg)
        self.logger.debug("sent", msg=msg, queue=self.settings.REDIS_MESSAGE_QUEUE, session_manager=self.name)
        

    async def _fetcher(self) -> None:
        while True:
            result = await self.r.brpop(self.settings.REDIS_RESULT_QUEUE, timeout=60)
            if not result:
                self.logger.info("waiting", session_pool_size=self.session_pool.qsize(), queue=self.settings.REDIS_RESULT_QUEUE, session_manager=self.name)
                continue
            
            _, config_json = result
            config_dict = json.loads(config_json)
            # merge init_args with config_dict
            for k, v in self.session_init_args.items():
                if k == "proxy": # proxy is already set in the blueprint, it should not be overridden in any case
                    continue
                if k in config_dict:
                    config_dict[k].update(v)
                    continue
                config_dict[k] = v
            session = self.client.create_session(**config_dict)
            await self.put_session(session)
            self.logger.debug("updated", session_pool_size=self.session_pool.qsize(), queue=self.settings.REDIS_RESULT_QUEUE, session_manager=self.name)


    async def init_session_pool(self) -> None:
        count = self.settings.SESSION_POOL_SIZE - await self.r.llen(self.settings.REDIS_RESULT_QUEUE) 
        if count > 0:
            async with asyncio.TaskGroup() as tg:
                for _ in range(count):
                    tg.create_task(self._create_blueprint())
            self.logger.info("requested", blueprints=count, session_manager=self.name)
        
        asyncio.create_task(self._fetcher())
        while self.session_pool.qsize() < self.settings.SESSION_POOL_SIZE:
            await asyncio.sleep(1)

        self.logger.info("initialized", session_pool_size=self.session_pool.qsize(), session_manager=self.name)


    async def get_session(self) -> Session:
        try:
            session = await asyncio.wait_for(self.session_pool.get(), timeout=10.0)
            # check for near retirement
            if not session.near_retirement and session.is_near_retirement():
                session.near_retirement = True
                self.logger.debug("near_retirement", session=session.id, session_manager=self.name)
                await self._create_blueprint()
            return session
        except asyncio.TimeoutError:
            self.logger.info("timeout", session_pool_size=self.session_pool.qsize(), session_manager=self.name)
            raise NoSessionAvailable()


    async def put_session(self, session: Session) -> None:
        await self.session_pool.put(session)


    async def close_session(self, session: Session) -> None:
        await session.close()


    async def replace_session(self, session: Session, reason: str = "") -> Session:
        if reason == "expired" and not session.near_retirement: # for session expired prematurely
            await self._create_blueprint()
        await self.close_session(session)
        
        new_session = await self.get_session()
        self.logger.info("replaced_session", old=session.id, new=new_session.id, reason=reason, age=(get_time() - session.created_at)/1000, requests=session.requests)
        return new_session
