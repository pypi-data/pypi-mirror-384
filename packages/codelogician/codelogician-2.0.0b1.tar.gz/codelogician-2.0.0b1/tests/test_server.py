#
#   Imandra Inc.
#
#   test_server.py
#


from fastapi.testclient import TestClient
from codelogician.strategy.state import StrategyState
from codelogician.strategy.config import StratConfig
from codelogician.server.cl_server import CLServer
from codelogician.server.state import ServerState

import unittest, os

class TestServerEndpoints(unittest.TestCase):
    """
    Let's make sure all the endpoints are working as expected
    """

    @classmethod
    def setUpClass(cls):
        state = ServerState(abs_path=os.getcwd())
        cls._client = TestClient(CLServer(state))

    def test_server_endpts(self):
        """ 
        Test that status message is returned correctly
        """
        response = self._client.get("/server/status")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello, World! I'm CodeLogician Server!"}

        response = self._client.get("/server/tutorial")
        assert response.status_code == 200
        assert 'tutorial' in response.json() and len(response.json()['tutorial'])


    def test_server_add_remove_strats(self):
        """
        Test that we can add/remove strategies and access info about them correctly
        """

        # we should not have any strategies present
        response = self._client.get("/strategy/list")
        assert response.status_code == 200
        assert response.json() == []

        # the response should get us a strat ID
        response = self._client.post("/strategy/create", params={'path': 'data/code5'})
        assert response.status_code == 200
        assert 'strategy_id' in response.json()

        # Now that we have the strategy created, we should be able to inspect its state, get a summary
        strat_id = response.json()['strategy_id']

        response = self._client.get(f"/strategy/{strat_id}/state")
        assert response.status_code == 200
        assert StrategyState.fromJSON(response.json())

        response = self._client.get(f"/strategy/{strat_id}/config")
        assert response.status_code == 200
        assert StratConfig.fromJSON(response.json())


    def test_sketches_api(self):
        """
        Test that we can create a sketch, add instructions to it, check the results, etc.
        """

        # Let's create the sketch from an 'anchor model' = 'one.py'
        response : dict = self._client.post("/sketches/{strat_id}/create", params={'anchor_model_path': "one.py"})
        assert response.status_code == 200
        assert 'sketch_id' in response

        new_sketch_id = response.json()['sketch_id']

        # Let's make sure it's not in the list of sketches
        response : dict = self._client.get("/sketches/list")

        assert response.status_code == 200
        assert 'sketches' in response.json()

        # let's now add a definition 
        assert 


        sketch = self._client.get("/sketches")



if __name__ == "__main__":
    unittest.main()