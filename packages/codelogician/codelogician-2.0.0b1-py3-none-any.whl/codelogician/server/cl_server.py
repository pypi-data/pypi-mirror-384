#
#   CodeLogician Server
#
#   server.py
#

import unittest, logging, os
from pathlib import Path

log = logging.getLogger(__name__)
from ..strategy.sketch import Sketch
from ..strategy.state import StrategyState
from ..strategy.model import Model
from ..strategy.pyiml_strategy import PyIMLStrategy
from ..strategy.config import StratConfig

from .state import ServerState
from .config import ServerConfig
from .events import FileSystemEvent, FileSystemEventType
from .file_event_handler import MyFileSysEventHandler

from typing import Dict
from watchdog.observers import Observer
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP


@asynccontextmanager
async def lifespan(app: 'CLServer'):
    """
    This handles events that happen on start/shutdown of the FastAPI server
    """

    for strat_worker in app.strategy_workers.values():
        app.file_sys_observer.schedule(
            MyFileSysEventHandler(app.file_event_callback), 
            strat_worker.state().src_dir_abs_path, 
            recursive=True
        )

        if not strat_worker.is_alive():
            strat_worker.start()
            log.info(f"Strategy thread [{strat_worker.state().src_dir_abs_path}] started")
 

    app.file_sys_observer.start()
    log.info("File system observer started!")

    # Let's now pass on the control to other parts of the system
    yield

    # This should kill the `run` loop
    log.info("Sending `None` event to strategies to shut them down!")
    for strategy in app.strategy_workers.values():
      strategy.add_event(None)

    # Let's send in these just in case
    app.file_sys_observer.stop()

    # Now let's wait for them to finish
    for strategy in app.strategy_workers.values():
      strategy.join() # Let's wait for the strategy to stop
      strategy.state().save() # Now let's save its state to disk

    app.file_sys_observer.join()

    app.save_state()

class CLServer (FastAPI):
    """ Class for CL Server """

    def __init__(self, server_state : ServerState):
        """ ctor """
        super().__init__(title="CLServer", lifespan=lifespan)
        self._state = server_state # Config is part of the state

        # This is the container of all strategy workers (threads)        
        self.strategy_workers : Dict[str, PyIMLStrategy] = {}

        # If we have initial strategies in our config, we will now create
        # actual strategy threads for them
        self.create_strat_workers()

        # Observer will help us monitor filesystem events
        self.file_sys_observer = Observer()

        # Now let's setup the MCP server 
        if self._state.config.mcp:
            self.mount_mcp_server()

    def search_sketches(self, query:str)-> list[Model]:
        """
        return list of models for specified query
        """

        return []

    def all_sketch_ids (self) -> list[str]:
        """ 
        Return the full list of sketch IDs
        """

        all_ids = []
        for strat_id in self.strategy_workers:
            all_ids.extend(self.strategy_workers[strat_id].state().sketch_ids())

        return all_ids

    def get_strat_for_sketch_id (self, sketch_id : str) -> PyIMLStrategy | None:
        """ 
        return strategy ID for a corresponding sketch ID (or None if can't find it)
        """

        for strat_id in self.strategy_workers:
            if sketch_id in self.strategy_workers[strat_id].state().sketch_ids():
                return self.strategy_workers[strat_id]
            
        return None
    
    def get_sketch_from_sketch_id (self, sketch_id : str) -> Sketch | None:
        """
        Return Sketch object from the specified sketch_id
        """
        for strat_id in self.strategy_workers:
            if sketch_id in self.strategy_workers[strat_id].state().sketch_ids():
                return self.strategy_workers[strat_id].state().sketches.from_id(sketch_id)
        
        return None

    def create_sketch(self, strat_id : str, anchor_model_path : str) -> str:
        """ 
        Create a new sketch and return its sketch ID
        """

        if strat_id not in self.strategy_workers:
            raise Exception (f"Could not locate the specified strategy: {strat_id}")

        return self.strategy_workers[strat_id].state().create_new_sketch(anchor_model_path)

    def list_sketches (self) -> Dict[str,list[Dict[str,str]]]:
        """ 
        Return list of sketches by strategy
        """

        result = {}

        for strat_id in self.strategy_workers:
            result[strat_id] = self.strategy_workers[strat_id].state().list_sketches()

        return result

    def list_strategies (self) -> list[Dict[str,str]]:
        """
        Return a list of dictionaries specifying the strategies currently running
        """
        
        strats = []
        for strat_id in self.strategy_workers:
            strat = {
                'strat_id': strat_id,
                'path': self.strategy_workers[strat_id].state().src_dir_abs_path,
                'type': 'Python' # for now, we only support python
            }
            strats.append(strat)
        
        return strats
        
    def create_strat_workers(self):
        """ We go through the list of paths we have, initialize their states """
        
        log.info(f"Will now instantiate server strategies. I have {len(self._state.strategy_paths)} paths!")

        for path in list(set(self._state.strategy_paths)):
            try:
                strat_state = StrategyState.from_directory(path)
                self.strategy_workers[strat_state.strat_id] = PyIMLStrategy(strat_state)
            except Exception as e:
                log.error(f"Error during strategy instantiation: {path}: {str(e)}")
                continue

            log.info(f"Created strategy worker for {path}.")
    
    def setup_strat_configs(self, strat_config:str):
        """ Load up configuration for strategies """

        try:
            stratConfig = StratConfig.fromYAML(strat_config)        
            log.info(f"Reading in StratConfig file: {strat_config}")
            log.info(stratConfig)
        except Exception as e:
            log.error(f"Failed to load StratConfig: {str(e)}. Switching to defaults.")
            stratConfig = StratConfig()

    # def setup_server_config(self, server_config:str):
    #     # Let's try to load in the server config file
    #     try:
    #         serverConfig = ServerConfig.fromYAML(server_config)
    #         log.info (f"Reading in configuration file: {server_config}")
    #         log.info (serverConfig)
    #     except Exception as e:
    #         log.error(f"Failed to load server configuration: {str(e)}. Switching to defaults.")
    #         serverConfig = ServerConfig()

    #     return serverConfig

    def mount_mcp_server(self):
        """
        Mount the MCP server
        """

        log.info(f"Starting to mount MCP server...")
        mcp = FastApiMCP (
            self
            , name="CodeLogician Server"
            , description="MCP server for CodeLogician Server"
            , describe_full_response_schema=True
            , describe_all_responses=True
        )

        # Mount the MCP server directly to your FastAPI app
        mcp.mount_http()
        log.info(f"MCP server mounted!")
    
    
    def strategy_worker_by_id(self, strat_id:str) -> PyIMLStrategy:
        """ 
        Return strategy worker for specified ID
        """
        if strat_id not in self.strategy_workers:
            raise Exception(f"Specified ID not found: {strat_id}")
        
        return self.strategy_workers[strat_id]

    def strategy_state_by_id (self, strat_id:str) -> StrategyState:
        """
        Return strategy state for specified ID
        """

        if strat_id not in self.strategy_workers:
            raise Exception(f"Specified ID not found: {strat_id}")
        
        return self.strategy_workers[strat_id].state()

    def strategy_states (self) -> Dict[str, StrategyState]:
        """
        Return dictionary of all strategy states
        """

        states = {s.state().strat_id:s.state() for s in self.strategy_workers.values()}
        return states

    def strategy_config_by_id (self, strat_id : str) -> StratConfig:
        """
        Return strategy config for specified ID
        """

        if not (strat_id in self.strategy_workers):
            raise Exception(f"Specified ID not found: {strat_id}")
        
        return self.strategy_workers[strat_id].config()

    def update_strat_config (self, strat_id:str, strat_config:StratConfig):
        """
        Update strategy configuration for the specified strategy
        """

        if strat_id not in self.strategy_workers:
            raise Exception (f"Specified strategy [{strat_id}] not found!")
        
        self.strategy_workers[strat_id].update_config(strat_config)

    @staticmethod
    def is_path_valid(new_path : str, existing_paths : list[str]) -> bool:
        """
        Return True/False if the specified path doesn't overlap with existing strategies' paths
        """

        if new_path in existing_paths: return False

        for curr_path in existing_paths:
            if Path(curr_path).is_relative_to(Path(new_path)) or \
                Path(new_path).is_relative_to(Path(curr_path)): return False

        return True

    def add_strategy(self, new_strat_path : str) -> str:
        """
        Add a new strategy and return its ID
        """

        new_strat_path = str(Path(new_strat_path).resolve())
    
        if not os.path.exists(new_strat_path):
            raise Exception(f"Failed to create new strategy: specified path [{new_strat_path}] doesn't exist!")
  
        existing_paths = [ s.state().src_dir_abs_path for s in self.strategy_workers.values() ]

        if not self.is_path_valid(new_strat_path, existing_paths):
            raise Exception(f"Specified path is not valid: {new_strat_path}")

        if Path(new_strat_path).is_dir():
            try:
                strat_state = StrategyState.from_directory(new_strat_path)
            except:
                strat_state = StrategyState(src_dir_abs_path=new_strat_path)
        else:
            try:
                strat_state = StrategyState.fromFile(new_strat_path)
            except:
                strat_state = StrategyState(src_dir_abs_path=new_strat_path)

        try:
            self.strategy_workers[strat_state.strat_id] = PyIMLStrategy(state=strat_state)
            self.strategy_workers[strat_state.strat_id].start()
        except Exception as e:
            raise Exception (f"Failed to create ther worker: {e}")

        self.file_sys_observer.schedule(
            MyFileSysEventHandler(self.file_event_callback), 
                self.strategy_workers[strat_state.strat_id].state().src_dir_abs_path, 
                recursive=True
            )

        log.info(f"Started Strategy for dir: {strat_state.src_dir_abs_path}")

        return strat_state.strat_id
    
    def rem_strategy(self, strat_id : str) -> None:
        """
        Remove strategy (by strat_id)
        """

        if strat_id not in self.strategy_workers:
            raise Exception (f"Specified strategy path does not exist: {strat_id}")

        self.strategy_workers[strat_id].add_event(None) # this should stop it
        self.strategy_workers[strat_id].join()
        del self.strategy_workers[strat_id]

    def path_to_strategy(self, filepath : str) -> str|None:
        """
        Return strategy ID if the file path is contained within this
        """

        def good_extension(extensions):
            for ext in extensions:
                if filepath.endswith(ext): return True
            return False

        for strat_id in self.strategy_workers:
            strat_state : StrategyState = self.strategy_workers[strat_id].state()

            if Path(filepath).is_relative_to(Path(strat_state.src_dir_abs_path)):
                # Let's check that this is not a directory and the right file extension for this strategy
                if not Path(filepath).is_dir() and good_extension(self.strategy_workers[strat_id].extensions):
                    return strat_id
        
        return None

    def file_event_callback(self, event:FileSystemEvent, event_type:FileSystemEventType) -> None:
        """
        Gets called by the FileSystemEventObserver - this routes event to the right strategy
        """

        strat_id = self.path_to_strategy(event.src_path)

        if strat_id is None:
            log.info(f"Received an event, but couldnt assign it to a strategy: {event.src_path}; {event_type}")
            return

        strategy = self.strategy_workers[strat_id]

        if event_type in [FileSystemEventType.CREATED, FileSystemEventType.MODIFIED, FileSystemEventType.DELETED]:
            ext = Path(event.src_path).suffix
            if ext in strategy.extensions:
                self.strategy_workers[strat_id].add_event(
                    FileSystemEvent(
                        action_type = event_type,
                        abs_path1 = event.src_path
                    )
                )
            else:
                log.warning(f"Received a filsystem event for file with unsupported extension: {ext}")

        elif event_type == FileSystemEventType.MOVED:
            src_ext = Path(event.src_path).suffix
            dest_ext = Path(event.dest_path).suffix

            if src_ext in strategy.extensions and dest_ext in strategy.extensions:
                self.strategy_workers[strat_id].add_event(
                    FileSystemEvent(
                        action_type = event_type,
                        abs_path1=event.src_path,
                        abs_path2=event.dest_path
                    )
                )
            else:
                log.warning(f"Received a filesystem event for file with unsupported extension: {src_ext} -> {dest_ext}")
            
        else:
            log.error(f"Received an unknown event type: {event_type}")

    def save_state(self) -> None:
        """
        Attempt to save the current server state information. Note that we're only recording the 
        paths to strategies - they will save their own states there... 
        """

        log.info("Will save server state now.")
        self._state.strategy_paths = []

        for s in self.strategy_workers.values():
            log.info (f"Adding {str(s.state().src_dir_abs_path)}")
            self._state.strategy_paths.append(str(s.state().src_dir_abs_path))

        try:
            self._state.save()
        except Exception as e:
            log.error(f"Failed to save server state to disk: {e}")
