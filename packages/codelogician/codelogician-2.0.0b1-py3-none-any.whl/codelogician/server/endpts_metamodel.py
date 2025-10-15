#
# Imandra Inc.
#
# metamodel_endpoints.py
#


from fastapi import HTTPException
from .cl_server import CLServer
import logging

log = logging.getLogger(__name__)

def register_metamodel_endpoints(app : CLServer):

    # Return summary of the current state
    @app.get("/metamodel/{strategy_id}/latest/summary", operation_id="get_summary")
    async def metamodel_latest_summary(strategy_id:str):
        """
        Return summary of the latest metamodel
        """

        try:
            state = app.strategy_state_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")

        log.info("Received /state/summary request")
        # already returns JSON representation
        if state.curr_meta_model is None:
            return {}
        else:
            return state.curr_meta_model.summary()

    @app.get("/metamodel/{strategy_id}/latest/list", operation_id="get_models_list")
    async def model_list(strategy_id:str, listby:str="frm_status"):
        """
        Return a list of model statistics, sorted by specified criteria. Options are:
        - frm_status - formalization status
        - upstream - number of models upstream which are affected by the specified model
        - opaques - number of opaque functions
        - failed_vgs - number of failed verification goals
        """
        log.info(f"Received request for model listing by {listby}.")

        try:
            state = app.strategy_state_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")

        try:
            if state.curr_meta_model is None:
                return []
            else:
                return state.curr_meta_model.gen_listing(listby)
        except Exception as e:
            return HTTPException(status_code=404, detail=f"Error when requesting listing: {str(e)}")

    @app.get("/metamodel/{strategy_id}/latest/vgs", operation_id="list_of_vgs")
    async def verification_goals(strategy_id:str):
        """
        Return verification goals with their statuses for the entire metamodel
        """

        try:
            state = app.strategy_state_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")
  
        log.info("Received /state/latest/vgs request")
        if state.curr_meta_model is None: return []
        
        return state.curr_meta_model.vgs()

    @app.get("/metamodel/{strategy_id}/latest/decomps", operation_id="list_of_decomps")
    async def decomps(strategy_id:str):
        """
        Return the list of decomps
        """

        log.info("Received /state/latest/decomps request")

        try:
            state = app.strategy_state_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")

        if state.curr_meta_model is None: return []
        return state.curr_meta_model.decomps()

    @app.get("/metamodel/{strategy_id}/latest/opaques", operation_id="list_of_opaque_functions")
    async def opaques(strategy_id:str):
        """
        Return list of opaque functions
        """

        log.info("Received /state/latest/opaques request")

        try:
            state = app.strategy_state_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")

        if state.curr_meta_model is None: return []
        return state.curr_meta_model.opaques()

    @app.get("/metamodel/{strategy_id}/latest", operation_id="latest_metamodel")
    async def latest_state (strategy_id:str):
        """
        Return the latest metaModel
        """
        log.info("Received request for the latest metamodel")

        try:
            state = app.strategy_state_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")

        if state.curr_meta_model is None: return {}
        return state.curr_meta_model.toJSON()

    @app.get("/metamodel/{strategy_id}/cache/by_index/{idx}", operation_id="get_metamodel_from_cache")
    async def get_state(strategy_id:str, idx : int):
        """
        Returns a complete state of the cache.
        """
        log.info("Received cache metamodel request for index {idx}")

        try:
            state = app.strategy_state_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")

        if idx in state.meta_cache.indices():
            mmodel = state.meta_cache.get_cache_metamodel(idx)
            if mmodel is None:
                return HTTPException(status_code=404, detail=f"Metamodel from cache with index={idx} not found!")
            else:
                return mmodel.toJSON()
        else:
            log.error(f"{idx} index not found!")
            return HTTPException(status_code=404, detail=f"Metamodel from cache with index={idx} not found!")

    @app.get("/metamodel/{strategy_id}/cache/indices", operation_id="get_metamodel_cache_indices")
    async def cache_indices (strategy_id:str) -> list[int]:
        """
        Return the list of all indices in cache.
        """

        log.info("Request for all indices.")

        try:
            state = app.strategy_state_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")
    
        return state.meta_cache.indices()
