import asyncio
import json
from typing import Dict

from zenx.utils import log_processing_time
from .base import Pipeline



class ItxpPipeline(Pipeline):
    name = "itxp"
    required_settings = ["ITXP_SOCKET_PATH"]


    async def open(self) -> None:
        for setting in self.required_settings:
            if not getattr(self.settings, setting):
                raise ValueError(f"Missing required setting: {setting}")
        try:
            await self._connect()
        except Exception:
            self.logger.exception("open", pipeline=self.name)
            raise
        self.logger.info("opened", pipeline=self.name)


    async def _connect(self) -> None:
        _, self.writer = await asyncio.open_unix_connection(self.settings.ITXP_SOCKET_PATH)


    @log_processing_time
    async def process_item(self, item: Dict, spider: str) -> Dict:
        payload = {
            "scraper": spider,
            "type": "post",
            "post": {
                "url": item.get("link"),
                "headline": item.get("headline"),
                "scraped_at": item.get("scraped_at"),
                "published_at": item.get("published_at"),
            },
        }
        await self.send(payload)
        return item


    async def send(self, payload: Dict) -> None:
        try:
            if not self.writer or self.writer.is_closing():
                await self._connect()

            self.writer.write((json.dumps(payload) + '\n').encode())
            await self.writer.drain()
        except Exception as e:
            self.logger.error("processing", exception=str(e), payload=payload, pipeline=self.name)


    async def close(self) -> None:
        if self.writer:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except BrokenPipeError:
                pass
            self.writer = None
        self.logger.info("closed", pipeline=self.name)