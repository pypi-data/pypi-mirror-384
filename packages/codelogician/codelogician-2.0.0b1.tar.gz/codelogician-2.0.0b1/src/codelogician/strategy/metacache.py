#
#   Imandra Inc.
#
#   metacache.py
#

from .metamodel import MetaModel
from .events import StrategyEvent
from ..server.events import ServerEvent

from pydantic import BaseModel
from typing import Dict

class CacheEntry(BaseModel):
    event : StrategyEvent|ServerEvent
    mmodel : MetaModel

class MetaCache(BaseModel):
    """
    Helps us manage the cache of historic metamodel states, load/save them to disk
    """

    cache : list[CacheEntry] = []

    def latest_mmodel(self) -> MetaModel|None:
        """
        Return the latest model
        """
        if len(self.cache) > 0:
            return self.cache[0].mmodel
        
        return None

    def save_meta_model(self, event: StrategyEvent|ServerEvent, mmodel : MetaModel):
        """
        Save combination of event (server/strategy) and metamodel to cache
        """
        self.cache.insert(0, CacheEntry(event = event, mmodel = mmodel))

    def get_cache_metamodel(self, idx:int) -> MetaModel|None:
        """
        Return the cache model if it exists
        """
        if 0 <= idx and idx < len(self.cache):
            return self.cache[idx].mmodel
        else:
            return None

    def indices(self):
        """
        Return the list of available indices
        """
        return list(range(len(self.cache)))

