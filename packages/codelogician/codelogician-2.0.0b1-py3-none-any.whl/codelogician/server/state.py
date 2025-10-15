#
#   Imandra Inc.
#
#   state.py
#

from pydantic import BaseModel
from .config import ServerConfig
from rich.pretty import Pretty
import os, logging, pathlib, json

log = logging.getLogger(__name__)

class ServerState(BaseModel):
    """
    Overall server state - notice we just maintain list of directories for strategies. 
    The actual states/etc. will be stored there.
    """

    abs_path : str
    strategy_paths : list[str] = []
    config : ServerConfig = ServerConfig()

    def save(self):
        """ 
        Save server state to disk 
        """
        
        try:
            with open(self.abs_path, 'w') as outfile:
                json.dump(self.toJSON(), outfile)
        except Exception as e:
            raise Exception(f"Failed to write server state file to disk: {e}")

    def __str__ (self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())

    def toJSON(self):
        """ We're just going to store paths to the actual CL_Cache's """
        return self.model_dump_json()
        
    @staticmethod
    def fromDir (dir_path:str):
        """
        Load server state from config/command-line arguments 
        """

        abs_path = pathlib.Path(dir_path).resolve()
        if not os.path.isdir(abs_path):
            raise Exception (f"Provided path [{abs_path}] is not a directory!")
        
        return ServerState.fromFile(os.path.join(abs_path, ".cl_server"))

    @staticmethod
    def fromFile(abs_path):
        
        try:
            with open(abs_path) as infile:
                j = json.load(infile)
        except Exception as e:
            raise Exception (f"Failed to read in state file: [{abs_path}]; {e}")
        
        return ServerState.model_validate_json(j)
    
if __name__ == "__main__":
    pass
