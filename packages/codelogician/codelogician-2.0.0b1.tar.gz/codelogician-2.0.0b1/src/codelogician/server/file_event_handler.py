#
#   Imandra Inc.
#
#   file_event_handler.py
#

import logging

from ..server.events import FileSystemEventType
from watchdog.events import FileSystemEventHandler

log = logging.getLogger(__name__)

class MyFileSysEventHandler(FileSystemEventHandler):
    """
    This monitors the filesystem and creates events which the strategy thread will then process 
    """

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_created(self, event):
        """
        File created: `event.src_path`
        """
        self.callback(event, FileSystemEventType.CREATED)

    def on_modified(self, event):
        """
        File is modified: `event.src_path`
        """
        self.callback(event, FileSystemEventType.MODIFIED)

    def on_deleted(self, event):
        """
        Filed was deleted: `event.src_path`
        """
        self.callback(event, FileSystemEventType.DELETED)

    def on_moved(self, event):
        """
        File moved from `event.src_path` to `event.dest_path`
        """
        self.callback(event, FileSystemEventType.MOVED)
