from __future__ import annotations
import asyncio
from curl_cffi import AsyncSession, Response as CurlResponse

from zenx.utils import get_time, get_uuid
from .base import HttpClient
from .types import Session, Response



class CurlCffiClient(HttpClient):
    name = "curl_cffi"


    async def open(self) -> None:
        await self.session_manager.init_session_pool()


    def create_session(self, **kwargs) -> Session:
        session_id = get_uuid()
        proxy = kwargs.get("proxy")
        if proxy and "{ctx}" in proxy: # ctx will only be available in case of memory-session with proxy
            kwargs["proxy"] = proxy.format(ctx=session_id)
        if "impersonate" not in kwargs:
            kwargs["impersonate"] = "chrome"
        self.logger.debug("created", session=session_id, kwargs=kwargs, client=self.name)
        # will only be available in case of redis backend
        blp_created_at = kwargs.pop("extra", {}).get("created_at")
        transport = AsyncSession(max_clients=1, **kwargs)
        session = Session(id=session_id, age=self.settings.SESSION_AGE, transport=transport, blp_created_at=blp_created_at)
        return session


    async def request(
        self,
        url: str,
        method: str = "GET",
        dont_filter: bool = False,
        **kwargs,
    ) -> Response | None:
        if not dont_filter:
            if await self.db.exists(url, "http_client"):
                self.logger.debug("duplicate", url=url, client=self.name)
                return

        session = await self.session_manager.get_session()
        try:
            if session.is_over_age():
                session = await self.session_manager.replace_session(session, reason="retired")

            req_at = get_time()
            response: CurlResponse = await self._session_request(session, url=url, method=method, **kwargs)
            recv_at = get_time()
            latency = recv_at - req_at
            session.requests +=1
            self.logger.info("response", status=response.status_code, url=url, session_id=session.id, requests=session.requests, client=self.name, requested_at=req_at, responded_at=recv_at, latency_ms=latency, remote_ip=response.primary_ip, blp_created_at=session.blp_created_at)

            if response.status_code in self.settings.ACCESS_DENIAL_STATUS_CODES:
                session = await self.session_manager.replace_session(session, reason="expired")
        except asyncio.TimeoutError:
            session = await self.session_manager.replace_session(session, reason="timeout")
            await self.session_manager.put_session(session)
            raise
        else:
            await self.session_manager.put_session(session)

        if not dont_filter:
            if response.status_code == 200:
                # 3 days
                await self.db.insert(url, "http_client", expiry_sec=259200)

        return Response(
            url=response.url,
            status=response.status_code,
            text=response.text,
            headers=dict(response.headers),
            cookies=dict(response.cookies),
            requested_at=req_at,
            responded_at=recv_at,
            latency_ms=latency,
            body=response.content,
            raw_response=response,
        )


    async def direct_request(
        self,
        url: str,
        method: str = "GET",
        dont_filter: bool = False,
        **kwargs,
    ) -> Response | None:
        if not dont_filter:
            if await self.db.exists(url, "http_client"):
                self.logger.debug("duplicate", url=url, client=self.name)
                return

        async with AsyncSession(max_clients=1) as s:
            try:
                req_at = get_time()
                response: CurlResponse = await s.request(url=url, method=method, **kwargs)
                recv_at = get_time()
                latency = recv_at - req_at
                self.logger.info("response", status=response.status_code, url=url, client=self.name, requested_at=req_at, responded_at=recv_at, latency_ms=latency, remote_ip=response.primary_ip)
            except Exception as e:
                self.logger.error("request", exception=str(e), url=url, client=self.name)
                raise

        if not dont_filter:
            if response.status_code == 200:
                # 3 days
                await self.db.insert(url, "http_client", expiry_sec=259200)

        return Response(
            url=response.url,
            status=response.status_code,
            text=response.text,
            headers=dict(response.headers),
            cookies=dict(response.cookies),
            requested_at=req_at,
            responded_at=recv_at,
            latency_ms=latency,
            body=response.content,
            raw_response=response,
        )

