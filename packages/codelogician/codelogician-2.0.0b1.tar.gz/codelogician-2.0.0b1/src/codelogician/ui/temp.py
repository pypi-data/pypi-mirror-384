
from pathlib import PurePath
from collections import defaultdict

import httpx, json

from strategy.state import StrategyState

endpoint = "http://127.0.0.1:8000/strategy/states"
data = httpx.get(endpoint)

j = json.loads(data.text.strip("'"))

strat_states = {}
for path in j:
    strat_state = StrategyState.fromJSON(j[path])
    strat_states[path] = strat_state

print (strat_state)