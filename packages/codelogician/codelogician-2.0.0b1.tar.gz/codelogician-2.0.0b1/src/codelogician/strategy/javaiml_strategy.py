#
#   Imandra Inc.
#
#   javaiml_strategy.py
#

from .pyiml_strategy import PyIMLStrategy
from .state import StrategyState
from ..server.events import (
    ServerEvent,
    FileSystemCheckbackEvent,
    FileSystemEvent
)
import logging

log = logging.getLogger(__name__)

class JavaIMLStrategy(PyIMLStrategy):
    """ Java strategy  """

    language = 'Java'

    def __init__ (self, state:StrategyState):
        super().__init__(state=state)

    def watch_directories(self):
        """ Return the list of directories the observer should watch """
        return []
        #return self.abs_src_dir

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


