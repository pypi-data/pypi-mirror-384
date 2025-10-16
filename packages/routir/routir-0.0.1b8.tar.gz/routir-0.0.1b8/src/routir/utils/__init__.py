from abc import ABC
import logging
from pathlib import Path
import pickle
from typing import Any, Dict, List
from tqdm.auto import tqdm

logging.basicConfig(
    format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger("search-service") 

def pbar(it=None, **kwargs):
    if 'dynamic_ncols' not in kwargs:
        kwargs['dynamic_ncols'] = True

    return tqdm(it, **kwargs)

_file_singleton = {}
def load_singleton(fn, load_fn=None):
    global _file_singleton
    fn = str(Path(fn).absolute())
    if fn not in _file_singleton:
        if load_fn is None:
            with open(fn, 'rb') as f:
                _file_singleton[fn] = pickle.load(f)
        else:
            _file_singleton[fn] = load_fn(fn)
        
    return _file_singleton[fn]

def dict_topk(scores: Dict[Any, float], k: int) -> Dict[Any, float]:
    return dict(sorted(scores.items(), key=lambda x: -x[1])[:k])

def _recursive_subclasses(cls: type):
    for subcls in cls.__subclasses__():
        yield subcls
        yield from _recursive_subclasses(subcls)


class FactoryEnabled(ABC):

    @classmethod
    def load(cls, cls_name: str, **kwargs):
        for subcls in _recursive_subclasses(cls):
            if subcls.__name__ == cls_name or subcls == cls_name:
                return subcls(**kwargs)

        raise TypeError(f"Unsupported subclass {cls_name} for {cls.__name__}")