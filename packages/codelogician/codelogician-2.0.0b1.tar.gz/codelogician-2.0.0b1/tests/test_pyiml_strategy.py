#
#   Imandra Inc.
#
#   test_pyiml_strategy.py
#

import unittest
from codelogician.strategy.state import StrategyState
from codelogician.strategy.pyiml_strategy import PyIMLStrategy, StratMode
from codelogician.strategy.events import ChangeMode


class TestPyIMLStrategy(unittest.TestCase):
    """ 
    Test PyIML strategy worker
    """

    def test_codelogician_calls(self):
        """ """

        print (f"Step 1: Load in the state value")
        state = StrategyState.from_directory("data/code2")

        print (state.curr_meta_model)

        for m in state.curr_meta_model.models:
            print (m)

        print(f"Step 2: Start the thread")
        strat = PyIMLStrategy(state)
        strat.start()

        print (f"Step 3: Send an event to the strategy - this should kick off autoformalization for us")
        # All files in the directory
        strat.add_event (ChangeMode(new_mode=StratMode.AUTO))

        print (f"Step 4: Wait until it completes")
        import time
        time.sleep(30)

        strat.add_event(None)

        print (f"Step 5: Print out the summary and the models")

        print (f"Step 6: Our models should now have mode set to `transparent`")
        #for path in models:
        #  #print (models[path])

        state.save()

if __name__ == "__main__":
  unittest.main()
