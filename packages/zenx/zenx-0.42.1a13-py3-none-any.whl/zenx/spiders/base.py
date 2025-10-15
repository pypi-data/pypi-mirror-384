import asyncio
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Coroutine, Dict, List, Literal, Optional, Type
from structlog import BoundLogger
import html_text

from zenx.http import HttpClient, Response
from zenx.monitors import Monitor
from zenx.pipelines import PipelineManager
from zenx.settings import Settings



class Spider(ABC):
    # central registry
    name: ClassVar[str]
    _registry: ClassVar[Dict[str, Type["Spider"]]] = {}
    pipelines: ClassVar[List[str]] = []
    monitor_name: ClassVar[Literal["itxp"]] = "itxp"
    client_name: ClassVar[Literal["curl_cffi"]] = "curl_cffi"
    custom_settings: ClassVar[Dict[str, Any]] = {}


    def __init_subclass__(cls, **kwargs) -> None:
        # for multiple inheritence to work
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "name"):
            raise TypeError(f"Spider subclass {cls.__name__} must have a 'name' attribute.")

        # ensure preprocess is always the first pipeline
        if hasattr(cls, "pipelines") and cls.pipelines:
            pipelines = cls.pipelines.copy()
            if "preprocess" in pipelines:
                pipelines.remove("preprocess")
            pipelines.insert(0, "preprocess")
            cls.pipelines = pipelines
        else:
            cls.pipelines = ["preprocess"]

        # add spider to registry
        cls._registry[cls.name] = cls


    @classmethod
    def get_spider(cls, name: str) -> Type["Spider"]:
        if name not in cls._registry:
            raise ValueError(f"Spider '{name}' is not registered. Available spiders: {list(cls._registry.keys())}")
        return cls._registry[name]


    @classmethod
    def spider_list(cls) -> List[str]:
        return list(cls._registry.keys())


    def __init__(self, client: HttpClient, pm: PipelineManager, logger: BoundLogger, settings: Settings, monitor: Monitor | None = None, **kwargs) -> None:
        self.client = client
        self.pm = pm
        self.logger = logger
        self.settings = settings
        self.monitor = monitor
        self.background_tasks = set()

    
    def create_task(self, coro: Coroutine, name: Optional[str] = None) -> None:
        t = asyncio.create_task(coro, name=name)
        self.background_tasks.add(t)
        t.add_done_callback(self.background_tasks.discard)


    def extract_text(self, html: str, **kwargs) -> str:
        return html_text.extract_text(html, **kwargs)
    

    async def request(self,
        url: str,
        method: str = "GET",
        dont_filter: bool = False,
        bypass_session_manager: bool = False,
        **kwargs,
    ) -> Response:
        """ helper method for spiders """
        if bypass_session_manager:
            response = await self.client.direct_request(
                url=url,
                method=method,
                dont_filter=dont_filter,
                **kwargs,
            )
        else:   
            response = await self.client.request(
                url=url,
                method=method,
                dont_filter=dont_filter,
                **kwargs,
            )
        if response and self.monitor and response.status == self.monitor.trigger_status_code:
            self.create_task(self.monitor.process_stats({"type": "heartbeat"}, self.name))
        return response


    async def process_item(self, item: Dict, spider: str, via: List[str] = []) -> None:
        """ helper method for spiders """
        await self.pm.process_item(item, spider, via)


    async def open(self) -> None:
        pass


    @abstractmethod
    async def crawl(self, task_id: str | None = None) -> None:
        """ Short-lived scrape """
        ...


    async def process_response(self, response: Response) -> None:
        pass


    async def close(self) -> None:
        pass
