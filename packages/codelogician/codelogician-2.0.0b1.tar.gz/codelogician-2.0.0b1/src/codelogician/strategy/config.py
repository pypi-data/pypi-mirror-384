#
#   Imandra Inc.
#
#   config.py
#   

# TODO we should just make this declarative (i.e. specify field, their types,
# default values, etc) and have the rest of the code be auto-generated. Too 
# much code duplication here

from enum import Enum
import logging, yaml, json

from rich.pretty import Pretty
from rich.panel import Panel
from rich import print as rprint
from typing import Optional
from pydantic import BaseModel

log = logging.getLogger(__name__)

class StratMode(Enum):
    """ Strategy has two modes:
        - standby - it always waits for commands to kick off formalization and do so only in 
            specific batches (i.e. )
        - auto - this continuously checks whether there's something that can be formalized 
            and attempts to submit it
    """

    STANDBY = "standby"
    AUTO = "auto"

class StratConfigUpdate(BaseModel):
    """ 
        We use this to update strategies configuration
    """
    time_for_filesync_checback : Optional[int] = None
    write_models : Optional[bool] = None
    write_consolidated : Optional[bool] = None
    artifact_dir : Optional[str] = None
    iml_dir : Optional[str] = None
    mode : Optional[StratMode] = None
    save_on_close : Optional[bool] = None
    meta_caching : Optional[bool] = None

class StratConfig(BaseModel):
    """
    Container for the PyIML Strategy configuration
    """

    time_for_filesync_checkback : int = 5 # How long to wait (in seconds) for changes to local files to subside
    write_models : bool = True # Should we write individual models (when there's iml code)
    write_models_in_same_dir : bool = True # When we write out IML models, should we write them next to the source files?
    write_consolidated : bool = False # Should we write a consolidated model when possible?
    artifact_dir : str = 'cldata' # Directory with generated artifacts (relative to the source directory)
    iml_dir : str = 'iml' # Directory (relative to artifact directory) where IML models will be written
    mode : StratMode = StratMode.AUTO # AUTO/STANDBY mode (this deals with formalization)
    save_on_close : bool = True # Should we save the state/config on shutdown
    meta_caching : bool = True # Should we be caching the meta state?

    def setField(self, field, value):
        """
        Attempt to set the specified 'field' to 'value'
        """

        def convert_str_to_bool(v:str):
            if v.lower() in ['t', 'true']: return True
            if v.lower() in ['f', 'false']: return False
            raise Exception (f"Unknown value {v} - can't convert to a bool!")

        # TODO Again, we should auto-generate this from description 
        # of all the fields and their types

        if field == 'time_for_filesync_checkback':
            self.time_for_filesync_checkback = int(value)
        elif field == 'write_models':
            self.write_models = convert_str_to_bool(value)
        elif field == 'write_models_in_same_dir':
            self.write_models_in_same_dir = bool(value)
        elif field == 'write_consolidated':
            self.write_consolidated = convert_str_to_bool(value)
        elif field == 'iml_dir':
            self.iml_dir = str(value)
        elif field == 'mode':
            try:
                self.mode = StratMode[value.upper()]
            except Exception as e:
                raise Exception (f"Invalid enum value for `mode` [{str(e)}]. Possible values are: 'STANDBY', 'AUTO'")
        elif field == 'save_on_close':
            self.save_on_close = convert_str_to_bool(value)
        elif field == 'meta_caching':
            self.meta_caching = convert_str_to_bool(value)
        else:
            raise KeyError(f"Specified field {field} not found!")

    def __repr__(self):
        """ Return a nice representation of the Config object """
        return json.dumps(self.toJSON(), indent=4)

    @staticmethod
    def fromJSON(j : str|dict):
        """
        Return an object from JSON file
        """

        if isinstance(j, str):
            return StratConfig.model_validate_json(j)
        elif isinstance(j, dict):
            return StratConfig.model_validate(j)
        else:
            raise Exception (f"Input must be either a str or a dict!")

    def toJSON(self):
        """ Return a JSON object """
        return self.model_dump_json()

    @staticmethod
    def fromYAML(path):
        """ fromYAML """

        try:
            with open(path) as infile:
                config = yaml.safe_load(infile)
        except FileNotFoundError:
            log.error(f"No file found: {path}")
            raise Exception (f"No file found: {path}")
        except yaml.YAMLError as e:
            log.error(f"Failed to parse the YAML file: {str(e)}")
            raise Exception (f"Failed to parse the YAML file: {str(e)}")
        except Exception as e:
            log.error(f"Failed to read in the YAML configuration: {str(e)}")
            raise Exception (f"Error parsing config: {str(e)}")

        # We should have a nice config container now
        try:
            config = StratConfig.model_validate(config)
        except Exception as e:
            errMsg = f"PyIMLConfig validation error: {str(e)}"
            log.error(errMsg)
            raise Exception(errMsg)

        return config

    def __rich__ (self):
        """ 
        Return a Rich representation
        """
    
        pretty = Pretty(self.toJSON(), indent_size=2)
        return Panel(pretty, title="PyIMLStrategy config", border_style="green")
