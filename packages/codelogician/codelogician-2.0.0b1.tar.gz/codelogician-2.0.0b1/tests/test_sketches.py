#
#   Imandra Inc.
#
#   test_sketches.py
#

import unittest, json, asyncio

from imandra.u.agents.code_logician.base.vg import (
    VG,
    VerifyReqData,
    RawVerifyReq,
    VerifyRes
)

from codelogician.strategy.sketch import  (
    Sketch, SketchState, SketchChange, 
    SketchContainer, 
    calc_vg_difference, ChangeSummary
)
from codelogician.strategy.sketch_task import (
    SketchChangeTask, SketchChgSetModel, 
    SketchChgInsertDef, SketchChgModifyDef, 
    SketchChgDeleteDef, SketchChange
)
from codelogician.strategy.state import StrategyState
from codelogician.strategy.worker import run_sketch_task
from codelogician.strategy.model import Model

class TestSketches(unittest.TestCase):
    """
    Let's test Sketch logic and their applications to MetaModel, etc...
    """

    def test_error_handling(self):
        """
        Test that the sketch knows how to handle errors in IML code
        """

        iml_code = "hello1234\n verify(123-33)"

        change = SketchChgSetModel(new_iml_code=iml_code)
        task = SketchChangeTask(sketch_id="123", change=change, iml_code=iml_code)

        res = asyncio.run(run_sketch_task(task, callback=None))

        self.assertFalse(res is not None and res.success)

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

verify double_non_neg$$$ative_is_increasing12

instance (fun x -> x >= 0 ==> not (double x > x))


let two_x = (let x = 1 in double x)

eval (double 2)
"""
        change = SketchChgSetModel(new_iml_code=iml_code)
        task = SketchChangeTask(sketch_id="123", change=change, iml_code=iml_code)

        res = asyncio.run(run_sketch_task(task, callback=None))

        self.assertFalse(res is not None and res.success)

    def create_base_models(self):
        """
        Create a set of base models we'll later use in the test files.
        """

        m1 = Model(rel_path="rel1.py", src_code="""
def one():
    return 1
""")
        
        m2 = Model(rel_path="rel2.py", src_code="""
def two(a):
    if one(a) + 2 > 10:
        return 1
    else:
        return a + 4
""")
        m2.add_dependency(m1)
        m3 = Model(rel_path="rel3.py", src_code="""
def three(b):
    if two(b) * 10 > 45:
        return 123
    else:
        return -3444
""")
        m3.add_dependency(m2)

        return { m.rel_path : m for m in [m1, m2, m3] }

    def test_writing_reading(self):
        """
        Create a nice sketch container and save it/load it
        """

        sk_cont = SketchContainer()

        init_model = """
let g x =
  if x > 22 then 9
  else 100 + x;;

let f x =
  if x > 99 then
    100
  else if x < 70 && x > 23
  then 89 + x
  else if x > 20
  then g x + 20
  else if x > -2 then
    103
  else 99;;

let g_upper_bound x =
   g x <= 122;;

verify (g_upper_bound);;

verify (fun x -> f x <> 158);;
"""
        
        sketch = Sketch(anchor_model_path="one.py", init_iml_model=init_model, base_models={})

        change_result = asyncio.run(run_sketch_task(sketch.gen_init_task()))
        
        self.assertTrue(change_result is not None)

        if change_result: sketch.apply_change_result(change_result=change_result)

        changes = [
            SketchChgInsertDef(new_def_code="let denis (i : int) = 123;;"),
            #SketchCh ( change_type=SketchOperation.DELETE, out_text="g" ),
            #SketchCh ( change_type=SketchOperation.INSERT, in_text="let denis2 (i : int) = 123;;" ),
        ]

        for c in changes:
            # This should get us our task
            task = None
            try:
                task = sketch.get_task(c)
            except Exception as e:
                self.assertTrue(False, f"Error during task creation: {e}")
                return

            result = asyncio.run(run_sketch_task(task))
            if result: sketch.apply_change_result(result)

        sk_cont.add(sketch)

        sketch = Sketch(
            sketch_id = "sketch_two",
            anchor_model_path="one.py",
            init_iml_model="hello",
            base_models={}
        )

        change_result = asyncio.run(run_sketch_task(sketch.gen_init_task()))
        if change_result: sketch.apply_change_result(change_result=change_result)

        changes = [
            SketchChgInsertDef ( new_def_code="let denis(i : int) = 123;;" ),
            SketchChgDeleteDef ( def_name_or_vg_idx="denis" ),
            SketchChgInsertDef ( new_def_code="let denis(i : int) = 123;;" ),
            SketchChgDeleteDef ( def_name_or_vg_idx="denis")
        ]

        for c in changes:
            # This should get us our task
            task = None
            try:
                task = sketch.get_task(c)
            except Exception as e:
                self.assertTrue(False, f"Error during task creation: {e}")
                return
            
            result = asyncio.run(run_sketch_task(task))
            if result: sketch.apply_change_result(result)

        sk_cont.add(sketch)

        path = f"src/codelogician/data/sketches/sketch_cont1.json"

        #with open(path, "w") as outfile:
        #    #print (sk_cont.model_dump_json(), outfile)
        #    pass
        

        #with open(path) as infile:
        #    j = json.load(infile)
        
        #loaded_sk = SketchContainer.fromJSON(j)

        #self.assertTrue (sk_cont == loaded_sk)

    
    def test_sketch_vg_diff(self):
        """
        This tests whether we can calculate changes in VG states across different states
        """

        vg0 = VG (
            res=VerifyRes.model_validate( {"proved": {"proved_pp": "dummy"}} ),
            data=VerifyReqData.model_validate ( {"predicate": "pred_zero", "kind": "verify"})
        )

        vg1 = VG (
            res=VerifyRes.model_validate( {"proved": {"proved_pp": "dummy"}} ),
            data=VerifyReqData.model_validate ( {"predicate": "pred_one", "kind": "verify"})
        )

        vg2 = VG (
            res=VerifyRes.model_validate( {"proved": {"proved_pp": "dummy"}} ),
            data=VerifyReqData.model_validate ( {"predicate": "pred_two", "kind": "verify"})
        )

        vg3 = VG(
            res=VerifyRes.model_validate( {"refuted": {"model": {"m_type": "Counter_example", "src":"dummy counterexample"}}}),
            data=VerifyReqData.model_validate ( {"predicate": "pred_three", "kind": "verify"})
        )

        vg4 = VG (
            res=VerifyRes.model_validate( {"proved": {"proved_pp": "dummy"}} ),
            data=VerifyReqData.model_validate ( {"predicate": "pred_three", "kind": "verify"}) 
        )

        old_vgs = [vg0, vg1, vg2, vg3]
        new_vgs = [vg1, vg2, vg4]


        diff = calc_vg_difference (old_vgs=old_vgs, new_vgs=new_vgs)

        self.assertTrue(diff[0].res_changed is None)
        self.assertTrue(diff[1].res_changed is None)
        self.assertTrue(diff[2].res_changed == ("refuted", "proved"))
        self.assertTrue(diff[3].is_removed)

    def test_sketch_creation (self):
        """
        Test that we can create a sketch, apply changes to it, and extract the models
        """

        init_iml_model = ""

        sketch = Sketch (
            anchor_model_path="a.py",
            init_iml_model=init_iml_model,
            base_models={}
        )

    def test_sketch_allocation(self):
        """
        We want to make sure that we can allocate changes in the sketch correctly to the underlying 
        models.
        """
        pass

    def test_sketch_mmodel (self):
        """
        Test that MetaModel can correctly create sketch files, and then can
        correctly incorporate back the results.
        """
        pass
    
    def test_sketch_commands_base (self):
        """
        Let's test some commands
        """

        changes = []
        # Step 1: Delete g (breaks f and g_upper_bound temporarily)
        changes.append ( SketchChgDeleteDef (def_name_or_vg_idx="g") )

        # Step 2: Insert replacement g_new with slightly different semantics *)
        changes.append(SketchChgInsertDef (new_def_code="""
let g_new x =
    if x > 22 then 10
    else 100 + x;;
"""
        ))

        # Step 3: Modify f to use g_new instead of g *)
        changes.append ( SketchChgModifyDef (
            def_name_or_vg_idx="f", new_def_body="""
let f x =
    if x > 99 then
        100
    else if x < 70 && x > 23 then
        89 + x
    else if x > 20 then
        g_new x + 20
    else if x > -2 then
        103
    else 99;;"""
        ))

        # Step 4: Modify g_upper_bound to reference g_new instead of g *)
        changes.append(SketchChgModifyDef (
            def_name_or_vg_idx="g_upper_bound",
            new_def_body="let g_upper_bound x = g_new x <= 122;;"
        ))

        # Step 5: Insert a new verification goal for g_new *)
        changes.append(SketchChgInsertDef(new_def_code="verify (fun x -> g_new x >= 0);;"))

        init_code = """
let g x =
  if x > 22 then 9
  else 100 + x;;

let f x =
  if x > 99 then
    100
  else if x < 70 && x > 23
  then 89 + x
  else if x > 20
  then g x + 20
  else if x > -2 then
    103
  else 99;;

let g_upper_bound x =
   g x <= 122;;

verify (g_upper_bound);;

verify (fun x -> f x <> 158);;
""" 
        sketch = Sketch(anchor_model_path="hello", init_iml_model=init_code, base_models={})

        task = sketch.gen_init_task()
        result = asyncio.run(run_sketch_task(task))
        if result: sketch.apply_change_result(result)

        for change in changes:
            try:
                task = sketch.get_task(change)
            except Exception as e:
                self.assertTrue(False, f"Failed to create a task: {e}")

            result = asyncio.run(run_sketch_task(task))

            if result:
                # Now we should have all the required information
                summary = sketch.apply_change_result(result)

                print (summary.stats())


    def test_skech_commands(self):
        """
        Test that a sketch can correctly process commands
        """
        
        state = StrategyState.from_directory("src/codelogician/data/code5")
        mmodel = state.curr_meta_model
        whole_model, base_models = mmodel.gen_consolidated_model(rel_path="two.py")

        # Let's create the sketch pls
        sketch = Sketch(
            anchor_model_path = "two.py",
            init_iml_model=whole_model,
            base_models = base_models
        )

        result = asyncio.run(run_sketch_task(sketch.gen_init_task()))
        if result:
            sketch.apply_change_result(change_result=result)

        # These are the changes that we propose to make to the sketch
        changes = [
            
            SketchChgInsertDef(new_def_code="let denis1 = 123;;"),
            SketchChgInsertDef(new_def_code="let denis2 = 123456;;"),
            SketchChgInsertDef(new_def_code="let denis3 = 5555;;"),
            SketchChgInsertDef(new_def_code="let denis4 = 'asd';;"),
        ]

        # Let's process the changes and make sure they all work out
        for change in changes:
            # Task should contain all the information we need to invoke ImandraX
            task = None
            try:
                task = sketch.get_task(change)
            except Exception as e:
                self.assertTrue(False, f"Error during task creation: {e}")
                return

            self.assertTrue(task is not None)

            # Result should now have all the info that's required for 
            result = asyncio.run(run_sketch_task(task, None))
            
            if result:
                # Now we should have all the required information
                summary : ChangeSummary = sketch.apply_change_result(result)

                print (summary.stats())

        # This will now take the changes that were made in the sketch
        # and apply them to the original models
        mmodel.apply_sketch (sketch)


    def test_sketch_vgs(self):
        """
        Test that we can successfully extract vgs/decomp requests from the IML file
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

verify (fun x -> x > 0 ==> double x > (123 * x))

let two_x = (let x = 1 in double x)

eval (double 2)
"""
        task = SketchChangeTask(
            sketch_id="123",
            change=SketchChgSetModel(new_iml_code=iml_code), 
            iml_code=iml_code)

        result = asyncio.run(run_sketch_task(task))


        self.assertTrue(result is not None and result.success)

        predicates=[
            'fun x -> x > 0 ==> double x > x', 
            'fun x -> x > 0 ==> double x > (123 * x)', 
        ]

        self.assertTrue(result is not None and result.vgs[0].data is not None and (result.vgs[0].data.predicate == predicates[0]))
        self.assertTrue(result is not None and result.vgs[1].data is not None and (result.vgs[1].data.predicate == predicates[1]))

    def test_sketch_loads(self):
        """
        Test serialization of a sketch object.
        """
        
        pass


if __name__ == "__main__":
    unittest.main()