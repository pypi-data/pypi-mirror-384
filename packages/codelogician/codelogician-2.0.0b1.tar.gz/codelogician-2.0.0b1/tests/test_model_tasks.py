#
#   Imandra Inc.
#
#   test_model_tasks.py
#


import unittest

from imandra.u.agents.code_logician.base import (
    FormalizationDependency,
    #FormalizationStatus,
    ModuleInfo,
)

from imandra.u.agents.code_logician.command import (
    InjectFormalizationContextCommand
)

from codelogician.strategy.model_task import ModelTask
from codelogician.strategy.model import Model
from codelogician.strategy.worker import run_code_logician

from pathlib import Path
import asyncio

class TestTasks(unittest.TestCase):
    """ 
    Test Model tasks and their execution
    """
    
    @unittest.skip
    def test_serialization(self):
        """
        Let's make sure that we can serialize this correctly
        """
        path = "hello.py"
        
        srcCode = 'def hello():\n return 1'
        context = "Human-provided context"
        
        dependencies = [
      	    FormalizationDependency (
        		src_module = ModuleInfo(
          			name = path,
          			relative_path=Path(path),
          			content = srcCode,
          			src_lang="Py"
        		), 
        	    iml_module = ModuleInfo(
          		    name=path,
          		    relative_path=Path(path),
          		    content="let one = 1",
          		    src_lang="IML"
        	    )
      		)
    	]

        t = ModelTask(
            rel_path="",
            src_code="", 
            context=context,
            dependencies=dependencies
        )

        j = t.toJSON()

        t2 = ModelTask.fromJSON(j)

        self.assertEqual(t, t2)

    @unittest.skip
    def test_construction(self):
        """ Test task construction """
        pass

    @unittest.skip
    def test_Context(self):
        """ Test that the context plays a role """

        context = "Try doing something special here"

        mtask = ModelTask(
            rel_path="hello.py", 
            src_code="def hello():\n return 1",
            context=context
        )
    
        contextCmd = InjectFormalizationContextCommand(context=context)

        self.assertTrue(contextCmd in mtask.commands())

    def test_model_setting (self):
        """
        Test that we can successfully set the model code and then extract 
        all the VGs/Decomps from it.
        """

        src_code = """
def my_func(one:int)=
    return 2 * one
"""

        m = Model(
            rel_path="my_model.py",
            src_code=src_code
        )

        iml_code = """
let my_func(one : int) =
    2 * one
[@@decomp top ()]

verify (fun x -> x <> 1)
"""

        m.set_iml_model(iml_code)

        task = m.gen_iml_user_update_task()

        res = run_code_logician(task, callback=None)

        expected_iml_code = """
let my_func(one : int) =
    2 * one
[@@decomp top ()]

verify (fun x -> x <> 1)
"""

        expected_iml_model = """
let my_func(one : int) =
    2 * one
"""
        self.assertTrue(res.agent_state.iml_code.strip() == expected_iml_code.strip())
        self.assertTrue(res.agent_state.iml_model.strip() == expected_iml_model.strip())
        self.assertTrue(len(res.agent_state.vgs) == 1)
        self.assertTrue(res.agent_state.vgs[0].data.predicate == 'fun x -> x <> 1')
        self.assertTrue(len(res.agent_state.region_decomps) == 1)
        self.assertTrue(res.agent_state.region_decomps[0].data.name == 'my_func')

if __name__ == "__main__":
    unittest.main()
