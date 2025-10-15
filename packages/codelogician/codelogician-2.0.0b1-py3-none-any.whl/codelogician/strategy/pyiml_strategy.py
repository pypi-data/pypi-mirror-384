#
#   Imandra Inc.
#
#   pyiml_strategy.py
#

import logging, os
from threading import Thread, Timer
from queue import Queue, Empty
from pathlib import Path

from rich.progress import Progress

from ..server.events import (
    ServerEvent,
    FileSystemCheckbackEvent,
    FileSystemEvent
)

from .events import (
    StrategyEvent,
    RunOneshotEvent,
    StratParamUpdate,
    ChangeMode,
    CLResultEvent,
    ModelCLTaskEvent,
    AutoModeCLTaskEvent,
    SketchChangeEvent,
    SketchChangeResultEvent
)


from .state  import StrategyState
from .config import StratConfig, StratMode
from .worker import CodeLogicianWorker
from .sketch import Sketch
from .sketch_task import SketchChangeTask
from .model_task import ModelTask, UserManualIMLEditTask

log = logging.getLogger(__name__)

class PyIMLStrategy(Thread):
    """
    Strategy is responsible for reacting to outside events and invoking CodeLogician/ImandraX.
    """

    language : str = 'Python'
    extensions : list[str] = ['.py', '.iml']

    def __init__ (
        self,
        state : StrategyState, 
        config : StratConfig = StratConfig(), 
        oneshot:bool=False):
        """ """
        super().__init__()

        self._config : StratConfig = config # Configuration container
        self._oneshot : bool = oneshot # In oneshot mode, we just run autoformalization once
        self._state : StrategyState = state  # Contains the entire formalization state

        # This will be our events queue
        self._queue = Queue()

        # CodeLogician worker
        # `add_event` is the callback function that'll be used to get the result back
        self._codeLogicianWorker = CodeLogicianWorker(self.add_event)
        self._codeLogicianWorker.start()

        #if oneshot:
        #    self.add_event(RunOneshotEvent())

        # Let's do a directory sync if we're in AUTO mode
        if self._config.mode == StratMode.AUTO:
            log.info("Starting file sync")
            self.state().run_file_sync()

            self.check_autoformalization_tasks()

        log.info('Started CodeLogician Worker thread')

    def language(self) -> str:
        """
        Return the programming language supported by this strategy.
        """
        return self.language

    def file_extensions(self) -> list[str]:
        """
        Return the list of file extensions this strategy is "interested" in
        """
        return self.extensions

    def config(self) -> StratConfig:
        """
        Return strategy's configuration object
        """
        return self._config
    
    def update_config(self, new_config:StratConfig) -> None:
        """
        Update strategy config
        """
        self._config = new_config

    def state(self) -> StrategyState:
        """
        Return strategy's formalization state
        """
        return self._state

    def add_event (self, event : StrategyEvent|ServerEvent|None) -> None:
        """ 
        Add event to the queue for processing (None will force shutdown)
        """

        # This is blocking, but it shouldn't take any time
        self._queue.put(event)

        log.info(f"Event added: {type(event).__name__}")

    def process_event(self, event) -> None:
        """ 
        process_event - dispatches event-specific handling methods
        """

        if isinstance (event, FileSystemEvent):
            # we process filesystem event in this case, we need to do something special
            log.info(f"About to process file system update event")
            self.proc_filesystem_update(event)

        elif isinstance (event, FileSystemCheckbackEvent):
            log.info(f"About to process file system checkback event")
            # We process file system checkback events
            self.proc_filesystem_checkback(event)

        elif isinstance (event, ChangeMode):
            log.info (f"About to process mode change to: {str(event)}")
            self.proc_mode_change(event.new_mode)

        elif isinstance (event, CLResultEvent):
            log.info("About to process CL Result event")
            self.proc_cl_result(event)
    
        elif isinstance(event, RunOneshotEvent):
            log.info ("About to process RunOneshotEvent")
            self.proc_oneshot_event(event)
    
        elif isinstance(event, ModelCLTaskEvent):
            log.info(f"About to process ModelCLTaskEvent")
            self.proc_model_cl_task_event(event)
    
        elif isinstance(event, AutoModeCLTaskEvent):
            log.info(f"About to process AutoModelCLTaskEvent")
            self.proc_auto_mode_cl_task_event(event)
        
        else:
            log.error (f"Gotten an unknown event type: {type(event).__name__}")
  
    def proc_sketch_change_event(self, event : SketchChangeEvent) -> None:
        """
        We have an incoming SketchChange event
        """
    
        self._codeLogicianWorker.add_task(
            SketchChangeTask(change=event.change, iml_code="")
        )

    def proc_sketch_change_result (self, event : SketchChangeResultEvent) -> None:
        """
        We have received result of running ImandraX on the change to a sketch
        """

        log.info(f"Received ImandraX result for sketch={event.sketch_id}")
        sketch = self.state().sketches.from_id(event.sketch_id)

        if sketch:
            sketch.apply_change_result(event.change_result)
            log.info(f"Successfully applied it now.")
        else:
            log.error(f"Unknown sketch with id={event.sketch_id}")

    def proc_auto_mode_cl_task_event(self, event : AutoModeCLTaskEvent) -> None:
        """
        """
    
        self._codeLogicianWorker.add_task(event.task)

        log.info (f"Adding new task")

        self.state().add_task(event.task)

    def proc_model_cl_task_event(self, event : ModelCLTaskEvent) -> None:
        """
        Process ModelCLTaskEvent
        """

        if not self.state().curr_meta_model or not(event.rel_path in self.state().curr_meta_model.models):
            log.error(f"Something's wrong - either the MetaModel doesn't exist or the model is missing [{event.rel_path}]")
            return

        oldGraphState = None
        model = self.state().curr_meta_model.models[event.rel_path]
        if model.agent_state:
            oldGraphState = model.agent_state.graph_state

        clTask = ModelTask (
            rel_path = event.rel_path,
            specified_commands=[event.cmd],
            graph_state = oldGraphState
        )

        log.info (f"Adding new task")
        self.state().add_task(clTask)

    def proc_oneshot_event(self, event : RunOneshotEvent) -> None:
        """
        Process running oneshot event
        """
    
        self._oneshot = True
        self._config.mode = StratMode.AUTO

        log.info(f"We're now in AUTO mode - will check what we shouild do with autoformalization...")
        self.check_autoformalization_tasks()

    def proc_mode_change (self, newMode : StratMode) -> None:
        """
        Process mode change
        """

        if not isinstance (newMode, StratMode):
            log.error (f"Error: getting a non-StratMode value: {str(newMode)}")
            return

        self._config.mode = newMode
        log.info(f"Setting strategy mode to {newMode}")

        if newMode == StratMode.AUTO:
            log.info("Since we're in AUTO mode now, will check formalization tasks")
            self.check_autoformalization_tasks()

    def check_autoformalization_tasks (self) -> None:
        """
        When in automode, we will check our meta model if there're any 
        formalization tasks that need to be done
        """

        log.info("Checking autoformalization tasks!")

        tasks = self.state().get_next_tasks()
        if len(tasks):
            log.info (f"Adding {len(tasks)} new tasks")
            # Once the tasks are done, the results will be inserted back into the Queue
            # for this strategy thread to process
            for task in tasks:
                self.add_event(AutoModeCLTaskEvent(task=task))
        else:
            log.info("No new formalization tasks present!")
      
            # Now let's check if we're in the oneshot mode, then we should quit
            # if there're no outstanding CL tasks (we store them in the state variable)
            if self._oneshot and self.state().tasks == []:
                log.info ("There are no tasks now. Quitting!")
                self.add_event(None)

    def check_back_callback (self, abs_path : str) -> None:
        """
        This is the callback function that's called
        """
        log.info(f"Adding FileSystemCheckbackEvent for {abs_path}")

        self.add_event(FileSystemCheckbackEvent(abs_path=abs_path))

    def proc_filesystem_update(self, event : FileSystemEvent) -> None:
        """
        Process event when there're changes to the file system (files in the directory
        that we're monitoring). This will update the statuses of the individual models
        in the MetaModel.

        We're now also handling changes to the corresponding IML models. So, if the
        user makes changes to the resulting IML model, then we need to override it.

        """

        if self.state().curr_meta_model is None:
            return

        self.state().curr_meta_model.process_filesystem_event(event)

        if self._config.mode == StratMode.AUTO:
            log.info("Since we're in AUTO mode, we will schedule a Timer thread to check back" \
            " on the file and see if it's stable enough to formalize the changes.")

            # Let's now schedule a checkback event
            timer = Timer(
                interval=self._config.time_for_filesync_checkback
                , function=self.check_back_callback
                , args=(event.abs_path1,)
            )

            # Now let's start this thing
            timer.start()
        else:
            log.info("No checkback thread started as we're in STANDBY mode")

    def proc_filesystem_checkback(self, event : FileSystemCheckbackEvent) -> None:
        """
        Process fileSystemCheckback event - we need to go and check 
        if there're any formalization tasks we should be doing.
        """

        log.info("Processing fileSystemCheckback event")

        if not self.state().curr_meta_model: return

        ext = Path(event.abs_path).suffix

        if ext == '.py':
            if not self.state().curr_meta_model.abs_path_in_models(event.abs_path):
                log.info(f"Model for path: {event.abs_path} not found. Aborting.")
                return
        
        elif ext == '.iml':
            model_path = str(Path(event.abs_path).with_suffix('.py'))
            if not self.state().curr_meta_model.abs_path_in_models(model_path):
                log.info(f"IML code for model with path: {model_path} not found. Aborting.")
                return
            
        else:
            return

        if self._config.mode == StratMode.AUTO:
            log.info("Checking autoformalization tasks")
            self.check_autoformalization_tasks()

    def write_model_code (self, rel_path:str) -> None:
        """
        Write out IML code to disk
        """

        if not self.state().curr_meta_model:
            log.error(f"Somehow we're processing a CLResult event but we have no current MetaModel!")
            return

        # Let's write these out to a specific directory
        models = self.state().curr_meta_model.models
        if rel_path not in models:
            log.info(f"Somehow the result is for a non-existent model")
            return
        
        # Let's get the model for this event
        model = models[rel_path]

        # If we have IML code for this model, let's print it out (if we're supposed to in the config)
        if not model.iml_code():
            return
        
        # Let's check how we want to write out the model
        if self._config.write_models_in_same_dir:
            # We need to write out the IML file into the same directory            

            #file_dir = Path(rel_path).parent
            file_name = Path(rel_path).with_suffix('.iml')

            tgt_path = os.path.join(self.state().src_dir_abs_path, file_name)

            try:
                with open(tgt_path, 'w') as outfile:
                    print (model.iml_code(), file=outfile)
            except Exception as e:
                log.error(f"Failed to write out IML file: [{tgt_path}]: {e}")
        
        else:
            # Let's make sure we have the artifact directory, or we can create it
            artifactDirPath = os.path.join(self.state().src_dir_abs_path, self._config.artifact_dir)
            if not os.path.isdir(artifactDirPath):
                log.warning(f"Artifact directory {artifactDirPath} doesn't exist. Trying to create it.")
                try:
                    os.mkdir(artifactDirPath)
                except Exception as e:
                    log.error(f"Failed to create artifact directory [{artifactDirPath}]: error: {str(e)}. Aborting.")
                    return

            # Figure out the target directory
            imlDirPath = os.path.join(artifactDirPath, self._config.iml_dir)
            if not os.path.isdir(imlDirPath):
                log.warning(f"IML model directory {imlDirPath} doesn't exist. Trying to create it.")
                try:
                    os.mkdir(imlDirPath)
                except Exception as e:
                    log.error(f"Failed to create IML artifact directory {imlDirPath}: error: {str(e)}. Aborting.")
                    return

                filename = os.path.basename(model.rel_path).replace('.py', '.iml')
                imlFullpath = os.path.join(imlDirPath, filename)

                try:
                    with open(imlFullpath, 'w') as outfile:
                        print (model.iml_code(), file=outfile)
                except Exception as e:
                    log.error(f"Failed to write IML file: [{imlFullpath}]: {str(e)}")


    def proc_cl_result(self, event : CLResultEvent) -> None:
        """
        Process the CL result
        """

        log.info(f"Applying CL Result to the model: {event}")

        # This will apply the result to the metamodel/model
        self.state().apply_cl_result(event.result)

        # This will remove the task from the list of tasks in the state
        self.state().remove_task(event.result.task)

        if self._config.write_consolidated:
            log.warning(f"Writing out a consolidated model is not supporetd yet!")

        # If we're processing the result of us analyzing the user-edited IML model, 
        # let's not write it back to them
        is_not_user_iml_edit = not isinstance(event.result.task, UserManualIMLEditTask)

        # If the configuration is set to write out IML files, let's do this here
        if self._config.write_models and is_not_user_iml_edit:
            self.write_model_code(event.result.task.rel_path)

        # Let's now check if there're autoformalization tasks that need to be processed
        if self._config.mode == StratMode.AUTO:
            self.check_autoformalization_tasks()

    def run(self):
        """
        Execute strategy events.
        """

        if self._oneshot:
            self.run_oneshot()
            return

        while True:
            try:
                event = self._queue.get()  # Blocks until an item is available

                if event is None:
                    log.info("Received a 'None' event to process. Shutting down.")
                    self._codeLogicianWorker.add_task(None)
                    # this will also shut down the CL worker
                    break # we should get out

                # this should handle the various bits and pieces for us...
                self.process_event(event)

                # we've fired off the request, so now it should be good to go...
                self._queue.task_done()

            except Empty:
                # This block won't be reached if get() is called without a timeout
                pass

            except Exception as e:
                log.error (f"Caught exception during event processing: {str(e)}")

    def run_oneshot(self):
        """ 
        Execute strategy events in a oneshot way. Shows progress bars.
        """

        progressTasks = {}

        with Progress() as progress:

            for path in self.state().curr_meta_model.models:
                progressTasks[path] = progress.add_task(f"[green] Formalizing {path}", total = 1000)

            while True:
                try:
                    event = self._queue.get()  # Blocks until an item is available

                    if event is None:
                        log.info("Received a 'None' event to process. Shutting down.")
                        self._codeLogicianWorker.add_task(None) # This will also shut down the CL worker
                        break

                    if isinstance(event, AutoModeCLTaskEvent):
                        progress.update(progressTasks[event.task.rel_path], completed=250)
                    elif isinstance(event, CLResultEvent):
                        progress.update(progressTasks[event.result.task.rel_path], completed=1000)

                    # This should handle the various bits and pieces for us...
                    self.process_event(event)

                    # We've fired off the request, so now it should be good to go...
                    self._queue.task_done()

                except Empty:
                    # This block won't be reached if get() is called without a timeout
                    pass

                except Exception as e:
                    log.error (f"Caught exception during event processing: {str(e)}")
