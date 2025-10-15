from typing import Dict
import json
from httpx import AsyncClient
from structlog import BoundLogger

from zenx.database import DBClient
from zenx.settings import Settings
from zenx.utils import log_processing_time
from .base import Pipeline



class SynopticDiscordPipeline(Pipeline): # type: ignore[reportRedeclaration]
    name = "synoptic_discord"
    required_settings = ["SYNOPTIC_DISCORD_WEBHOOK"]
    
    
    def __init__(self, logger: BoundLogger, db: DBClient, settings: Settings) -> None:
        super().__init__(logger, db, settings)
        self._uri = settings.SYNOPTIC_DISCORD_WEBHOOK
        self._client = AsyncClient(headers={"Content-Type": "application/json"})


    async def open(self) -> None:
        for setting in self.required_settings:
            if not getattr(self.settings, setting):
                raise ValueError(f"Missing required setting: {setting}")
                
        self.logger.info("opened", pipeline=self.name)
    
    
    @log_processing_time
    async def process_item(self, item: Dict, spider: str) -> Dict:
        _item = {k: v for k, v in item.items() if not k.startswith("_")}
        _item['spider'] = spider
        if _item.get("headline"):
            _item["headline"] = _item["headline"][:200]
        message_content = f"```json\n{json.dumps(_item, indent=4)}\n```"
        payload = {"content": message_content}
        await self.send(payload)
        return item
    

    async def send(self, payload: Dict) -> None:
        try:
            response = await self._client.post(self._uri, json=payload)
            if response.status_code not in [200, 204]:
                raise Exception(f"unexpected response: {response.status_code}")
        except Exception as e:
            self.logger.error("processing", exception=str(e), payload=payload, pipeline=self.name)


    async def close(self) -> None:
        if hasattr(self, "_client") and self._client:
            await self._client.aclose()
        self.logger.info("closed", pipeline=self.name)
