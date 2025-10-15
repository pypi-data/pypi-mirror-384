#
#   Imandra Inc.
#
#   test_strat_state.py
#

import unittest
from rich import print as rprint
from codelogician.strategy.state import StrategyState

class TestStrategyState(unittest.TestCase):
    """ Test strategy state functions """

    def test_full_state_run (self):
        """ Let's:
        - 1. look at a directory
        - 2. formalize it
        - 3. save the state to disk
        """

        print ()
        print ()
        print (f"testFullStateRun")

        src_dir = "data/code2"

        print ("Step 1: Create a state from an empty cache directory")
        state = StrategyState.from_directory(src_dir)

        print (f"Let's now print out the state: \n {str(state)}\n\n")

        print ("Step 2: let's ask the state to update models' src code status. This should require them to generate tasks")
        state.run_file_sync()

        print ("The Metamodel should now have two models with source code but no formalization:")
        print (state)

        print (f"Step 3: Ask state to generate tasks")
        tasks = state.get_next_tasks()

        print (f"We now have {len(tasks)} tasks to work on!")
        for t in tasks:
            print (f"Task: {str(t)}")

        print (f"Let's now work on those tasks!")

        state.save()

    def test_state_load (self):
        """ """
        src_dir = "data/code2"

        state = StrategyState.from_directory(src_dir)

        rprint (state)

if __name__ == "__main__":

    unittest.main()