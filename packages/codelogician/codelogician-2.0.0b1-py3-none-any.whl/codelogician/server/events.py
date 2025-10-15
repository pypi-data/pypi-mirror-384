#
# Imandra Inc. 
#
# events.py 
# 

import datetime
from pydantic import BaseModel, Field
from enum import StrEnum

class ServerEvent(BaseModel):
    """
    Base class for all server events.
    """
    time : datetime.datetime = Field(default_factory=datetime.datetime.now)

class FileSystemEventType (StrEnum):
    """
    Enum to identify the type of filesystem event that occured
    """
    CREATED = 'Created'
    MODIFIED = 'Modified'
    DELETED = 'Deleted'
    MOVED = 'Moved'

class FileSystemEvent(ServerEvent, BaseModel):
    """
    Filesystem event 
    """
    action_type : FileSystemEventType
    abs_path1 : str 
    abs_path2 : str = ""

class FileSystemCheckbackEvent(ServerEvent, BaseModel):
    """ 
    This is the event that's sent out on a timer after the proper FileSystemEvent.
    The reason is that we don't want to react to every single file save, etc. So we want to wait
    until the user "settles down" editing their files. So, on each FileSystemEvent, we setup a timer
    to check on the file and if there hasn't been any changes to the files and we're in AUTO mode,
    then we kick off formalization.
    """
    
    abs_path : str
