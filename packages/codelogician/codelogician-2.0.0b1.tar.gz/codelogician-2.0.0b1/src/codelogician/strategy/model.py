#
#   Imandra Inc.
#
#   model.py
#

from imandra.u.agents.code_logician.base import (
    FormalizationDependency,
    FormalizationStatus,
    ModuleInfo
)

from typing import Optional, Dict
from pathlib import Path
import datetime, logging

from rich.text import Text
from rich.pretty import Pretty
from rich.panel import Panel
from rich import print as rprint

from pydantic import BaseModel, field_serializer
import numpy as np

log = logging.getLogger(__name__)

from .model_status import ModelStatus, SrcCodeStatus
from .model_task import (
    ModelTask, UserManualIMLEditTask, FormalizationNeed
)
from .cl_agent_state import CLAgentState, Embedding
from ..tools.cl_caller import clAutoformalize


class Model(BaseModel):
    """
        Container for a model - representing a single model along with its dependendencies, 
        formalization state, etc...
        
        These are the primary actions for a model:
        - 1. Update the source code
        - 2. Reset the source code to the formalization state -

        Context - Human-provided information to CodeLogician for this model. If it's set, then
        `NeedsFormalization` function will return True:

        AgentState contains the latest results of running CodeLogician on this model
        - 5. Apply agentState - this sets the agent state (formalization state)

        Three ways that a status is accessed:
        - needsFormalization(timeToWaitSinceSrcCodeChange : int) -> bool -- returns True if the model
        requires updated formalization
        -- hasSrcCodeChanged(timeToWaitSinceSrcCodeChange : int) -> bool
        -- depsChanged() -> bool - models in the dependencies list have changed
        -- instructionsPresent() -> bool: human instructions have been provided

        This function is used during autoformalization to determine that the order
        of model formalization (if there're "blocking" dependencies, then we will not)
        - deps_need_formalization() -> bool - if this is True, then metamodel will not

        Then there are other functions like:
        - 1. Accessing/modifying lists of dependencies (other models that this model depends on)
        - 2. Saving to / loading from JSON files
        - 3. Generating ModelTask (object with instructions to CodeLogician)
    """

    rel_path : str
    src_code : Optional[str] = None
    src_code_last_changed : Optional[datetime.datetime] = None
    src_language : str = "Python"
    agent_state : Optional[CLAgentState] = None

    # Here we account for user's changes to the model IML code 
    # and keep track of how long it's been since they edited it
    # if it's been long enough and it's different that what we have
    # then we'll kick off a command to make it part of the Graph State
    user_iml_code : Optional[str] = None # This is human provided IML code
    user_iml_code_last_changed : Optional[datetime.datetime] = None

    src_code_embeddings : list[Embedding] = [] # Embeddings for the original source code
    iml_code_embeddings : list[Embedding] = [] # IML code embeddings

    # This is human-provided context that is sent to the CL agent
    context : Optional[str] = None

    # This is used to keep track of the latest TaskID that was generated
    # We can only apply changes to the CL agent state if the taskID of the
    # result andf what we're waiting for matches - otherwise we discard the results
    outstanding_task_ID : Optional[str] = None

    # This will be typically inserted after creation of the object because
    # this requires actual object references (to other models)
    dependencies : list = [] # list of models that this model depends on
    rev_dependencies : list = [] # list of models that this model affects (the inverse of dependencies)

    @field_serializer('dependencies','rev_dependencies')
    def serialize_tags(self, deps: list) -> list:
        return list (map (lambda x: x.rel_path, deps))

    # This gets updated along with each agent state - here we maintain
    # IML code for the dependencies that were used. If they differ
    # then we may need to re-run CodeLogician.
    formalized_deps : list[FormalizationDependency] = []

    # We do the same with the human-provided context
    formalized_context : Optional[str] = None

    def add_dependency(self, d) -> None:
        """
        "Safe" add of a dependency - if it's already there, it would not add it twice
        """
        if d in self.dependencies: return
        self.dependencies.append(d)

    def status(self) -> ModelStatus:
        """ 
        Return a status object that contains various bits of the current state of the model
        """

        return ModelStatus(
            src_code_status=self.src_code_status(),
            instructions_added=self.context_provided(),
            deps_changed=self.deps_changed(),
            deps_need_formalization=self.deps_need_formalization(),
            formalization_status=self.formalization_status()
        )

    @staticmethod
    def calc_distance (vec1, vec2):
        """
        Calculate cosine distance between two vectors
        """

        dot_product = np.dot(vec1, vec2)

        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)

        if norm_vec1 == 0 or norm_vec2 == 0:
            return 1.0  # Handle cases where one or both vectors are zero vectors
        
        cosine_similarity = dot_product / (norm_vec1 * norm_vec2)
        cosine_distance = 1 - cosine_similarity
        return cosine_distance

    def calc_embedding_distance (self, query_vector : list[float]) -> float | None:
        """
        Calculate distance between the specified query vector and its own embeddings. Return the most minimal one.
        """

        qv = np.array(query_vector)

        min_distance = None
        for embedding in (self.iml_code_embeddings + self.src_code_embeddings):            
            curr_vec = np.array(embedding.vector)

            try:
                distance = self.calc_distance(qv, curr_vec)
            except Exception as e: raise Exception(f"Failed to calculate distance: {e}")

            if min_distance is None:
                min_distance = distance
            else:
                if distance < min_distance:
                    min_distance = distance
        
        if min_distance is None:
            return None
        return float(min_distance)

    def needs_embedding_update(self) -> bool:
        """
        Does this model need to update embedding info?
        """
        # TODO check to see if the source code/etc changed since last embedding...
        return False

    def gen_embedding_task (self) -> ModelTask:
        """
        Create an embedding task - TODO: we should streamline this 
        """
        task = ModelTask(
            rel_path=self.rel_path,
            src_code=self.src_code if self.src_code else "",
            context=self.context,
            gen_embeddings=True
        )

        # Let's now save this task so we know that we should expect 
        # the result 
        self.outstanding_task_ID = task.task_id

        return task

    def gen_formalization_task(self) -> ModelTask:
        """
        Generate a formalization taks (ModelTask) object if we need to
        """

        task = ModelTask(
            rel_path=self.rel_path,
            src_code=self.src_code if self.src_code else "",
            context=self.context,
            graph_state=self.agent_state.graph_state if self.agent_state else None,
            dependencies=self.depdendencies_iml_models()
        )

        self.outstanding_task_ID = task.task_id

        return task
    
    def gen_iml_user_update_task (self) -> ModelTask:
        """
        Generate a model task for updating the IML code within the
        """

        if self.user_iml_code is None:
            return None

        task = UserManualIMLEditTask(
            rel_path=self.rel_path,
            graph_state = self.agent_state.graph_state if self.agent_state else None,
            iml_code=self.user_iml_code
        )

        self.outstanding_task_ID = task.task_id

        return task

    def context_provided(self) -> bool:
        """ 
        Return True if there's human-provided context 
        """
        return bool(self.context)
  
    def apply_agent_state (self,
        agentState : CLAgentState,
        dependencies : list[FormalizationDependency] = []) -> None:
        """
        Apply the agent state
        """

        # Let's make sure we have an actual CLAgentState
        if not isinstance(agentState, CLAgentState):
            raise Exception (f"Expected a value of CLAgentState, but got something else: {str(agentState)}!")

        # Agent state
        self.agent_state = agentState

        # Remove instructions that were used from the current list of outstanding ones
        self.formalized_context = agentState.context

        # Let's now set the dependencies' models that were used
        self.formalized_deps = dependencies

        self.src_code_embeddings = agentState.src_code_embeddings
        self.iml_code_embeddings = agentState.iml_code_embeddings

    def user_iml_change_ready(self, user_wait_time:int) -> bool:
        """
        Has enough time passed since user modified the IML model?
        """

        if self.user_iml_code is None:
            return False

        # if we're missing formalization altogether, then source code has changed
        if self.agent_state is None:
            return True

        if user_wait_time is None or self.src_code_last_changed is None:
            timeLongEnough = True
        else:
            timeLongEnough = (datetime.datetime.now() - self.src_code_last_changed) > datetime.timedelta(seconds=user_wait_time)

        return timeLongEnough and (hash(self.user_iml_code) != hash(self.agent_state.iml_code))

    def formalization_reasons(self, user_wait_time:Optional[int]=None) -> list[FormalizationNeed]:
        """
        Returns a list of reasons for the need to perform formalization on this model.
        If the list is empty - then there's no need to do it.
        """

        if self.src_code is None: return [] # if we have no source code (i.e. file was deleted), then there's nothing to do    
        if self.agent_state is None: return [FormalizationNeed.NO_AGENT_STATE]

        reasons = []
        if self.has_src_code_changed(user_wait_time): reasons.append(FormalizationNeed.SRC_CODE_CHANGED)
        if self.context_provided(): reasons.append(FormalizationNeed.CONTEXT_ADDED)
        if self.deps_changed(): reasons.append(FormalizationNeed.DEPS_CHANGED)

        return reasons

    def deps_need_formalization(self, srcWaitTime:int=0):
        """ 
        Return True if there're dependencies (may be indirect) that are due for formalization and
        False otherwise. We use this function when constructing the list of Tasks for the metamodel. 
        """

        for d in self.dependencies:
            if d.formalization_reasons(srcWaitTime) or d.deps_need_formalization(srcWaitTime):
                return True

        return False

    def depdendencies_iml_models(self) -> list[FormalizationDependency]:
        """
        Return IML code of the dependencies
        """

        ds = []
        for model in self.dependencies:
            # We only care about the models that have IML code available
            if model.iml_code() is None: continue

            src_mod_info = model.to_CL_src_module_info()
            iml_mod_info = model.to_CL_iml_module_info()

            ds.append(
                FormalizationDependency(
                src_module=src_mod_info,
                iml_module=iml_mod_info,
                )
            )

        return ds

    def to_CL_src_module_info(self) -> ModuleInfo:
        """
        Create ModuleInfo
        """

        return ModuleInfo(
            name = self.rel_path,
            relative_path=Path(self.rel_path),
            content = self.src_code if self.src_code else "",
            src_lang = self.src_language
        )

    def to_CL_iml_module_info(self) -> ModuleInfo | None:
        """
        Return ModuleInfo object for the IML code if it's available, None otherwise
        """

        # If we don't have any IML code for this model, let's not return it
        if self.iml_code() is None:
            return None
        
        if self.iml_code() is not None:
            iml_code = str(self.iml_code())
        else:
            iml_code = ""

        return ModuleInfo (
            name = self.rel_path,
            relative_path = Path(self.rel_path),
            content = iml_code,
            src_lang="IML"
        )

    def src_code_status(self, srcCodeWaitTime:Optional[int]=None) -> SrcCodeStatus:
        """
        Return source code status
        """

        if self.src_code is None:
            return SrcCodeStatus.SRC_CODE_DELETED

        else:
            if srcCodeWaitTime is None or self.src_code_last_changed is None:
                timeLongEnough = True
            else:
                timeLongEnough = (datetime.datetime.now() - self.src_code_last_changed) > datetime.timedelta(seconds=srcCodeWaitTime)

        if timeLongEnough and (hash(self.src_code) == hash(self.iml_code())):
            return SrcCodeStatus.SRC_CODE_CHANGED
        else:
            return SrcCodeStatus.SRC_CODE_CURRENT

    def formalization_status(self) -> FormalizationStatus:
        """
        Return formalization status of the model
        """
        if self.agent_state is None:
            return FormalizationStatus.UNKNOWN
        else:
            return self.agent_state.status

    def has_src_code_changed(self, srcCodeWaitTime:Optional[int]=None) -> bool:
        """
        Return True if source code has changed from when it was formalized
        """

        # if we're missing formalization altogether, then source code has changed
        if self.agent_state is None:
            return True

        if srcCodeWaitTime is None or self.src_code_last_changed is None:
            timeLongEnough = True
        else:
            timeLongEnough = (datetime.datetime.now() - self.src_code_last_changed) > datetime.timedelta(seconds=srcCodeWaitTime)

        return timeLongEnough and (hash(self.src_code) != hash(self.agent_state.src_code))

    def deps_changed(self) -> bool:
        """    
        Return True if dependencies' models (IML code) have changed since we
        ran CL formalization task last time. When we receive CL results, we always
        record dependencies' IML models that were used. 
        """

        currentDeps = self.depdendencies_iml_models()

        if len(self.formalized_deps) != len(currentDeps):
            return True

        for d in self.formalized_deps:
            if d not in currentDeps:
                return True

        return False

    def set_iml_model (self, new_iml_model : str, record_time:bool = False) -> None:
        """
        Set the IML model code and record the time if we need to. This is used
        for users when manually overriding the model.
        """

        if not isinstance(new_iml_model, str):
            raise Exception (f"Expected a string for 'new_iml_model', but got {type(new_iml_model).__name__ }")

        #if hash(new_iml_model) != hash(self.iml_code()):
        if hash(new_iml_model) != hash(self.user_iml_code):
            log.info(f"User is updating the IML model: [{self.rel_path}]")

            if record_time:
                self.user_iml_code_last_changed = datetime.datetime.now()
            else:
                self.user_iml_code_last_changed = None
            
            self.user_iml_code = new_iml_model
        else:
            log.warning(f"Model set by the user doesn't appear to be any different from existing model: [{self.rel_path}]")

    def set_src_code(self, new_src_code : str|None, record_time:bool = False) -> None:
        """
        Set the src_code and update the time source code changed
        """

        # This means the code was deleted
        if new_src_code is None:
            self.src_code = None
            self.src_code_last_changed = None
            return 

        if not isinstance(new_src_code, str):
            raise Exception (f"Expected a string value for `new_src_code`, but got {type(new_src_code).__name__}")

        if hash(new_src_code) != hash(self.src_code):
            log.info(f"Updating source code for model [{self.rel_path}]")
      
            if record_time:
                self.src_code_last_changed = datetime.datetime.now()
            else:
                self.src_code_last_changed = None

            self.src_code = new_src_code
        else:
            log.warning(f"Specified model hasn't changed: [{self.rel_path}]")


    def iml_code(self) -> str|None:
        """
        If available, returns IML code with artifacts (e.g. VGs and decomps)
        """
        return self.agent_state.iml_code if self.agent_state else None

    def iml_model(self) -> str|None:
        """
        If available, returns IML model (not artifacts like VGs, decomps) 
        """
        return self.agent_state.iml_model if self.agent_state else None

    def verification_goals(self) -> list:
        """
        If available, returns the list of dictionaries with verification goals
        """
        return self.agent_state.vgs if self.agent_state else []

    def failed_vgs(self) -> list:
        """
        Return just the list of failed VGs
        """
        return list(filter(lambda x: x['status'] == False, self.verification_goals()))

    def decomps(self) -> list:
        """
        If available, returns the list of decomposition requests
        """
        return self.agent_state.region_decomps if self.agent_state else []
    
    def opaque_funcs (self) -> list:
        """
        If available, return the opaque functions used along with their approximations
        """
        return self.agent_state.opaque_funcs if self.agent_state else []

    def gen_stats(self) -> Dict:
        """
        Generate some numberical stats for this model
        """

        s = {}
        s['frm_status'] = str(self.formalization_status())
        s['num_opaques'] = len(self.opaque_funcs())
        s['num_failed_vgs'] = len(self.failed_vgs())

        return s

    def toJSON(self) -> str:
        """
        Return a dictionary we can save to disk
        """
        return self.model_dump_json()

    @staticmethod
    def fromJSON(j : str|dict) -> 'Model':
        """
        Return a Model object from provided JSON. Note that we do not set the lists
        of models for 'dependsOn' here because we don't have access to the
        actual model objects. This is done outside this state methods.
        """

        if isinstance(j, str):
            return Model.model_validate_json(j)
        elif isinstance(j, dict):
            return Model.model_validate(j)
        else:
            raise Exception (f"Input must be either a str or a dict!")

    def str_summary(self) -> str:
        """
        Return a one-line string with high-level details
        """

        return f"[status={self.status()}]"

    def __hash__ (self):
        """
        We need this so we can compare models
        """
        return hash(str(self.toJSON()))

    def __repr__(self):
        """
        Return a nice representation
        """

        dependencyPaths = list(map(lambda x: x.rel_path, self.dependencies))
        agentStateStr = "None" if self.agent_state is None else self.agent_state.status

        s  = f"Model: {self.rel_path} \n"
        s += f"{str(self.status())}\n"
        s += f"Formalization state: {agentStateStr}\n"
        s += f"Depends on: {dependencyPaths}\n"
        s += f"Source language: {self.src_language}\n"

        if self.src_code:
            s += f"Source code (condensed): \n {self.src_code[:100]}\n"
        else:
            s += f"Source code (condensed): \n None \n"

        s += f"Opaque funcs: {len(self.opaque_funcs())}\n"
        s += f"Decomps: {len(self.decomps())}\n"
        return s

    def __rich__ (self):
        """ Return a Rich representation """

        pretty = Pretty(self.toJSON(), indent_size=2)
        return Panel(pretty, title="Model", border_style="green")
