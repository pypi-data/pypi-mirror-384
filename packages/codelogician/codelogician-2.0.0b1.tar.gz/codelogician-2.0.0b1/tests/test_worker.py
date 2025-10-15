#
#   Imandra Inc.
#
#   test_worker.py
#

import unittest, asyncio

from codelogician.strategy.model import Model
from codelogician.strategy.worker import (
    CodeLogicianWorker, 
    printer_callback, 
    run_code_logician, 
    run_sketch_task
)
from codelogician.strategy.model_task import ModelTask
from codelogician.strategy.sketch_task import SketchOperation, SketchChange, SketchChangeTask


class TestWorker(unittest.TestCase):
    """
    Test that worker's methods for calling CL/ImandraX work properly 
    """

    def test_cl_formalization_call(self):
        """
        Test that we can successfully formalize a bit of Python code...
        """
        src_code = """
        def g(x: int) -> int:
        if x > 22:
            return 9
        else:
            return 100 + x
        
        def f(x: int) -> int:
        if x > 99:
            return 100
        elif 70 > x > 23:
            return 89 + x
        elif x > 20:
            return g(x) + 20
        elif x > -2:
            return 103
        else:
            return 99
        """

        model = Model(
            rel_path="one.py",
            src_code=src_code
        )

        task = model.gen_formalization_task()

        result = run_code_logician(task, None)

        self.assertTrue(result is not None)

        if result:
            model.apply_agent_state(result.agent_state, [])

        expModelCode = """
let g (x : int) : int =
  if x > 22 then
    9
  else
    100 + x

let f (x : int) : int =
  if x > 99 then
    100
  else if 70 > x && x > 23 then
    89 + x
  else if x > 20 then
    g x + 20
  else if x > -2 then
    103
  else
    99
"""

        self.assertTrue(model.iml_code() is not None)
        self.assertTrue(model.iml_code().strip() == expModelCode.strip()) # pyright: ignore

    def test_embedding_call(self):
        """
        Test that we can call CodeLogician and get embeddings back
        """

        # Initially, we only have the source code, no IML
        model = Model(
            rel_path="one.py",
            src_code="""
def f(a, b):
    return a + b
"""
        )

        task = model.gen_formalization_task()

        result = run_code_logician(task, None)

        self.assertTrue(result is not None)
        model.apply_agent_state(result.agent_state, []) # pyright: ignore

        #print (result.agent_state.src_code_embeddings)

        self.assertTrue(len(model.src_code_embeddings) == 1)
        self.assertTrue(len(model.iml_code_embeddings) == 1)

        expModelCode = """
let f (a : int) (b : int) : int =
  a + b
"""
        self.assertTrue(model.iml_code() is not None) 
        self.assertEqual(model.iml_code().strip(), expModelCode.strip()) # pyright: ignore

    def test_sketch_call(self):
        """ 
        Test running sketch change tasks        
        """

        iml_code = """
let add_one (x: int) : int = x + 1
[@@decomp top ()]

let is_positive (x: int) : bool = x > 0

let double (x: int) : int = x * 2

let decomp_double = double
[@@decomp top ~assuming: [%id is_positive] ~prune: true ()]

let square : int -> int = ()
[@@opaque]

let cube : int -> int = ()
[@@opaque]

axiom positive_addition x =
  x >= 0 ==> add_one x > x

theorem double_add_one x =
  double (add_one x) = add_one (add_one x) + x
[@@by auto]

verify (fun x -> x > 0 ==> double x > x)

let double_non_negative_is_increasing (x: int) = x >= 0 ==> double x > x

verify double_non_negative_is_increasing

instance (fun x -> x >= 0 ==> not (double x > x))


let two_x = (let x = 1 in double x)

eval (double 2)
"""

        change = SketchChange(change_type=SketchOperation.INIT, in_text=iml_code)
        task = SketchChangeTask(sketch_id="123", change=change, iml_code=iml_code)
        res = asyncio.run(run_sketch_task(task, callback=None))
        
        self.assertTrue(res is not None)
        self.assertTrue(res.success) # pyright: ignore

if __name__ == "__main__":
    unittest.main()