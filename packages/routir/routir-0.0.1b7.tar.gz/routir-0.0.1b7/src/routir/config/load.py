from pathlib import Path
from .config import Config
from ..models import Engine
from ..processors import ProcessorRegistry, Processor, ContentProcessor, BatchPairwiseScoreProcessor
from ..utils import logger
from ..utils.extensions import load_all_extensions

async def load_config(config: str):

    if Path(config).exists():
        config = Path(config).read_text()
    
    config: Config = Config.model_validate_json(config)

    load_all_extensions(user_specified_files=config.file_imports)

    for collection_config in config.collections:
        ProcessorRegistry.register(
            collection_config.name, 'content', ContentProcessor(collection_config)
        )
    logger.info(f"All collections are loaded")

    for service_config in config.services:
        cache_key = lambda x: tuple( x.get(k, "") for k in service_config.cache_key_fields )
        
        engine: Engine = Engine.load(
            service_config.engine, 
            name=service_config.name, 
            config=service_config.config
        )
        
        processor: Processor = Processor.load(
            service_config.processor,
            engine=engine,
            batch_size=service_config.batch_size,
            max_wait_time=service_config.max_wait_time,
            cache_size=service_config.cache,
            cache_ttl=service_config.cache_ttl,
            cache_key=cache_key,
            redis_url=service_config.cache_redis_url,
            redis_kwargs=service_config.cache_redis_kwargs
        )
        await processor.start()
        ProcessorRegistry.register(service_config.name, 'search', processor)

        if engine.can_score and not service_config.scoring_disabled: 

            processor = BatchPairwiseScoreProcessor(
                engine,
                batch_size=service_config.batch_size,
                max_wait_time=service_config.max_wait_time,
                cache_size=-1 # turn off cache for now
            )
            await processor.start()
            ProcessorRegistry.register(service_config.name, 'score', processor)

        logger.info(f"{service_config.name} initialized and ready")


    logger.info(f"All services are initialized")