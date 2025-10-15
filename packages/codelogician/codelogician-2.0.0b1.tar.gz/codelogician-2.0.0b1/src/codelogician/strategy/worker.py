#
#  Imandra Inc.
#
#  worker.py
#

import asyncio, logging, os, dotenv
from threading import Thread
from queue import Queue
from pydantic import BaseModel
from enum import StrEnum
from typing import Callable, Optional, Any

from google.protobuf.message import Message
from google.protobuf.json_format import MessageToDict

from .model import Embedding
from .model_task import ModelTask
from .sketch_task import SketchChangeTask, SketchChangeResult
from .cl_agent_state import CLAgentState, CLResult, CLResultStatus
from .events import CLResultEvent, SketchChangeResultEvent

from imandra.u.agents.code_logician.graph import GraphState
#from imandra.u.agents.code_logician.base import FormalizationState, FormalizationStatus
from imandra.u.agents import create_thread_sync, get_remote_graph
from imandra.core import AsyncClient
import imandrax_api

#from imandra.u.agents.code_logician.base.imandrax import ( 
#    DecomposeRes, EvalRes, PO_Res
#)

def proto_to_dict(proto_obj: Message) -> dict[Any, Any]:
    return MessageToDict(
        proto_obj,
        preserving_proto_field_name=True,
        always_print_fields_with_no_presence=True,
    )

from imandra.u.agents.code_logician.base.region_decomp import (
    DecomposeReqData,
    RegionDecomp,
)
from imandra.u.agents.code_logician.base.vg import (
    VG,
    VerifyReqData,
)

from imandra.u.agents.code_logician.imandrax.proto_models import (
    DecomposeRes,
    VerifyRes
)

dotenv.load_dotenv(".env")
IMANDRA_UNI_KEY = os.environ["IMANDRA_UNI_KEY"]

from iml_query.processing import (
    extract_decomp_reqs,
    extract_instance_reqs,
    extract_verify_reqs,
    iml_outline,
)

log = logging.getLogger(__name__)


def printer_callback (result : CLResult|SketchChangeResult):
    """ 
    Simple printer callback function to use in testing
    """

    if isinstance(result, CLResult):
        print (f"The CLResult is: {result}")
    elif isinstance (result, SketchChangeResult):
        print (f"The ImandraXResult is {result} ")
    else:
        print (f"Unknown task type: {type(result).__name__}")

#def proto_to_dict(proto_obj: Message) -> dict:
#    """imandrax-api returns protobuf messages, this function converts them to
#    dictionaries"""
#    return MessageToDict(
#        proto_obj,
#        preserving_proto_field_name=True,
#        always_print_fields_with_no_presence=True,
#    )

async def run_sketch_task (
        task : SketchChangeTask, 
        callback : Optional[Callable[[SketchChangeResultEvent], None]]=None) -> SketchChangeResult | None:
    """
    Run ImandraX to analyze the sketch change. If `callback` function is provided, then call it with the result.
    """

    try:
        verify_reqs = extract_verify_reqs(task.iml_code)
        #instance_reqs = extract_instance_req(task.iml_code)
        decomp_reqs = extract_decomp_reqs(task.iml_code)
    except Exception as e:
        raise Exception (f"Error during extraction of artifacts from IML code: {e}")

    decomp_results, verify_results = [], []

    try:
        async with AsyncClient(
            url=imandrax_api.url_prod,
            auth_token=IMANDRA_UNI_KEY,
        ) as c:
            eval_res = await c.eval_src(task.iml_code)

            # We only run these if we could parse the file
            if eval_res.success:
                #instance_results = [
                #    c.instance(**instance_req) for instance_req in instance_reqs
                #]

                if len(decomp_reqs):
                    decomp_results = [
                        await c.decompose(**decomp_req) for decomp_req in decomp_reqs
                    ]
                else:
                    decomp_results = []
                
                if verify_reqs:
                    verify_results = [
                        await c.verify_src(**verify_req) for verify_req in verify_reqs
                    ]
                else:
                    verify_results = []

            #if len(verify_results + decomp_results):
            #    await asyncio.gather(*(verify_results + decomp_results))

    except Exception as e:
        raise Exception (f"Error during call to ImandraX: {e}")

    #eval_res = EvalRes.model_validate(proto_to_dict(eval_res_data))

    region_decomps, vgs = [], []
    if eval_res.success:
        # Fill region decomps
        for decomp_req, decomp_res in zip(decomp_reqs, decomp_results, strict=True):
            decomp_req_data_model = DecomposeReqData(**decomp_req)
            decomp_res_model = DecomposeRes.model_validate(
                proto_to_dict(decomp_res)
            )
            region_decomps.append(
                RegionDecomp(
                    data=decomp_req_data_model,
                    res=decomp_res_model,
                )
            )

        # Fill vgs
        for verify_req, verify_res in zip(verify_reqs, verify_results, strict=True):
            verify_req_data_model = VerifyReqData(
                predicate=verify_req["src"], kind="verify"
            )
            verify_res_model = VerifyRes.model_validate(proto_to_dict(verify_res))
            vgs.append(
                VG(
                    data=verify_req_data_model,
                    res=verify_res_model,
                )
            )

    result = SketchChangeResult (
        task = task,
        success = eval_res.success,
        error = str(eval_res.errors),
        vgs = vgs,
        decomps = region_decomps
    )
    if callback:
        callback(SketchChangeResultEvent(sketch_id=task.sketch_id, change_result=result))
    else:
        return result

def run_code_logician(task : ModelTask, callback : Callable[[CLResultEvent], None]|None) -> CLResult | None:
    """ Run CodeLogician agent on the specified task object and return the result via the callback function """

    if not isinstance (task, ModelTask):
        raise Exception (f"{task} should've been a proper ModelTask object")
    
    # Let's inititialize the graph
    graph = get_remote_graph("code_logician", api_key=IMANDRA_UNI_KEY)
    create_thread_sync(graph)

    # If the task has an existing graph state, let's just use that as the starting point
    if task.graph_state:
        gs = task.graph_state
    else:
        gs = GraphState()
  
    # Our task should contain the commands we need to add
    gs = gs.add_commands(task.commands())
  
    log.info("Sending request to CodeLogician")

    try:
        res, _ = asyncio.run(gs.run(graph)) # Run the agent
    except Exception as e:
        errMsg = f"Failed to make the call to CodeLogician: {e}"
        log.error (errMsg)
        return 
    
    f = res.last_fstate
    if not f:
        log.error(f"CodeLogician contained no `last_fstate` in its result!. Exiting")
        return
    
    def make_embedding(embedding_type:str, d:dict):
        return Embedding(
            source = embedding_type,
            vector = d['embedding'],
            start_line = d['start_loc']['line'],
            start_col = d['start_loc']['column'],
            end_line = d['end_loc']['line'],
            end_col = d['end_loc']['column'],
        )

    src_code_embeddings, iml_code_embeddings = [], []

    if res.steps[-1].message is not None:
        if 'src_embeddings' in res.steps[-1].message:
            for e in res.steps[-1].message['src_embeddings']:
                src_code_embeddings.append(make_embedding("SRC", e))

        if 'iml_embeddings' in res.steps[-1].message:
            for e in res.steps[-1].message['iml_embeddings']:
                iml_code_embeddings.append(make_embedding("IML", e))
    
    clAgentState = CLAgentState (
        status = f.status,
        src_code = f.src_code,
        iml_code = f.iml_code,
        iml_model = f.iml_model,
        vgs = f.vgs,
        region_decomps = f.region_decomps,
        opaque_funcs = f.opaque_funcs,
        graph_state = res,
        iml_code_embeddings=iml_code_embeddings,
        src_code_embeddings=src_code_embeddings
    )

    clResult = CLResult(
        task=task, 
        status=CLResultStatus.SUCCESS, 
        agent_state=clAgentState
    )

    log.info(f"Received result from CodeLogician. Will now run callback.")

    if callback:
        try:
            callback(CLResultEvent(result=clResult))
        except Exception as e:
            log.error (f"We've caught an exception attempting to execute the 'callback' function!")
    else:
        return clResult

class CodeLogicianWorker(Thread):
    """ Thread for processing CL requests """

    def __init__(self, callback=None):
        """
        """
        super().__init__()

        self._callback = callback
        self._queue = Queue()

    def add_task (self, task:ModelTask|SketchChangeTask|None):
        """
        Add a model task to the queue
        """

        log.info("Adding task to the queue")
        try:
            self._queue.put_nowait(task)
        except Exception as e:
            log.error (f"Couldn't add to the queue: {e}")

    def run(self):
        """
        Let's execute some CL requests
        """

        while True:
            try:
                task = self._queue.get()  # Blocks until an item is available
                log.info("Processing new task.")
            
                if task is None:  # Sentinel value to signal termination
                    log.info("Received new task 'None'. Will now shutdown.")
                    break
            
                if isinstance (task, ModelTask):
                    worker = Thread(target=run_code_logician, args=(task, self._callback, ))
                    worker.start()
                elif isinstance (task, SketchChangeTask):
                    worker = Thread(target=run_sketch_task, args=(task, self._callback, ))
                    worker.start()
                else:
                    raise Exception (f"Unsupported type of task: {type(task).__name__}")

                # we've fired off the request, so now it should be good to go...
                self._queue.task_done()

            except Exception as e:
                # This block won't be reached if get() is called without a timeout
                pass
