#
#   Imandra Inc.
#
#   sketch.py
#    

import unittest, string, random, uuid
from pathlib import Path
from rich.text import Text
from rich.pretty import Pretty
from rich.panel import Panel
from rich import print as rprint

from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from .model import Model
from .sketch_task import (
    SketchChangeTask, SketchChangeResult,
    SketchChgSetModel, SketchChgInsertDef, 
    SketchChgModifyDef, SketchChgDeleteDef,
    SketchChange
)
from imandra.u.agents.code_logician.base.region_decomp import RegionDecomp
from imandra.u.agents.code_logician.base.vg import VG
from imandra.u.agents.code_logician.base import FormalizationStatus
#from imandra.u.agents.code_logician.base.imandrax import DecomposeRes, EvalRes, PO_Res
from ..tools.iml_utils import (
    add_definition, remove_definition, update_definition
)

class VGChange(BaseModel):
    """
    Helps us track VG changes over different states
    """
    is_new : bool # Is this a new VG that was just added?
    is_removed : bool # Has this VG been removed?
    res_changed : Optional[tuple[str,str]] = None # old vs new result type
    vg : VG # Actual VG info

class ChangeSummary(BaseModel):
    """
    Summary of the formalization state changes since the last state where we had an admissable model
    """

    vg_changes : list[VGChange]

    def stats(self) -> Dict[str, int]:
        """
        Return VG change statistics
        """

        def status_to_int (s:str) -> int:
            """
            """
            if s == 'unknown':
                return 1
            elif s == 'error' or s == 'err':
                return 2
            elif s == 'refuted':
                return 3
            elif s == 'verified_upto':
                return 4
            elif s == 'proved':
                return 5
            else:
                raise Exception (f"Unknown VG status: >{s}<")

        added, removed = 0, 0
        improved, deteriorated = 0, 0
        proved, refuted = 0, 0

        for vg_change in self.vg_changes:
            if vg_change.is_new:
                added += 1

            if vg_change.is_removed:
                removed += 1
                continue

            if vg_change.res_changed is None: continue

            if vg_change.res_changed[1] in ['proved', 'verified_upto']: proved += 1
            if vg_change.res_changed[1] in ['refuted']: refuted += 1

            if not vg_change.is_new:
                if status_to_int(vg_change.res_changed[0]) > status_to_int(vg_change.res_changed[1]):
                    deteriorated += 1
                elif status_to_int(vg_change.res_changed[0]) > status_to_int(vg_change.res_changed[1]):
                    improved += 1

        return {
            'added': added, 
            'removed': removed, 
            'improved': improved, 
            'deteriorated': deteriorated, 
            'proved': proved, 
            'refuted': refuted
        }

def calc_vg_difference(old_vgs : list[VG], new_vgs : list[VG]) -> list[VGChange]:
    """
    Compute difference between two lists of VGs
    """

    vg_diff : list[VGChange] = []

    def find_a_match(new_v:VG, other_vgs:list[VG]) -> VG | None:
        if new_v.data is None: return None
        return next(filter(lambda x: (x.data is not None) and (x.data.predicate == new_v.data.predicate), other_vgs), None) # pyright: ignore

    for new_vg in new_vgs:
        if new_vg.res is None: continue

        existing_vg = find_a_match(new_vg, old_vgs)

        if existing_vg is None:
            vg_diff.append (
                VGChange (
                    is_new=True, 
                    is_removed=False, 
                    res_changed=("", new_vg.res.res_type),
                    vg=new_vg
                )
            )
        else:
            # This is an existing VG, let's see if its result type has changed at all...
            if existing_vg.res is not None and new_vg.res.res_type != existing_vg.res.res_type:
                vg_diff.append (
                    VGChange (
                        is_new=False, 
                        is_removed=False, 
                        res_changed=(existing_vg.res.res_type, new_vg.res.res_type),
                        vg=new_vg
                    )
                )
            # ok, nothing changed
            else:
                vg_diff.append (
                    VGChange (
                        is_new=False, 
                        is_removed=False, 
                        res_changed=None,
                        vg=new_vg
                    )
                )
    
    for old_vg in old_vgs:
        if old_vg.res is None: continue
        
        if find_a_match(old_vg, new_vgs) is None:
            vg_diff.append(
                VGChange(
                    is_new=False, 
                    is_removed=True, 
                    res_changed=(old_vg.res.res_type, ""),
                    vg=old_vg
                )
            )

    return vg_diff

class SketchState(BaseModel):
    """
    SketchState contains the current version of 
    """
    state_id : int # State ID
    change : SketchChange # Change that caused this state
    iml_code : str # Actual IML code
    status : FormalizationStatus # Formalization status 
    error : Optional[str] = None # Error feedback from ImandraX
    
    vgs : list[VG] # List of current verification goals
    old_vgs : list[VG] # List of VGs in the last (good) state with admissable model
    decomps : list[RegionDecomp] = [] # Dictionary of decomposition requests/results

    vg_changes : list[VGChange] = Field (
        default_factory=lambda data:
            calc_vg_difference(data['vgs'], data['old_vgs']) if 'vgs' in data and 'old_vgs' in data else []
      )  # Changes in VGs
    
    # Summary of VG changes
    summary : ChangeSummary = Field (
        default_factory=lambda data:
            ChangeSummary(vg_changes=data['vg_changes'])
    )

class Sketch(BaseModel):
    """
    Sketch represent versions of a model
    """

    sketch_id : str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    processing : bool = False # TODO do we need this for the UI?
    anchor_model_path : str # relative path of the model that was used as the anchor 
    init_iml_model : str = "" # the initial model
    sketch_states : list[SketchState] = [] # here we keep track of changes in the state
    base_models : Dict[str, Model] # Dict (by relative path) of base models that went into this

    def get_state_by_idx(self, idx:int) -> SketchState:
        """
        Return SketchState for specific state ID
        """

        if not (0 <= idx and idx < len(self.sketch_states)):
            raise ValueError(f"Out of bounds state id: {idx}")
        
        return self.sketch_states[idx]

    def rollback(self, target_state_id:int|None=None):
        """
        rollback states 
        """

        if target_state_id is None:
            # We should just be able to 
            if len(self.sketch_states) in [0,1]:
                raise Exception (f"Not enough states[={len(self.sketch_states)}] to rollback!")
            self.sketch_states = self.sketch_states[1:]
        
        else:
            if not (0 <= target_state_id and target_state_id < len(self.sketch_states)):
                raise Exception (f"Invalid target state id[={target_state_id}] specified!")
            
            self.sketch_states = self.sketch_states[:(target_state_id+1)]


        
    def state_ids(self) -> list[int]:
        """
        Return list of SketchState IDs
        """
        if self.sketch_states:
            return list(range(len(self.sketch_states)))
        return []

    def latest_state(self) -> SketchState|None:
        """
        Return the latest sketch state if it's available
        """

        if len(self.sketch_states):
            return self.sketch_states[0]
        
        return None
    
    def last_good_state(self) -> SketchState|None:
        """
        Return last sketch state that has an admissable model
        """

        for i in range(len(self.sketch_states)-1, -1, -1):
            if self.sketch_states[i].status == FormalizationStatus.TRANSPARENT:
                return self.sketch_states[i]
        
        return None

    def gen_init_task(self) -> SketchChangeTask:
        """
        This is the task that needs to be run to populate the initial state
        """

        return SketchChangeTask (
            sketch_id = self.sketch_id,
            iml_code = self.init_iml_model,
            change = SketchChgSetModel(new_iml_code=self.init_iml_model)
        )

    def get_task (self, change: SketchChange) -> SketchChangeTask:
        """
        Return a SketchChangeTask that can be sent to the worker to be analyzed by ImandraX
        """
        
        # Writing it this way so it's easier for pyright to pick up
        state = self.latest_state()

        if state is None:
            raise Exception(f"Attempting to create a task but we have no initial state!")
                
        new_iml_model = self.process_change(state.iml_code, change)

        # Now we have a sketch change task!
        return SketchChangeTask(
            sketch_id=self.sketch_id,
            change = change,
            iml_code = new_iml_model
        )

    def apply_change_result (self, change_result : SketchChangeResult) -> ChangeSummary:
        """ 
        Apply the result of running change task to the state and get the ChangeSummary as the result
        """

        if len(self.sketch_states) == 0 or self.last_good_state() is None:
            state_id = 0
            old_vgs = []
            self.init_iml_model = change_result.task.iml_code
        else:
            state_id = len(self.sketch_states)+1
            old_vgs = self.last_good_state().vgs # pyright: ignore
            
        new_state = SketchState (
            state_id = state_id,
            change = change_result.task.change,
            iml_code = change_result.task.iml_code,

            status = FormalizationStatus.TRANSPARENT if change_result.success else FormalizationStatus.INADMISSIBLE,

            error = change_result.error,
            vgs = change_result.vgs,
            old_vgs= old_vgs,
            decomps = change_result.decomps
        )

        self.sketch_states.insert(0, new_state)

        return new_state.summary

    def get_model_changes(self) -> Dict[str, str]:
        """
        Generate changes to the underlying models
        """

        return {}

    def process_change(self, iml_code:str, change:SketchChange) -> str:
        """
        Process the change command for the specified code and return its updated version
        """

        if isinstance(change, SketchChgSetModel):
            updated_iml_code = change.new_iml_code

        elif isinstance(change, SketchChgInsertDef):
            try:
                updated_iml_code = add_definition(
                    source = iml_code, 
                    new_def = change.new_def_code
                )
            except Exception as e:
                raise Exception (f"Failed to insert: {e}")
        
        elif isinstance(change, SketchChgModifyDef):
            try:
                if isinstance (change.def_name_or_vg_idx, int):
                    updated_iml_code = update_definition(
                        source=iml_code, name="",
                        new_def=change.new_def_body,
                        verify_index=change.def_name_or_vg_idx
                    )
                else:
                    updated_iml_code = update_definition(
                        source=iml_code, 
                        name=change.def_name_or_vg_idx, 
                        new_def=change.new_def_body
                    )
            except Exception as e:
                raise Exception (f"Failed to update definition: {e}")

        elif isinstance (change, SketchChgDeleteDef):
            try:
                if isinstance(change.def_name_or_vg_idx, int):
                    updated_iml_code = remove_definition(
                        source=iml_code, name="", verify_index=change.def_name_or_vg_idx
                    )
                else:
                    updated_iml_code = remove_definition(
                        source=iml_code, name=change.def_name_or_vg_idx
                    )
            except Exception as e:
                raise Exception (f"Failed to delete definition: {e}")

        else:
            raise Exception (f"Unsupported change event: {change}")
        
        return updated_iml_code
  
    def __repr__(self):
        return f"Sketch [ID = {self.sketch_id}; Anchor model path = {self.anchor_model_path}]"

class SketchContainer(BaseModel):
    """
    Container for helping us keep track of the sketches
    """

    sketches : Dict[str, Sketch] = {}

    def add (self, new_sketch:Sketch) -> None:
        """
        Add spetch to the container
        """
        if new_sketch.sketch_id in self.sketches:
            raise ValueError(f"Sketch with specified ID is already present: {new_sketch.sketch_id}")

        self.sketches[new_sketch.sketch_id] = new_sketch

    def from_id(self, sketch_id) -> Sketch|None:
        """
        Return sketch from sketch ID, None if it's missing
        """

        if sketch_id in self.sketches:
            return self.sketches[sketch_id]
        return None

    def ids(self) -> list[str]:
        """ 
        List of available sketch IDs
        """
        return list(self.sketches.keys())

    def list_sketches(self) -> list[Dict[str,str]]:
        """ 
        List available sketches
        """
        
        res = []
        for sketch_id in self.sketches:
            res.append ({
                'sketch_id': sketch_id,
                'anchor_model': self.sketches[sketch_id].anchor_model_path
            })
        
        return res

    def toJSON(self):
        """
        Return JSON dict
        """
        return self.model_dump_json()

    @staticmethod
    def fromJSON(j : str|dict):
        """
        Create a SketchesContainer object from json dict
        """

        if isinstance (j, str):
            return SketchContainer.model_validate_json(j)
        else:
            return SketchContainer.model_validate(j)
  
    def __rich__ (self):
        """ Return the list of rich representations of the sketches we hold """

        pretty = Pretty(self.toJSON(), indent_guides=True)
        return Panel(pretty, title='SketchContainer', border_style="green")

