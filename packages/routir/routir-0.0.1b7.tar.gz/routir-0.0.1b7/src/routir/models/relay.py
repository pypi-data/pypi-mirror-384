from typing import Dict, Any, List, Tuple, Union
import aiohttp
import asyncio
from .abstract import Engine, _session_request
from ..processors.registry import ProcessorRegistry

class Relay(Engine):

    def __init__(
            self, name: str = None, config = None, 
            **kwargs
        ):
        super().__init__(name, config, **kwargs)

        assert 'service' in self.config

        self.other_kwargs = self.config.get('other_request_kwargs', {})
        # TODO: should support some runtime config like retry and timeout
        # TODO: support list of endpoints for load balancing 

    async def search_batch(self, queries, subsets=None, **kwargs):
        if subsets is None:
            subsets = ['none']*len(queries)
        assert len(subsets) == len(queries)

        for key in kwargs:
            if isinstance(kwargs[key], list):
                assert len(kwargs[key]) == len(queries)
            else:
                kwargs[key] = [kwargs[key]]*len(queries)
        
        payloads = [
            { 
                'query': queries[i],
                'service': self.config['service'],
                'subset': subsets[i],
                **self.other_kwargs,
                **{ k: kwargs[k][i] for k in kwargs },
            }
            for i in range(len(queries))
        ]

        if 'endpoint' in self.config:
            async with aiohttp.ClientSession() as session:
                resps = await asyncio.gather(*[ 
                    _session_request(session, f"{self.config['endpoint']}/query", load) 
                    for load in payloads
                ])
        else:
            assert ProcessorRegistry.has_service(self.config['service'], 'query')
            local_processor = ProcessorRegistry.get(self.config['service'], 'query')
            resps = await asyncio.gather(*[
                local_processor.submit(load)
                for load in payloads
            ])
        

        for resp, query in zip(resps, queries):
            assert resp['query'] == query
        return [ 
            # for backward compatiblity if the service is using `result` as key
            resp.get('scores', resp.get('result', {})) for resp in resps 
        ]
