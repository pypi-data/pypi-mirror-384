#
# Imandra Inc.
#
# endpoints.py
#

from .endpts_metamodel import register_metamodel_endpoints
from .endpts_model import register_model_endpoints
from .endpts_sketches import register_sketches_endpoints
from .endpts_strategy import register_strategy_endpoints
from .endpts_server import register_server_endpoints
from .cl_server import CLServer


def register_endpoints(app : CLServer): 
    """
    Register all the endpoints
    """

    register_server_endpoints(app)
    register_metamodel_endpoints(app)
    register_model_endpoints(app)
    register_sketches_endpoints(app)
    register_strategy_endpoints(app)