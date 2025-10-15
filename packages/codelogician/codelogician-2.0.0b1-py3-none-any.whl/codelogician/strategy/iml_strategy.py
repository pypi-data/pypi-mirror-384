#
#   Imandra Inc.
#
#   iml_strategy.py
#

from threading import Thread

from .state import StrategyState
from ..server.events import FileSystemEvent

import logging
log = logging.getLogger(__name__)


class IMLStrategy(Thread):
    """
    Base class for all IML (ImandraX) strategies
    """

    def __init__ (self, state:StrategyState):
        super().__init__()
        self._state = state

    def watch_directories(self):
        """ Return the list of directories the observer should watch """
        return []

    def on_load (self):
        """ What should be done on startup """
        pass

    def on_filesystem_event(self, event : FileSystemEvent):
        """ """
        log.info(f"Received {event} to process")
    
    def on_save(self):
        """
        What should be done on strategy save
        """
        pass