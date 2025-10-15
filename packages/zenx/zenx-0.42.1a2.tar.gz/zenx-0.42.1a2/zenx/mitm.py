from typing import Dict, List
import redis.asyncio as redis
import asyncio

from zenx.settings import settings
from zenx.logger import configure_logger
from zenx.spiders.base import Spider


logger = configure_logger("mitm", settings)
solver_redis = redis.Redis(host=settings.SOLVER_REDIS_HOST, port=6379, password=settings.SOLVER_REDIS_PASS, decode_responses=True, socket_timeout=30)
local_redis = redis.Redis(host="localhost", port=6379, decode_responses=True, socket_timeout=30)


async def consume_list(list_key: str):
    logger.info("consuming", redis_list=list_key)
    while True:
        try:
            blueprints = await solver_redis.rpop(list_key, count=100)
            if not blueprints:
                logger.debug("empty", redis_list=list_key)
                continue
            await local_redis.lpush(list_key, *blueprints)
            logger.info("got", redis_list=list_key, blueprints=len(blueprints))
        except Exception:
            logger.exception("consuming_failed", redis_list=list_key)
            continue


async def subscribe(channel: str) -> None:
    local_p = local_redis.pubsub()
    await local_p.subscribe(channel)
    logger.info("subscribed", channel=channel)

    async for msg in local_p.listen():
        logger.debug("message", content=msg)
        await solver_redis.publish(channel, msg)
        logger.debug("published", channel=channel, msg=msg)


def collect_targets() -> List[Dict]:
    targets = []
    spiders = Spider.spider_list()
    for spider in spiders:
        spider_cls = Spider.get_spider(spider)
        blueprint_list = spider_cls.custom_settings.get("SESSION_BLUEPRINT_REDIS_LIST")
        if not blueprint_list and len(spiders) == 1:
            blueprint_list = settings.SESSION_BLUEPRINT_REDIS_LIST
        if not blueprint_list:
            continue
        blueprint_channel = spider_cls.custom_settings.get("SESSION_BLUEPRINT_REDIS_CHANNEL")
        if not blueprint_channel and len(spiders) == 1:
            blueprint_channel = settings.SESSION_BLUEPRINT_REDIS_CHANNEL
        if not blueprint_channel:
            continue
        targets.append((blueprint_list, blueprint_channel))
    logger.info("collected_targets", targets=targets)
    return targets


async def run():
    targets = collect_targets()
    async with asyncio.TaskGroup() as tg:
        for list_key, channel in targets:
            tg.create_task(consume_list(list_key))
            tg.create_task(subscribe(channel))
