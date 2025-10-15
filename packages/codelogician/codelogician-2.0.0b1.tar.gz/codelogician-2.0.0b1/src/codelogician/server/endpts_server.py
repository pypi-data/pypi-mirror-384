#
# Imandra Inc.
#
# server_endpoints.py
# 

import logging
from .cl_server import CLServer

log = logging.getLogger(__name__)

def register_server_endpoints(app : CLServer):
    """ 
    General admin endpoints for the server
    """

    @app.get("/server/status", operation_id="get_server_status")
    async def status():
        """ 
        Returns status of the server.
        """
        return {"message": "Hello, World! I'm the CodeLogician Server!"}

    @app.get("/server/tutorial", operation_id="server_tutorial")
    async def tutorial():
        """
        Returns text description of how the server works and the main functions. This is 
        useful for MCP clients to learn about how to use the server itself.
        """

        tutorial = """
CodeLogician server is an 


How CodeLogician works:
- It creates a formal model of the source code, while processing each file - one at a time.
- It then 

Possible workflows:
- Creating a formal model of the project (directory)

        """
        return {"tutorial": tutorial}

    @app.get("/server/config", operation_id="get_server_config")
    async def server_config():
        """ 
        Return current server configuration 
        """
        log.info("Received request for server configuration")
        return app._state.config.toJSON()
