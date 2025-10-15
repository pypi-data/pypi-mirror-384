#
# Imandra Inc.
#
# model_cmd_endpoints.py
#

from fastapi import HTTPException
from imandra.u.agents.code_logician.command import Command
from ..strategy.events import ModelCLTaskEvent
from .cl_server import CLServer

import logging

log = logging.getLogger(__name__)

def register_model_endpoints (app : CLServer):
    """
    Individual model commands
    """

    @app.post("/model/{strategy_id}/command/{path}", operation_id="post_model_command")
    async def model_command(strategy_id:str, path:str, cmd:Command):
        """
        Submit model command
        """

        log.info(f"For model from strategy={strategy_id} with path=[{path}]; command={cmd}")

        try:
            state = app.strategy_state_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")

        if state.curr_meta_model is None:
            return HTTPException(status_code=404, detail=f"No MetaModel exists!")

        if path not in state.curr_meta_model.models:
            return HTTPException(status_code=404, detail=f"Could not locate model with specified path=[{path}]")

        try:
            taskEvent = ModelCLTaskEvent(rel_path=path, cmd=cmd)
            app.strategy_worker_by_id(strategy_id).add_event(taskEvent)
        except Exception as e:
            errMsg = f"Failed to create a task for CodeLogician: {str(e)}"
            log.error(errMsg)
            return HTTPException(status_code=403, detail=errMsg)
    
        return {"status": "OK"}
  
    @app.get("/model/{strategy_id}/paths", operation_id="get_model_paths")
    async def model_paths(strategy_id : str):
        """
        Get list of all paths for which models exist.
        """
        
        try:
            state = app.strategy_state_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")

        log.info("Request for model paths")
        if state.curr_meta_model is None:
            return []
        else:
            return list(state.curr_meta_model.models.keys())

    @app.get("/model/{strategy_id}/bypath/{path}", operation_id="get_model_by_path")
    async def model_by_path(strategy_id : str, path : str):
        """
        Retrieve JSON representation of a model for a specified path (which is relative to the source directory)
        """
    
        log.info(f"Request for model by path")

        try:
            state = app.strategy_state_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")

        if path in state.curr_meta_model.models:
            return state.curr_meta_model.models[path].toJSON()
        else:
            return HTTPException(status_code=404, detail=f"Model with specific path [{path}] not found!")
