#
#   Imandra Inc.
#
#   sketch_task.py
#

from enum import StrEnum
from pydantic import BaseModel
from typing import Optional
from imandra.u.agents.code_logician.base.region_decomp import RegionDecomp
from imandra.u.agents.code_logician.base.vg import VG

class SketchChange(BaseModel):
    """
    Sketch change operation
    """
    pass

class SketchChgSetModel(SketchChange, BaseModel):
    """
    Sketch Change Set Model operation (for initializations and for overrides)
    """
    new_iml_code : str

class SketchChgInsertDef(SketchChange, BaseModel):
    """
    Sketch Change Insert Definition operation
    """
    new_def_code : str

class SketchChgModifyDef(SketchChange, BaseModel):
    """
    Sketch Change Modify Definition operation
    """
    def_name_or_vg_idx : str | int
    new_def_body : str

class SketchChgDeleteDef(SketchChange, BaseModel):
    """
    Sketch Change Deletion Definition operation
    """
    def_name_or_vg_idx : str | int

class SketchChangeTask(BaseModel):
    """
    Sketch Change Task
    """
    sketch_id : str
    iml_code : str
    change : SketchChange

class SketchChangeResult(BaseModel):
    """
    Result of running ImandraX on the updated IML code
    """

    task : SketchChangeTask
    success : bool
    error : Optional[str] = None
    vgs : list[VG]
    decomps : list[RegionDecomp]

    def toJSON(self):
        return self.model_dump_json()
