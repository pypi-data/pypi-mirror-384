#
#   Imandra Inc.
#
#   cl_caller.py
#

from imandra.u.agents.code_logician.graph import GraphState
from imandra.u.agents.code_logician.command import InitStateCommand, GenFormalizationDataCommand, GenModelCommand
from imandra.u.agents.code_logician.base import FormalizationStatus
from imandra.u.agents import create_thread_sync, get_remote_graph
from queue import Queue
from threading import Thread
import asyncio

from ..strategy.cl_agent_state import CLAgentState

def clAutoformalize (src_code):
    """ Return the object containing results of running CodeLogician agent """

    graph = get_remote_graph("code_logician", api_key="29U5z4uV1E1Jbg6bOzdT4kpJUoqSKgaoaVzlGyt1zQfNXjFd")
    create_thread_sync(graph)

    # Create an empty agent state (`GraphState`), set the Python source program to the `src_code` element of the state and run the agent.
    gs = GraphState()

    # Create a list of commands for CL to execute
    gs = gs.add_commands([
        InitStateCommand (src_code=src_code, src_lang="python"), # Will initialize the state with specified Python source program
        GenFormalizationDataCommand(), # Will gather relevant formalization data (required to create the model)
        GenModelCommand(), # Will attempt to generate the formalized model
    ])

    res = asyncio.run(gs.run(graph)) # Run the agent
  
    f = res[0].last_fstate

    def formalizationStatusConverter(s):
        if s == FormalizationStatus.UNKNOWN:
            return "unknown"
        elif s == FormalizationStatus.INADMISSIBLE:
            return "inadmissable"
        elif s == FormalizationStatus.ADMITTED_WITH_OPAQUENESS:
            return "admitted_with_opaqueness"
        elif s == FormalizationStatus.EXECUTABLE_WITH_APPROXIMATION:
            return "executable_with_approximation"
        elif s == FormalizationStatus.TRANSPARENT:
            return "transparent"
        else:
            raise Exception (f"Something went wrong!!!")

    return CLAgentState (
        status = formalizationStatusConverter(f.status),
        src_code = f.src_code,
        iml_code = f.iml_code,
        vgs = f.vgs,
        region_decomps = f.region_decomps,
        opaque_funcs=f.opaques
    )
