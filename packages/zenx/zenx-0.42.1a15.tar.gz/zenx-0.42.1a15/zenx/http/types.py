from typing import Protocol
from dataclasses import dataclass, field
from typing import Dict, Any
from functools import cached_property
import orjson
from parsel import Selector, SelectorList
from urllib.parse import urljoin

from zenx.utils import get_time



@dataclass
class Response:
    url: str
    status: int
    text: str
    headers: Dict
    cookies: Dict
    responded_at: int
    requested_at: int
    latency_ms: int
    body: bytes | None = None
    raw_response: Any = field(default=None, repr=False)


    def json(self) -> Any:
        return orjson.loads(self.text)
    
    @cached_property
    def selector(self) -> Selector:
        content_type = self.headers.get('content-type', '').lower()
        if "xml" in content_type or self.text.strip().startswith("<?xml"):
            return Selector(self.text, type='xml')
        return Selector(self.text)
    
    def xpath(self, query: str, **kwargs) -> SelectorList[Selector]:
        return self.selector.xpath(query, **kwargs)

    def urljoin(self, *args: str) -> str:
        return urljoin(self.url, *args)


class Transport(Protocol):
    """ 
    3rd party libraries with request and close methods satisfy this interface e.g AsyncSession from curl_cffi 
    """
    async def request(self, *args, **kwargs) -> Any:
        ...
    
    async def close(self) -> None:
        ...


class Session:
    def __init__(self, id: str, age: int, transport: Transport, blp_created_at: str | None = None) -> None:
        self.id = id
        self.requests = 0
        self.created_at = get_time()
        self.expired_at = self.created_at + (age * 1000)
        self.transport = transport
        self.blp_created_at = blp_created_at
        self.near_retirement = False

    def is_over_age(self) -> bool:
        return get_time() > self.expired_at

    def is_near_retirement(self) -> bool:
        # near retirement if less than 60sec remaining to reach expired_at
        return (self.expired_at - get_time()) < (60 * 1000)

    async def request(self, *args, **kwargs) -> Any:
        return await self.transport.request(*args, **kwargs)
    
    async def close(self) -> None:
        await self.transport.close()

    
