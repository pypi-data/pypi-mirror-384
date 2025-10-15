#
#   Imandra Inc.
#
#   model_task.py
#

from imandra.u.agents.code_logician.command import (
    InitStateCommand,
    InjectFormalizationContextCommand,
    EditStateElementCommand,
    GenFormalizationDataCommand,
    GenModelCommand,
    AgentFormalizerCommand,
    GenVgsCommand,
    GenRegionDecompsCommand,
    GenTestCasesCommand,
    EmbedCommand,
    SetModelCommand,
    Command
)

from imandra.u.agents.code_logician.base import FormalizationDependency
from imandra.u.agents.code_logician.graph import GraphState
import uuid, datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from enum import StrEnum

class ModelTaskMode(StrEnum):
    """
    Strategy mode
    """
    AGENT = 'Agent'
    MANUAL = 'Manual'

class FormalizationNeed(StrEnum):
    """
    Reasons to perform formalization
    """
    NO_AGENT_STATE = "No_agent_state" # This is the first time we're formalizing the model
    SRC_CODE_CHANGED = "Source_code_changed" # Source code has changed
    CONTEXT_ADDED = "Context_added" # Human feedback has been provided
    DEPS_CHANGED = "Dependencies_changed" # Dependencies (at least one) have changed

class ModelTask(BaseModel):
    """ 
    Model task contains a single task for Code Logician to execute
    """

    rel_path        : str # path of the source file (relative to the source code directory)
    src_code        : str = "" # source code
    context         : Optional[str] = "" # IML source code for dependent models
    dependencies    : list[FormalizationDependency] = [] # IML source code for dependent models
    graph_state     : Optional[GraphState] = None # previous graph state, if available
    language        : str = "Python" # programming language 
    mode            : ModelTaskMode = ModelTaskMode.AGENT # mode used with CodeLogician (either "simple" or "agent")
    gen_vgs         : bool = True # Should we generate verification goals?
    gen_decomps     : bool = True # Should we generate decompositions?
    gen_embeddings  : bool = True # Should we generate embeddings?

    # This is used to submit user-specified commands for specific models
    # if this is set, then we disregard everything else and just return these
    # along with the existing state
    specified_commands : Optional[list[Command]] = None

    # Each task has a unique ID that we'll then use to assign back the result
    # of CL work for this task - if the model's task ID doesn't match the result
    # then we discard it - this way we always keep the most recent result
    task_id : str = Field(default_factory=lambda: str(uuid.uuid4())) # assigned task ID, new one created if not provided
  
    # Same with the timestamp, if it's provided (mostly during de/serialization, 
    # then let's use it otherwise, let's create a new one)
    created_at : datetime.datetime = Field(default_factory=datetime.datetime.now) # Each instance gets a new timestamp

    def commands(self):
        """
        Return a list of CodeLogician agent commands for this task
        """

        if self.specified_commands:
            # We need to return those and add nothing else
            return self.specified_commands

        commands : list[Command] = [
            InitStateCommand(src_code=self.src_code, src_lang=self.language)
        ]

        if self.context is not None:
            commands.append(InjectFormalizationContextCommand(context=self.context))
    
        if self.dependencies is not None:
            commands.append(EditStateElementCommand(update={"dependency": self.dependencies}))

        if self.mode == ModelTaskMode.MANUAL:
            commands.append(GenFormalizationDataCommand())
            commands.append(GenModelCommand())

        elif self.mode == ModelTaskMode.AGENT:
            commands.append(
                AgentFormalizerCommand(
                    no_gen_model_hitl=True,
                    max_tries_wo_hitl=3,
                    max_tries=3,
                    no_check_formalization_hitl=True,
                    no_refactor=False
                )
            )
        else:
            raise Exception(f"Attempting unrecognized mode: {self.mode}")

        if self.gen_vgs:
            commands.append(GenVgsCommand(description=""))

        if self.gen_decomps:
            commands.append(GenRegionDecompsCommand(function_name=None))

        #if self.genDecomps or len(self.tests) > 0:    
        #for i in self.tests:
        #    commands.append(GenTestCasesCommand(decomp_idx=i))

        if self.gen_embeddings:
            commands.append(EmbedCommand())

        return commands

    def toJSON(self):
        """
        Convert to a JSON
        """
        return self.model_dump_json()
  
    @staticmethod
    def fromJSON(j : dict|str):
        """
        fromJSON
        """
        if isinstance(j, str):
            return ModelTask.model_validate_json(j)
        else:
            return ModelTask.model_validate(j)

    def __repr__(self):
        """ """
        return f"Base ModelTask with ID = {self.task_id}; path={self.rel_path}"

class UserManualIMLEditTask(ModelTask, BaseModel):
    """
    This updates the graph state from a manual user IML edit
    """

    iml_code : str # user provided IML code

    def commands(self):
        """
        We're just going to invoke the commands 
        """

        if self.graph_state:
            commands = [
                SetModelCommand(model=self.iml_code)
            ]
        else:
            commands : list[Command] = [
                InitStateCommand(src_code=self.src_code, src_lang=self.language),
                SetModelCommand(model=self.iml_code)

            ]

        return commands
