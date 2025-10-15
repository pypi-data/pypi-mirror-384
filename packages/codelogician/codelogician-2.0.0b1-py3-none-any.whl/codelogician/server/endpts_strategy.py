#
# Imandra Inc.
#
# strategy_endpoints.py
#

from fastapi import HTTPException
from .cl_server import CLServer
from .state import ServerState
from ..strategy.state import StrategyState
from ..strategy.config import StratConfig, StratConfigUpdate
from typing import Dict

# TODO need to implement this vs manually creating an pydantic model
#from pydantic_partial import create_partial_model
#PartialPyIMLConfig = create_partial_model(StratConfig)

import logging
log = logging.getLogger(__name__)

def register_strategy_endpoints(app: CLServer):
    """ 
    Functions relate to accessing the state of the strategy or sending it commands
    """

    @app.get("/strategy/list", operation_id="list_strategies")
    async def list_strategies () -> list[Dict[str,str]]:
        """
        Return the current list of strategies. Each strategy will contain:
        - 'strat_id' - strat_id
        - 'path' - directory path for this strategy
        - 'type' - 'PyIML' will be returned as it's the only strategy currently supported 
        """
        return app.list_strategies()

    @app.get("/strategy/states", operation_id="get_all_strategy_states")
    async def all_strategy_states() -> list[StrategyState]:
        """
        Return all strategy states
        """
        return list(app.strategy_states().values())

    @app.post("/strategy/create", operation_id="create_new_strategy")
    async def create_strategy (path:str):
        """
        Create a new strategy
        """
        try:
            strat_id = app.add_strategy(path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to create strategy: {e}")
    
        return {'strategy_id': strat_id}

    @app.post("/strategy/{strategy_id}/delete", operation_id="delete_strategy")
    async def delete_strategy(strategy_id : str):
        """
        Remove strategy (will stop the worker and delete it from the container)
        """

        try:
            app.rem_strategy(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to delete strategy: {str(e)}")
    
        return {'status': 'ok'}

    @app.get("/strategy/{strategy_id}/state", operation_id="get_strategy_state")
    async def strat_state(strategy_id : str):
        """
        Return the full strategy state 
        """
        log.info(f"Received strategy state request")

        try:
            state = app.strategy_state_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")

        return state.toJSON()

    @app.get("/strategy/{strategy_id}/summary", operation_id="get_strategy_summary")
    async def strat_summary(strategy_id : str):
        """
        Return PyIML strategy state summary
        """
        log.info("Received request for strategy summary")    

        try:
            state = app.strategy_state_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")

        return state.summary()

    @app.get("/strategy/{strategy_id}/config", operation_id="get_strategy_config")
    async def strat_config(strategy_id : str):
        """ 
        Return the current strategy configuration 
        """
        log.info("Received request for strategy config")

        try:
            strat_config = app.strategy_config_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy state: {e}")

        return strat_config
  
    @app.patch("/strategy/{stategy_id}/config/set", operation_id="set_config_field")
    async def strat_config_set(strategy_id : str, configUpdate : StratConfigUpdate):
        """
        Set strategy configuration field to specified value.
        """

        try:
            strat_config = app.strategy_config_by_id(strategy_id)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to get strategy config: {e}")

        log.info(f"Received strategy config update request: {str(configUpdate.model_dump())}")
        try:
            updated_data = configUpdate.model_dump(exclude_unset=True)
            for key, value in updated_data.items():
                setattr(strat_config, key, value)
        
            app.update_strat_config(strategy_id, strat_config)
        except Exception as e:
            err_msg = f"Error when attempting to update config: {str(e)}"
            log.error(err_msg)
            return HTTPException(status_code=406, detail=err_msg)
        
        return {"status": "ok"}
