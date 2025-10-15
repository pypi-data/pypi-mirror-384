#
#   Imandra Inc.
#
#   cl_agent_state.py
#

from pydantic import BaseModel, Field
from typing import Optional, Dict
from imandra.u.agents.code_logician.base import FormalizationStatus
from imandra.u.agents.code_logician.graph import GraphState
from imandra.u.agents.code_logician.base import VG, RegionDecomp, TopLevelDefinition

from .model_task import ModelTask

from enum import StrEnum

class Embedding(BaseModel):
    """
    Contains data on the embeddings we calculate to search the files
    """
    source : str # Either IML or SRC
    vector : list[float] # actual value
    start_line : Optional[int] = None # Location of the file where it was taken
    start_col : Optional[int] = None 
    end_line : Optional[int] = None
    end_col : Optional[int] = None


class CLAgentState(BaseModel):
    """ 
    Wrapper around the CL agent state - this is what we get back from CL.
    """
    status : FormalizationStatus = FormalizationStatus.UNKNOWN
    src_code : str = ""
    iml_code : Optional[str] = None # IML code with artifacts (e.g. VGs)
    iml_model : Optional[str] = None # IML code without artifacts
    vgs: list[VG] = []
    region_decomps: list[RegionDecomp] = []
    opaque_funcs : list[TopLevelDefinition] = []
    context : str = ""
    src_code_embeddings : list[Embedding] = []
    iml_code_embeddings : list[Embedding] = []

    # These things are massive, so we don't save them to disk
    graph_state : Optional[GraphState] = Field(default=None, exclude=True) 

    def toJSON(self):
        """
        Return a dictionary we can save to disk
        """
        return self.model_dump_json()

    @staticmethod
    def fromJSON(j:str|dict):
        """ 
        Create a CLAgentState value from JSON 
        """
        if isinstance(j, str):
            return CLAgentState.model_validate_json(j)
        else:
            return CLAgentState.model_validate(j)

    def __repr__(self):
        """
        Return a nice set here 
        """

        iml_code = str(self.iml_code) if self.iml_code else "N\\A"
        iml_model = str(self.iml_model) if self.iml_model else "N\\A"

        s = "Agent state:\n"
        s += f"Status: {self.status}\n"
        s += f"Src Code: \n{self.src_code[:100]}\n"
        s += f"IML Code: \n{iml_code[:100]}\n"
        s += f"IML Model: \n{iml_model[:100]}\n"
        s += f"Context: \n{self.context}\n"
        s += f"Opaque funcs: \n{self.opaque_funcs}\n"
        s += f"Decomps: \n{self.region_decomps}\n"
        s += f"VGs: \n{self.vgs}\n"
        return s


class CLResultStatus(StrEnum):
    """ 
    CLResultStatus
    """
    SUCCESS = 'Success'
    ERROR = 'Error'
    TIMEOUT = 'Timeout'

class CLResult(BaseModel):
    """
    CLResult 
    """  
    task : ModelTask
    status : CLResultStatus
    agent_state : CLAgentState

    def __repr__(self):
        """ Nice representation """
        return f"CodeLogician result: [status={self.status.name}; taskID={self.task.task_id}]"