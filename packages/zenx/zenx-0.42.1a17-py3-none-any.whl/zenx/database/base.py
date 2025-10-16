from abc import ABC, abstractmethod
from typing import ClassVar, Dict, List, Type
from structlog import BoundLogger

from zenx.settings import Settings



class DBClient(ABC):
    name: ClassVar[str]
    required_settings: ClassVar[List[str]]
    _registry: ClassVar[Dict[str, Type["DBClient"]]] = {}
    

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "name"):
            raise TypeError(f"DBClient subclass {cls.__name__} must have a 'name' attribute.")
        cls._registry[cls.name] = cls

    
    @classmethod
    def get_db(cls, name: str) -> Type["DBClient"]:
        if name not in cls._registry:
            raise ValueError(f"DBClient '{name}' is not registered. Available db clients: {list(cls._registry.keys())}")
        return cls._registry[name]

    
    def __init__(self, logger: BoundLogger, settings: Settings) -> None:
        self.logger = logger
        self.settings = settings

        
    @abstractmethod
    async def open(self) -> None:
        ...

    
    @abstractmethod
    async def _connect(self) -> None:
        ...


    @abstractmethod
    async def insert(self, id: str, spider: str, **kwargs) -> bool:
        ...


    @abstractmethod
    async def exists(self, id: str, spider: str) -> bool:
        ...


    @abstractmethod
    async def close(self) -> None:
        ...
