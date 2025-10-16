from typing import Any, Dict, List
from abc import abstractmethod
from dataclasses import dataclass

from ...utils import FactoryEnabled

def _trim_indent_in_block(block):
    # only works for spaces, not tabs
    first_line = block.strip('\n').split("\n")[0]
    indent = len(first_line) - len(first_line.lstrip())
    return "\n".join([
        line[indent:] if len(line) > indent else line
        for line in block.strip('\n').split("\n")
    ]).strip()

def _combine_passages(passages):
    return "\n\n".join(
        f"[{i+1}] {text}" for i, text in enumerate(passages)
    )


@dataclass
class PromptBuilder(FactoryEnabled):
    @abstractmethod
    def __call__(self, query: str, candidates: List[str]) -> List[str]:
        raise NotImplementedError


@dataclass
class ResponseParser(FactoryEnabled):
    @abstractmethod
    def __call__(self, responses: List[str]) -> Dict[int, float]:
        raise NotImplementedError


@dataclass
class RankKPromptBuilder(PromptBuilder):

    prompt = _trim_indent_in_block("""
        Determine a ranking of the passages based on how relevant they are to the query. 
        If the query is a question, how relevant a passage is depends on how well it answers the question. 
        If not, try analyze the intent of the query and assess how well each passage satisfy the intent. 
        The query may have typos and passages may contain contradicting information. 
        However, we do not get into fact-checking. We just rank the passages based on they relevancy to the query. 

        Sort them from the most relevant to the least. 
        Answer with the passage number using a format of `[3] > [2] > [4] = [1] > [5]`. 
        Ties are acceptable if they are equally relevant. 
        I need you to be accurate but overthinking it is unnecessary.
        Output only the ordering without any other text.

        Query: {query}

        {docs}
    """)

    def __call__(self, query, candidates):
        return [ 
            self.prompt.format(query=query, docs=_combine_passages(candidates))
        ]


@dataclass
class NumberListParser(ResponseParser):
    def __call__(self, responses: List[str], pids: List[Any]):
        assert len(responses) == 1
        
        rr = responses[0].strip().split("\n")[-1].split(">")
        ranking = []
        for i, p in enumerate(rr):
            for pidxstring in p.split("="):
                pdix = pidxstring.strip().replace("[", "").replace("]", "")
                
                try: 
                    pid = pids[int(pdix) - 1]
                except KeyboardInterrupt:
                    pass
                except:
                    continue
                    
                if pid in ranking:
                    return ranking
                ranking.append(pid)
            
        return ranking


"[7] > [3] > [8] > [18] > [12] = [13] = [14] = [10] > [19] > [5] > [20] > [1] = [4] = [6] = [9] = [11] = [15] = [16] = [17]"