from typing import Any, Dict, List, Tuple, Union

import os
import asyncio
import uuid
from functools import partial

from ..abstract import Reranker

from .prompts import PromptBuilder, ResponseParser
from ...utils import logger

# engine = AsyncLLMEngine.from_engine_args(AsyncEngineArgs(model="Qwen/QwQ-32B", tensor_parallel_size=4, distributed_executor_backend="ray"))


# TODO: at some point thes should be class and implement the same interface and
# fold in the init in them, but probably good enough for now.
async def _openai_completion(client, model, prompts, **kwargs):
    if 'temperature' not in kwargs:
        kwargs['temperature'] = 0.6
    if 'max_tokens' not in kwargs:
        kwargs['max_tokens'] = 2000

    res = await asyncio.gather(*[
        client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            **kwargs
        )
        for prompt in prompts
    ])

    return [ r.choices[0].message.content.strip() for r in res ]

# TODO: still buggy
async def _vllm_async_completion(engine, prompts, **kwargs):
    from vllm import SamplingParams
    # Submit all requests
    request_ids = [uuid.uuid4() for _ in range(len(prompts))]
    sampling_params = SamplingParams(*kwargs)
        
    # Add request to engine
    await asyncio.gather(*[
        engine.add_request(
            request_id=request_id,
            prompt=prompt,
            params=sampling_params
        )
        for request_id, prompt in zip(request_ids, prompts)
    ])
    
    # Process results as they complete
    results = {}
    while len(results) < len(prompts):
        request_outputs = await engine.step_async()
        
        for request_output in request_outputs:
            if request_output.finished:
                results[request_output.request_id] = request_output.outputs[0].text.strip()
    
    return [ results[request_id] for request_id in request_ids ]
    

class LLMReranker(Reranker):

    def __init__(self, name=None, config=None, **kwargs):
        super().__init__(name, config, **kwargs)

        assert 'model_name_or_path' in self.config

        if 'server_endpoint' in self.config:
            import openai
            client = openai.AsyncOpenAI(
                api_key=self.config.get('api_key', os.getenv("OPENAI_API_KEY", "noneset")), 
                base_url=self.config['server_endpoint']
            )
            self.llm_caller = partial(
                _openai_completion, client, self.config['model_name_or_path'],
                **self.config.get('request_kws', {})
            )
        else:
            from vllm import AsyncLLMEngine, AsyncEngineArgs    
            import torch
            engine = AsyncLLMEngine.from_engine_args(AsyncEngineArgs(
                model=self.config['model_name_or_path'], 
                tensor_parallel_size=torch.cuda.device_count(), 
                distributed_executor_backend="ray",
                **self.config.get('init_kws', {})
            ))
            self.llm_caller = partial(
                _vllm_async_completion, engine, **self.config.get('request_kws', {})
            )
        
        self.truncator = lambda x: x
        if 'truncate_doc_to_n_tokens' in self.config and self.config['truncate_doc_to_n_tokens'] > 0:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(self.config.get('tokenizer_name', self.config['model_name_or_path']), use_fast=True)
            self.truncator = lambda x: tokenizer.decode(tokenizer.encode(x)[:self.config['truncate_doc_to_n_tokens']])
        
        self.prompt_builder = PromptBuilder.load(self.config.get('prompt_builder', 'RankKPromptBuilder'))
        self.response_parser = ResponseParser.load(self.config.get('response_parser', 'NumberListParser'))

        self.window_size = int(self.config.get('rerank_window', 20))
        self.stride_size = int(self.config.get('rerank_stride', 10))

    async def rerank_call(self, query, doc_ids, candidates):
        resp = await self.llm_caller(self.prompt_builder(query, candidates))
        new_ranking: List[Any] = self.response_parser(resp, doc_ids)

        # new_ranking = [
        #     doc_id for doc_id, score in sorted(scores.items(), key=lambda x: -x[1])
        # ]

        if len(new_ranking) < len(doc_ids):
            adding = [
                d for d in doc_ids if d not in new_ranking
            ]
            print(f"{new_ranking} ------ {adding}")
            new_ranking += [
                d for d in doc_ids if d not in new_ranking
            ]
        

        assert len(doc_ids) == len(new_ranking)
        # , f"========== {len(doc_ids)}, {len(new_ranking)}, {new_ranking}"

        return new_ranking

    async def rerank_single_query(self, query: str, docs: List[str], stride_size: int=None, window_size: int=None):
        global_doc_idx = list(range(len(docs)))
        stride_size = stride_size if stride_size is not None else self.stride_size
        window_size = window_size if window_size is not None else self.window_size

        for rerank_end_idx in range(len(docs), 0, -stride_size):
            rerank_start_idx = max(rerank_end_idx - window_size, 0)
            
            logger.info(f"Reranking idx {rerank_start_idx} to {rerank_end_idx}")
            doc_ids = global_doc_idx[rerank_start_idx:rerank_end_idx].copy()

            global_doc_idx[rerank_start_idx:rerank_end_idx] = await self.rerank_call(
                query, doc_ids, [ docs[did] for did in doc_ids ]
            )

            if rerank_start_idx == 0: 
                break
        
        return global_doc_idx

    async def score(self, queries, all_docs, candidate_length = None, with_progress = False, **kwargs):
        # TODO: worth later on make it single call instead of batching to support async
        # Batching is probably a bad idea here.
        truncated_docs = list(map(self.truncator, all_docs))

        if candidate_length is None:
            assert len(queries) == 1
            candidate_length = [len(all_docs)]
        
        s = 0
        tasks = []
        for query, n_docs in zip(queries, candidate_length):
            tasks.append(self.rerank_single_query(
                query=query, docs=truncated_docs[s:s+n_docs],
                stride_size=kwargs.get('stride_size'), window_size=kwargs.get('window_size')
            ))
            s += n_docs

        results = await asyncio.gather(*tasks)

        s = 0
        all_scores = {}
        for qidx, (reranked_list, n_docs) in enumerate(zip(results, candidate_length)):
            assert len(reranked_list) == n_docs
            for pos, local_didx in enumerate(reranked_list):
                all_scores[(qidx, s+local_didx)] = 1/(pos+1)
            s += n_docs
        
        return all_scores


        

