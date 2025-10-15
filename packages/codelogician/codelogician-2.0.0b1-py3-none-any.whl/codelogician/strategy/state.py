#
#   Imandra Inc.
#
#   state.py
#

import os, json, copy, logging, unittest, uuid
from pathlib import Path
from rich import print as rprint
from rich.panel import Panel
from rich.pretty import Pretty

from .sketch import SketchContainer, Sketch
from .metamodel import MetaModel
from .model_task import ModelTask
from .metacache import MetaCache
from .worker import CLResult

from pydantic import BaseModel, Field, AfterValidator
from typing import Annotated, Optional, Dict, Any
from pathlib import Path

log = logging.getLogger(__name__)

class StrategyState(BaseModel):
    """ 
    Contains the metamodel, sketches and various additional strategy-specific settings
    """

    # Source directory - it must be absolute path!
    src_dir_abs_path : Annotated[str, AfterValidator(lambda x: str(Path(x).resolve()))]

    language : str = "Python"

    # List of sketches (we should also change to the be a container)
    sketches : SketchContainer = SketchContainer()

    # List of outstanding CL agent tasks
    tasks : list[ModelTask] = []

    # Container with a list of metamodel states along with events
    meta_cache : MetaCache = MetaCache()

    # We'll use this unique ID to keep the strategies
    strat_id : str = Field(default_factory=lambda: str(uuid.uuid4())[:8])

#    def meta_model_validator (data: Optional[Dict[str, Any]]):
#        if data["meta_cache"].latest():
#            return data["meta_cache"].latest() 
#        else:
#            return MetaModel(src_dir_abs_path=data["src_dir_abs_path"], models={})

    # Current MetaModel
    curr_meta_model : MetaModel = Field (
        default_factory = 
            lambda data: data["meta_cache"].latest_mmodel() if data["meta_cache"].latest_mmodel()
            else MetaModel(src_dir_abs_path=data["src_dir_abs_path"], models={})
    )

    def sketch_ids(self):
        """
        Return list of all sketch IDs
        """

        return self.sketches.ids()

    def list_sketches(self):
        """
        Return list of sketch summary information
        """
        return self.sketches.list_sketches()
    
    def create_new_sketch(self, anchor_model_path:str):
        """
        """
        if anchor_model_path not in self.curr_meta_model.models:
            raise Exception (f"Could not find specified anchro model path: {anchor_model_path}")
        
        iml_model, base_models = self.curr_meta_model.gen_consolidated_model(anchor_model_path)

        new_sketch = Sketch(
            anchor_model_path=anchor_model_path,
            init_iml_model=iml_model,
            base_models=base_models
        )

        self.sketches.add(new_sketch)

        return new_sketch.sketch_id


    def run_file_sync(self):
        """
        Perform analysis of file system synchronization. The models's `src_code`
        are then adapted to the many things that are different.
        """

        try:
            self.curr_meta_model.run_file_sync()
        except Exception as e:
            log.error (f"Failed to perform file system synchronization: {str(e)}")
            return

    def apply_cl_result (self, cl_result : CLResult):
        """
        Apply result from running CodeLogician on a model
        """
        
        if self.curr_meta_model:
            self.curr_meta_model.apply_cl_result(cl_result)

    def cacheIndices(self):
        """
        Return cache indicies that are available
        """
        return self.meta_cache.indices()

    def get_next_tasks(self):
        """
        Return MetaModel's current tasks
        """
        
        if self.curr_meta_model is None: return []
        
        return self.curr_meta_model.get_next_tasks()

    def saveMetaToCache (self, event, metaModel = None):
        """
        Save the MetaModel to cache...
        """

        if metaModel is None:
            self.meta_cache.save_meta_model(event, self.curr_meta_model)
        else:
            self.meta_cache.save_meta_model(event, metaModel)

    def update_metamodel (self, event, new_metamodel):
        """
        Update the current MetaModel and save a snapshot to cache
        """

        self.meta_cache.save_meta_model(event, new_metamodel)
        self.curr_meta_model = new_metamodel

    def add_task(self, task:ModelTask):
        """
        Add CL task that's being worked on
        """
    
        self.tasks.append(task)

    def remove_task(self, task:ModelTask):
        """
        Remove CL task from the task list after it's been done
        """
        self.tasks.remove(task)

    def summary(self):
        """
        Return summary JSON of the state
        """

        currMetaModelSummary = copy.copy(self.curr_meta_model.summary())
        numModelsInCache = len(self.meta_cache.indices())

        return {
            'src_dir' : self.src_dir_abs_path,
            'num_tasks' : len(self.tasks),
            'current_tasks' : list(map(lambda x: x.toJSON(), self.tasks)),
            'num_models_in_cache' : numModelsInCache,
            'curr_meta_model' : currMetaModelSummary
        }

    @staticmethod
    def from_file(cache_file_path : str):
        """
        Load in cache from specific filepath
        """
    
        if Path(cache_file_path).is_absolute():
            abs_path = str(cache_file_path)
        else:
            abs_path = str(Path(cache_file_path).resolve())

        d = {}
        if os.path.exists(abs_path):
            try:
                with open(cache_file_path) as infile:
                    d = json.load(infile)
            except Exception as e:
                log.error(str(e))
                raise Exception (f"Failed to read in cache from [{cache_file_path}]: {str(e)}")
        
        else:
            raise Exception(f"Path [{cache_file_path}] does not exist!")
        
        try:
            state = StrategyState.fromJSON(d)
        except Exception as e:
            raise Exception (f"Got an error during validation: {str(e)}: path={cache_file_path}; {str(d)}")

        return state

    @staticmethod
    def from_directory(dir_path : str):
        """
        Load in the cache from a specified directory
        """

        cacheFilePath = os.path.join(dir_path, '.cl_cache')
        
        if os.path.exists(cacheFilePath):
            log.info(f"Creating strategy state from existing path")
            return StrategyState.from_file(cacheFilePath)
        else:
            log.info(f"Specified path for strategy cache does not exist, so creating a default one")
            return StrategyState(
                src_dir_abs_path=dir_path
                                 )

    def toJSON(self):
        """
        Return a nice JSON representation
        """
        return self.model_dump_json(indent=2)

    def save(self):
        """ 
        Save this state to disk
        """
        
        path = None
        try:
            path = os.path.join(self.src_dir_abs_path, '.cl_cache')
            with open(path, 'w') as outfile:
                print(self.toJSON(), file=outfile)
        except Exception as e:
            log.error(f"Failed to save Strategy state to: {path}; error={e}")

    @staticmethod
    def fromJSON(j : str|dict):
        """
        Return PyIMLStrategy state object from a JSON
        """

        if isinstance(j, str):
            return StrategyState.model_validate_json(j)
        elif isinstance(j, dict):
            return StrategyState.model_validate(j)
        else:
            raise Exception (f"Input must be either a str or a dict!")

    def __repr__(self):
        """
        Should have a Rich representation also...
        """
        return f"StrategyState: \n {str(self.curr_meta_model)} "

    def __rich__(self):
        """
        Return Rich representation of the strategy state
        """

        pretty = Pretty(self.summary(), indent_size=2)
        return Panel(pretty, title="PyIML Strategy State", border_style="green")
