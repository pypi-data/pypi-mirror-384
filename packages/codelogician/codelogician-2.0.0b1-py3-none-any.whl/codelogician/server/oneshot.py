#
#   Imandra Inc.
#
#   oneshot.py
#

from rich.progress import Progress

import logging
from pathlib import Path
from ..strategy.config import StratConfig
from ..strategy.state import StrategyState
from ..strategy.pyiml_strategy import PyIMLStrategy

log = logging.getLogger(__name__)

def do_oneshot(clean : bool, abs_path : str, strat_config : StratConfig):
    """
    We only care about StratConfig because we're not running the server here at all.
    """

    if not Path(abs_path).is_absolute():
        abs_path = str(Path(abs_path).resolve())

    if clean:
        if Path(abs_path).is_dir():
            state = StrategyState(src_dir_abs_path=abs_path)
        else:
            state = StrategyState(src_dir_abs_path=str(Path(abs_path).parent))
    else:
        try:
            state = StrategyState.from_directory(abs_path) # We will later initialize the path
        except Exception as e:
            print (f"Encountered an exception when loading the cache: {str(e)}. Using empty state.")
            state = StrategyState(src_dir_abs_path=abs_path)

    strategy = PyIMLStrategy(state, strat_config, oneshot=True)
    
    strategy.start()

    log.info("Strategy thread started")
    strategy.join()

    try:
        state.save()
        log.info(f"Saved state to file: {state.src_dir_abs_path}")
    except Exception as e:
        print (f"Failed to save the state to disk: {str(e)}")
