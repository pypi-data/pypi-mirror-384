#
# Imandra Inc.
#
# sketches_endpoints.py
#

from fastapi import HTTPException
from .cl_server import CLServer
from ..strategy.state import StrategyState
from ..strategy.sketch import SketchChange, SketchChangeTask
from ..strategy.sketch_task import (
    SketchChgSetModel, SketchChgInsertDef, SketchChgModifyDef, SketchChgDeleteDef
)
from ..strategy.events import SketchChangeEvent, SketchChangeResultEvent
from ..strategy.worker import run_sketch_task
import logging, asyncio

log = logging.getLogger(__name__)

def register_sketches_endpoints(app : CLServer):
    """ Register sketch-related endpoints """

    @app.get("/sketches/search/", operation_id="search_sketches")
    async def search (query : str):
        """
        Search for specific sketch
        """
        return {"models" : app.search_sketches(query)}

    @app.get("/sketches/list", operation_id="list_sketches")
    def get_sketches_list():
        """ 
        List all of the sketches available for all strategies. Returns a list of dictionaries,
        references by strategy id and mapped to a list of sketch IDs.

        
        'sketch_id': sketch_id,
        'anchor_model': self.sketches[sketch_id].anchor_model_path

        Example: {'STRAT_ID': [{"SketchID1", "SketchID2"]}
        """

        return { "sketches": app.list_sketches() }

    @app.post("/sketches/{strategy_id}/create", operation_id="create_sketch")
    def create_sketch(strategy_id : str, anchor_model_path : str):
        """
        Create a new sketch for this strategy
        """

        try:
            strat_state : StrategyState = app.strategy_state_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")

        if anchor_model_path not in strat_state.curr_meta_model.models:
            raise HTTPException(status_code=404, detail=f"Unknown model path: {anchor_model_path}")

        try:
            sketch_id = app.create_sketch(strategy_id, anchor_model_path)    
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to create a new sketch:{e}")

        return { "sketch_id": sketch_id }

    @app.post("/sketches/{sketch_id}/try_change", operation_id="try_sketch_change")
    async def try_sketch_change(sketch_id: str, change : SketchChange, commit_on_success : bool = True):
        """
        Try a sketch change (optionally and if successful, apply it - by default, this is True)
        """

        sketch = app.get_sketch_from_sketch_id(sketch_id)

        if sketch is None:
            raise HTTPException(status_code=404, detail=f"Could not locate sketch with ID={sketch_id}")
    
        try:
            result_iml = sketch.process_change(sketch_id, change)    
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Could not apply change: {e}")

        try:
            change_result = asyncio.run(run_sketch_task(SketchChangeTask(sketch_id=sketch_id, change=change, iml_code=result_iml)))
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Error during call to ImandraX: {e}")

        if commit_on_success and change_result is not None and change_result.error is None:
            strat = app.get_strat_for_sketch_id(sketch_id=sketch_id)
            if strat: 
                strat.add_event (SketchChangeResultEvent(sketch_id=sketch_id, change_result=change_result))
                log.info(f"Added SketchChangeResult to strategy[id={strat.state().strat_id}]")
            else:
                log.error(f"Failed to find strategy for sketch_id = {sketch_id}")

        if change_result is None:
            return { "result": "N//A" }
        else:
            return { "result" : change_result.toJSON() }

    @app.post("/sketches/{sketch_id}/change", operation_id="apply_sketch_change")
    def apply_sketch_change (sketch_id:str, change : SketchChgSetModel|SketchChgInsertDef|SketchChgModifyDef|SketchChgDeleteDef):
        """
        Apply sketch change
        """

        if sketch_id not in app.all_sketch_ids():
            raise HTTPException(status_code=404, detail=f"Sketch with id={sketch_id} was not found!")
    
        strat = app.get_strat_for_sketch_id (sketch_id)

        if strat is None:
            raise HTTPException(status_code=400, detail=f"Could not locate strategy for sketch={sketch_id}")

        strat.add_event (SketchChangeEvent(sketch_id=sketch_id, change=change))

        return {"status": "ok"}

    @app.post("/sketches/{sketch_id}/rollback", operation_id="rollback_changes")
    def rollback_changes(sketch_id:str, target_state_id:int|None=None):
        """
        Rollback changes. If `target_state_id` is specified, then the Sketch will go back to the specified state ID if possible.
        If `target_state_id` is not specified, then the Sketch will rollback the last change, unless it's the initial one.
        """

        sketch = app.get_sketch_from_sketch_id(sketch_id)

        if sketch is None:
            raise HTTPException(status_code=404, detail=f"Sketch with id={sketch_id} was not found!")
        
        try:
            sketch.roll_back(target=target_state_id)
        except Exception as e:
            raise HTTPException(status=403, detail=f"Failed to rollback the state: {e}")

        return {"status": "ok"}

    @app.post("/sketches/{sketch_id}/state", operation_id="")
    def get_latest_sketch_state(self, sketch_id : str):
        """ 
        Return the latest sketch state
        """
    
        if sketch_id not in self.app.all_sketch_ids():
            raise HTTPException(status_code=404, detail=f"Could not locate sketch with id = {sketch_id}")
    
        return { "status": "ok" }
