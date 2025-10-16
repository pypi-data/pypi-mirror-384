from datetime import datetime
import json
import os
from typing import Dict
from httpx import AsyncClient
from structlog import BoundLogger
import aiofiles

from zenx.utils import get_time, log_processing_time
from .base import Pipeline
from zenx.database import DBClient
from zenx.settings import Settings



class SynopticS3Pipeline(Pipeline):
    name = "synoptic_s3"
    required_settings = ["SYNOPTIC_S3_STREAM_ID", "SYNOPTIC_S3_API_KEY"]
    stream_id = "SYNOPTIC_S3_STREAM_ID"
    api_key = "SYNOPTIC_S3_API_KEY"
    

    def __init__(self, logger: BoundLogger, db: DBClient, settings: Settings) -> None:
        super().__init__(logger, db, settings)
        self._stream_id = getattr(settings, self.stream_id)
        self._api_key = getattr(settings, self.api_key)
        self._client = AsyncClient()
        self._cache = {} # mime_type: {"created_at": get_time(), "upload_url": upload_url}
        self._cache_ttl = 50 * 60 * 1000 # 50 minutes


    async def open(self) -> None:
        for setting in self.required_settings:
            if not getattr(self.settings, setting):
                raise ValueError(f"Missing required setting for pipeline '{self.name}': {setting}")
        self.logger.info("opened", pipeline=self.name)
        
    
    async def _fetch_presigned_media_urls(self, item: Dict) -> Dict:
        if item['_id'] in self._cache:
            created_at = self._cache[item['_id']]['created_at']
            if (get_time() - created_at) < self._cache_ttl:
                return self._cache[item['_id']]['presigned_urls']

        url = f"https://api.dev.synoptic.com/v1/streams/{self._stream_id}/post"
        headers={
            'x-api-key': self._api_key,
            'Accept': '*/*',
        }
        mime_types = [m['type'] for m in item['media']]
        json_data = {
            'idempotencyKey': item['_id'],
            'content': item['headline'] or "n/a",
            'uploadMedia': [{'mimeType': "image/jpeg"} for mime_type in mime_types],
            "metadata": {
                "type": "Post",
                "sourceLink": item['link'],
                "sourceName": item['source'],
                "headline": item['headline'],
                "media": item['media'],
                "icon": {
                    "url": item['icon']
                },
                "sourceTimestamp": item['published_at']
            }
        }
        try:
            response = await self._client.post(
                url=url,
                headers=headers,
                json=json_data,
            )
            if response.status_code != 201:
                raise Exception(f"unexpected response: {response.status_code}")
        except Exception as e:
            self.logger.error("fetch_presigned_media_url", exception=str(e), json_data=json_data, mime_types=mime_types, pipeline=self.name)
        else:
            upload_urls = response.json()['mediaUploadURLs']
            if not upload_urls:
                self.logger.error("unsupported_mime_type", mime_types=mime_types, pipeline=self.name)
                return

            presigned_urls = {}
            for upload in upload_urls:
                mime_type = upload['type']
                if mime_type not in presigned_urls:
                    presigned_urls[mime_type] = []
                presigned_urls[mime_type].append(upload['url'])

            self._cache[item['_id']] = {"created_at": get_time(), "presigned_urls": presigned_urls}
            return presigned_urls

    
    @log_processing_time
    async def process_item(self, item: Dict, spider: str) -> Dict:
        if "headline" in item: # first time media presigned urls need to be fetched
            if not item.get("media"):
                return item
            presigned_urls = await self._fetch_presigned_media_urls(item)
            if presigned_urls:
                item['_presigned_urls'] = presigned_urls
                self.logger.info("presigned_urls_fetched", presigned_urls=presigned_urls, pipeline=self.name)
            if "_presigned_urls_ready" in item:
                item["_presigned_urls_ready"].set()
            return item

        # upload media to s3
        payload = {"url": item['presigned_url'], "headers": {"content-type": item['mime_type']}, "file_path": item['file_path']}
        await self.send(payload)
        if item['fd'] != -1:
            os.close(item['fd'])
            os.remove(item['file_path'])
        return item


    async def send(self, payload: Dict) -> None:
        url = payload['url']
        headers = payload['headers']
        file_path = payload['file_path']
        try:
            async with aiofiles.open(file_path, mode="rb") as f:
                content = await f.read()
            response = await self._client.put(url, headers=headers, content=content)
            response.raise_for_status()
        except Exception as e:
            self.logger.error("processing", exception=str(e), url=url[:100], headers=headers, file_path=file_path, pipeline=self.name)

    
    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
        self.logger.info("closed", pipeline=self.name)

