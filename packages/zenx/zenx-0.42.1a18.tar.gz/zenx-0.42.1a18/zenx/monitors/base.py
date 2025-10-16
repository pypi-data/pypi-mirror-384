from abc import ABC, abstractmethod
from typing import ClassVar, Dict, List, Type
from structlog import BoundLogger

from zenx.settings import Settings



class Monitor(ABC):
    name: ClassVar[str]
    required_settings: ClassVar[List[str]]
    _registry: ClassVar[Dict[str, Type["Monitor"]]] = {}



    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "name"):
            raise TypeError(f"Monitor subclass {cls.__name__} must have a 'name' attribute.")
        cls._registry[cls.name] = cls


    @classmethod
    def get_monitor(cls, name: str) -> Type["Monitor"]:
        if name not in cls._registry:
            raise ValueError(f"Monitor '{name}' is not registered. Available monitors: {list(cls._registry.keys())}")
        return cls._registry[name]


    def __init__(self, logger: BoundLogger, settings: Settings) -> None:
        self.logger = logger
        self.settings = settings
        self.trigger_status_code: int | None = None


    @abstractmethod
    async def open(self) -> None:
        ...


    @abstractmethod
    async def process_stats(self, stats: Dict, spider: str) -> None:
        ...


    @abstractmethod
    async def send(self, payload: Dict) -> None:
        ...


    @abstractmethod
    async def close(self) -> None:
        ...
