#
#   Imandra Inc.
#
#   config.py
#

import logging, json, yaml, unittest
from rich.text import Text
from pydantic import BaseModel
from pydantic_yaml import parse_yaml_raw_as, to_yaml_str
from typing import Dict
from ..strategy.config import StratConfig

log = logging.getLogger(__name__)

class ServerConfig(BaseModel):
    """ Container for the Server configuration  """ 

    debug : bool = True # Are we running in debug mode?
    host : str = "127.0.0.1" # Host address
    port : int = 8000 # Port address
    mcp : bool = True # Are we running the MCP server as well?
  
    strategy_configs : Dict[str, StratConfig] = {}

    def strat_config (self, strat_name:str):
        """
        Return strategy configuration for a specified strategy
        """
        if strat_name in self.strategy_configs:
            return self.strategy_configs[strat_name]
        else:
            return StratConfig()
    
    #raise ValueError(f"{strat_name} not found!")

    def __rich__(self):
        """ Create a Rich representation """
        return Text(str(self))


    def toJSON(self):
        """ """
        return self.model_dump_json()

    def __repr__(self):
        """ Return a nice representation of the Config object """
        return json.dumps(self.toJSON(), indent=4)
  
    @staticmethod
    def fromYAML(path):
        """ Read-in the YAML file """

        try:
            with open(path) as infile:
                config = yaml.safe_load(infile)
        except FileNotFoundError as e:
            log.error(f"Failed to read in the YAML configuration: {str(e)}")
            raise Exception (f"No file found: {path}")
        except yaml.YAMLError as e:
            log.error(f"Failed to parse the YAML file: {str(e)}")
            raise Exception (f"Failed to parse the YAML file: {str(e)}")
        except Exception as e:
            log.error(f"Error parsing config: {str(e)}")
            raise Exception (f"Error parsing config: {str(e)}")

        # We should have a nice config container now
        try:
            config = ServerConfig.model_validate(config)
        except Exception as e:
            errMsg = f"ServerConfig validation error: {str(e)}"
            log.error(errMsg)
            raise Exception(errMsg)

        return config
