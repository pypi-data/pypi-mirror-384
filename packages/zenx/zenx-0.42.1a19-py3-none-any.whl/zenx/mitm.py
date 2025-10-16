from typing import Dict, List
import redis.asyncio as redis
import asyncio

from zenx.settings import settings
from zenx.logger import configure_logger
from zenx.spiders.base import Spider


logger = configure_logger("mitm", settings)
solver_redis = redis.Redis(host=settings.SOLVER_REDIS_HOST, port=settings.SOLVER_REDIS_PORT, password=settings.SOLVER_REDIS_PASS, decode_responses=True, socket_timeout=30)
local_redis = redis.Redis(host="localhost", port=6379, decode_responses=True, socket_timeout=30)


async def handle_result(queue: str):
    logger.info("started", handler="result", queue=queue)
    while True:
        try:
            results = await solver_redis.rpop(queue, count=100)
            if not results:
                logger.debug("empty", queue=queue)
                await asyncio.sleep(1)
                continue
            await local_redis.lpush(queue, *results)
            logger.info("got", queue=queue, results=len(results))
        except Exception:
            logger.exception("failed", handler="result", queue=queue)


async def handle_message(queue: str) -> None:
    logger.info("started", handler="message", queue=queue)
    while True:
        try:
            messages = await local_redis.rpop(queue, count=100)
            if not messages:
                logger.debug("empty", queue=queue)
                await asyncio.sleep(1)
                continue
            await solver_redis.lpush(queue, *messages)
            logger.info("sent", queue=queue, messages=len(messages))
        except Exception:
            logger.exception("failed", handler="message", queue=queue)


def collect_targets() -> List[Dict]:
    targets = []
    spiders = Spider.spider_list()
    for spider in spiders:
        spider_cls = Spider.get_spider(spider)
        result_q = spider_cls.custom_settings.get("REDIS_RESULT_QUEUE")
        if not result_q and len(spiders) == 1:
            result_q = settings.REDIS_RESULT_QUEUE
        if not result_q:
            continue
        msg_q = spider_cls.custom_settings.get("REDIS_MESSAGE_QUEUE")
        if not msg_q and len(spiders) == 1:
            msg_q = settings.REDIS_MESSAGE_QUEUE
        if not msg_q:
            continue
        targets.append((result_q, msg_q))
    logger.info("collected_targets", targets=targets)
    return targets


async def run():
    targets = collect_targets()
    async with asyncio.TaskGroup() as tg:
        for result_q, msg_q in targets:
            tg.create_task(handle_result(result_q))
            tg.create_task(handle_message(msg_q))
