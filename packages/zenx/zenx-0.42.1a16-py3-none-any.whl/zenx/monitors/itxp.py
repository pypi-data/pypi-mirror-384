import json
import time
import asyncio
from typing import Dict, Optional

from .base import Monitor


try:

    class ItxpMonitor(Monitor): # type: ignore[reportRedeclaration]
        name = "itxp"
        required_settings = ["MONITOR_ITXP_SOCKET_PATH", "MONITOR_ITXP_TRIGGER_STATUS_CODE"]


        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.trigger_status_code = self.settings.MONITOR_ITXP_TRIGGER_STATUS_CODE
            self.socket_path = self.settings.MONITOR_ITXP_SOCKET_PATH
            self.writer: Optional[asyncio.StreamWriter] = None


        async def open(self) -> None:
            for setting in self.required_settings:
                if not getattr(self.settings, setting):
                    raise ValueError(f"Missing required setting: {setting}")
            try:
                await self._connect()
            except Exception:
                self.logger.exception("open", monitor=self.name)
                raise

            self.logger.info("opened", monitor=self.name)


        async def _connect(self) -> None:
            _, self.writer = await asyncio.open_unix_connection(self.socket_path)


        async def process_stats(self, stats: Dict, spider: str) -> None:
            payload = {
                "scraper": spider,
                "type": stats.get("type"), # e.g heartbeat, error
                "msg": stats.get("msg"),
            }

            try:
                await self.send(payload)
            except Exception as e:
                self.logger.error("processing", exception=str(e), payload=payload, monitor=self.name)
                await self.close()
            else:
                self.logger.debug("processed", monitor=self.name)


        async def send(self, payload: Dict) -> None:
            if not self.writer or self.writer.is_closing():
                await self._connect()

            self.writer.write((json.dumps(payload) + '\n').encode())
            await self.writer.drain()


        async def close(self) -> None:
            if self.writer:
                self.writer.close()
                try:
                    await self.writer.wait_closed()
                except BrokenPipeError:
                    pass
                self.writer = None
            self.logger.info("closed", monitor=self.name)

except ModuleNotFoundError:
    # proxy pattern
    class ItxpMonitor(Monitor):
        name = "itxp"
        required_settings = []

        _ERROR_MESSAGE = (
            f"The '{name}' monitor is disabled because the required dependencies are not installed. "
            "Please install it to enable this feature:\n\n"
            "  pip install 'zenx[itxp]'"
        )

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            raise ImportError(self._ERROR_MESSAGE)

        async def open(self) -> None: pass
        async def process_stats(self, stats: Dict, spider: str) -> None: pass
        async def send(self, payload: Dict) -> None: pass
        async def close(self) -> None: pass
