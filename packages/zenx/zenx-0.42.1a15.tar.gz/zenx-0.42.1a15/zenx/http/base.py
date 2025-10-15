from abc import ABC, abstractmethod
import asyncio
from copy import deepcopy
from typing import Any, Callable, ClassVar, Type, Dict
from structlog import BoundLogger

from zenx.database import DBClient
from zenx.settings import Settings
from .types import Session, Response



class SessionManager(ABC):
    name: ClassVar[str]
    _registry: ClassVar[Dict[str, Type["SessionManager"]]] = {}


    def __init__(self, client: "HttpClient", logger: BoundLogger, settings: Settings) -> None:
        self.client = client
        self.logger = logger
        self.settings = settings
        self.session_pool: asyncio.Queue[Session] = asyncio.Queue(maxsize=self.settings.SESSION_POOL_SIZE)
        self._session_init_args: Dict = {"proxy": self.settings.PROXY}
        self._session_init_callable: Callable | None = None


    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "name"):
            raise TypeError(f"SessionManager subclass {cls.__name__} must have a 'name' attribute.")
        cls._registry[cls.name] = cls


    @classmethod
    def get_session_manager(cls, name: str) -> Type["SessionManager"]:
        if name not in cls._registry:
            raise ValueError(f"SessionManager '{name}' is not registered. Available session managers: {list(cls._registry.keys())}")
        return cls._registry[name]


    @property
    def session_init_args(self) -> Dict:
        kwargs = deepcopy(self._session_init_args)
        if self._session_init_callable:
            kwargs.update(self._session_init_callable())
        return kwargs


    def set_session_init_args(self, kwargs: Dict) -> None:
        self._session_init_args.update(kwargs)


    def set_session_init_callable(self, callable: Callable[..., Dict]) -> None:
        self._session_init_callable = callable


    @abstractmethod
    async def init_session_pool(self) -> None:
        ...

    @abstractmethod
    async def get_session(self) -> Session:
        ...

    @abstractmethod
    async def put_session(self, session: Session) -> None:
        ...
    
    @abstractmethod
    async def close_session(self, session: Session) -> None:
        ...

    @abstractmethod
    async def replace_session(self, session: Session, reason: str = "") -> Session:
        ...


    async def close(self) -> None:
        count = self.session_pool.qsize()
        while not self.session_pool.empty():
            session = await self.session_pool.get()
            await session.close()
        self.logger.debug("closed", sessions=count, session_manager=self.name)



class HttpClient(ABC):
    # central registry
    name: ClassVar[str]
    _registry: ClassVar[Dict[str, Type["HttpClient"]]] = {}


    @abstractmethod
    async def open(self) -> None:
        ...

    
    @abstractmethod
    def create_session(self, **kwargs) -> Session:
        ...


    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "name"):
            raise TypeError(f"HttpClient subclass {cls.__name__} must have a 'name' attribute.")
        cls._registry[cls.name] = cls


    @classmethod
    def get_client(cls, name: str) -> Type["HttpClient"]:
        if name not in cls._registry:
            raise ValueError(f"HttpClient '{name}' is not registered. Available http clients: {list(cls._registry.keys())}")
        return cls._registry[name]
    

    def __init__(self, logger: BoundLogger, db: DBClient, settings: Settings) -> None:
        self.logger = logger
        self.db = db
        self.settings = settings
        self.session_manager = SessionManager.get_session_manager(self.settings.SESSION_BACKEND)(self, logger, settings)
    

    async def _session_request(self, session: Session, **kwargs) -> Any:
        try:
            response = await asyncio.wait_for(session.request(**kwargs), timeout=kwargs.get("timeout",20)+5)
        except Exception as e:
            self.logger.error("request", exception=str(e), url=kwargs.get("url"), client=self.name, session_id=session.id)
            raise
        else:
            return response


    @abstractmethod
    async def request(self, url: str, method: str = "GET", dont_filter: bool = False, **kwargs) -> Response | None:
        """ request with session """
        ...


    @abstractmethod
    async def direct_request(self, url: str, method: str = "GET", dont_filter: bool = False, **kwargs) -> Response | None:
        """ request without session """
        ...


    async def close(self) -> None:
        await self.session_manager.close()

