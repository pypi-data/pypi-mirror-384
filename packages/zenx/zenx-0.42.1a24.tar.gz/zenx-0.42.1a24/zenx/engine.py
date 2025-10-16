import asyncio
import time
from typing import Dict, List
import pebble
import uvloop
import setproctitle

from zenx.logger import configure_logger
from zenx.monitors import Monitor
from zenx.pipelines import PipelineManager
from zenx.database import DBClient
from zenx.http import HttpClient
from zenx.schedular import Schedular
from zenx.spiders import Spider
from zenx.settings import Settings, settings as global_settings



class Engine:


    def __init__(self, forever: bool) -> None:
        self.forever = forever


    async def _execute_spider(self, spider_name: str, settings: Settings, spider_kwargs: Dict[str, str]) -> None:
        spider_cls = Spider.get_spider(spider_name)
        settings_data = settings.model_dump()
        settings_data.update(spider_cls.custom_settings)
        settings = Settings.model_validate(settings_data)

        log_file = spider_kwargs.get("LOG_FILE")
        log_file = f"{spider_cls.name}_{log_file}" if log_file else spider_cls.name
        logger = configure_logger(log_file, settings)
        if settings.SESSION_POOL_SIZE < settings.CONCURRENCY:
            settings.SESSION_POOL_SIZE = settings.CONCURRENCY

        db = DBClient.get_db(settings.DB_TYPE)(logger=logger, settings=settings)
        await db.open()

        client = HttpClient.get_client(spider_cls.client_name)(logger=logger, db=db, settings=settings) # type: ignore[call-arg]
        # await client.open()

        if settings.MONITORING_ENABLED:
            # this pipeline is only intended for providing data to itxp monitor
            spider_cls.pipelines.append("itxp") 
        pm = PipelineManager(
            pipeline_names=spider_cls.pipelines,
            logger=logger,
            db=db,
            settings=settings
        )
        await pm.open_pipelines()

        if not settings.MONITORING_ENABLED:
            spider_cls.monitor_name = None
        monitor = Monitor.get_monitor(spider_cls.monitor_name)(logger=logger, settings=settings) if spider_cls.monitor_name else None
        if monitor:
            await monitor.open()

        spider = spider_cls(client=client, pm=pm, logger=logger, settings=settings, monitor=monitor, **spider_kwargs)
        await spider.open()
        # First, run spider's open. This allows the spider to configure the client
        # before the client's connection pool is initialized.
        await client.open()
        try:
            loop = asyncio.get_running_loop()
            if self.forever:
                if settings.START_DATETIME:
                    real_world_start_time = settings.START_DATETIME.timestamp()
                    
                    real_world_clock = time.time()
                    monotonic_clock = loop.time()
                    offset = real_world_clock - monotonic_clock

                    start_time_on_loop = real_world_start_time - offset
                    start_time = start_time_on_loop
                elif settings.START_OFFSET_SECONDS >= 60: # for minute alignment
                    real_world_start_time = int(time.time() / 60) * 60 + settings.START_OFFSET_SECONDS 

                    real_world_clock = time.time()
                    monotonic_clock = loop.time()
                    offset = real_world_clock - monotonic_clock
                    
                    start_time_on_loop = real_world_start_time - offset
                    start_time = start_time_on_loop
                else:
                    start_time = loop.time()
                
                schedular_cls = Schedular.get_schedular(settings.SCHEDULAR)
                schedular = schedular_cls(logger, settings)
                
                await schedular.open()
                await schedular.run(spider.crawl, start_time)
                await schedular.close()
            else:
                await spider.crawl()
        except asyncio.CancelledError: # main func (_execute_spider) raises CancelledError instead of KeyboardInterrupt on ctrl+c
            logger.debug("cancelled", task="crawl", spider=spider_name)
        finally:
            logger.debug("waiting", background_tasks=len(spider.background_tasks), belong_to="spider", spider=spider_name)
            while spider.background_tasks:
                for t in list(spider.background_tasks):
                    # tasks that are long-running e.g someting inside loop
                    if "cancellable" in t.get_name():
                        t.cancel()
                await asyncio.gather(*spider.background_tasks, return_exceptions=True)
            logger.info("shutdown", spider=spider_name)
            await spider.close()
            await client.close()
            await db.close()
            if monitor:
                await monitor.close()
            await pm.close_pipelines()


    def run_spider(self, spider: str, spider_kwargs: Dict[str, str]) -> None:
        setproctitle.setproctitle(f"zenx-{global_settings.ZENX_VERSION}:{spider}")
        settings = global_settings.model_copy()
        uvloop.run(self._execute_spider(spider, settings, spider_kwargs))


    def run_spiders(self, spiders: List[str], spider_kwargs: Dict[str, str]) -> None:
        with pebble.ProcessPool(max_workers=len(spiders)) as pool:
            for spider in spiders:
                pool.schedule(self.run_spider, [spider, spider_kwargs])


