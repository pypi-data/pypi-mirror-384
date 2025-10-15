#
#   Imandra Inc.
#
#   test_metamodel.py
#


import unittest

from codelogician.tools.cl_caller import clAutoformalize
from codelogician.strategy.cl_agent_state import CLAgentState
from codelogician.strategy.metamodel import MetaModel
from codelogician.strategy.model import Model
from codelogician.server.events import FileSystemEvent, FileSystemEventType

class TestMetaModel(unittest.TestCase):
    """ 
    Test MetaModel functionality
    """

    def test_cl_agent_states(self):
        """ Test serialization """

        some_code1 = """
def denis_function1(x):
    if x > 4:
        3
    else:
        12
"""
        path1 = "my_path1.py"
        m1 = Model(rel_path="my_path1.py", src_code=some_code1)
        astate = CLAgentState.fromJSON(clAutoformalize(some_code1).toJSON())
        m1.apply_agent_state(astate)

        some_code2 = """
def denis_function2(x):
    if x > 14:
        43
    else:
        12
"""

        path2 = "my_path2.py"
        m2 = Model(rel_path="my_path2.py", src_code=some_code2)
        astate = CLAgentState.fromJSON(clAutoformalize(some_code2).toJSON())
        m2.apply_agent_state(astate)

        models = {
            path1: m1, path2: m2
        }

        metaModel = MetaModel(src_dir_abs_path="", models=models)
        #print (metaModel)

    def test_dependency_changes(self):
        """
        Dependency changes
        """

        m1 = Model(rel_path="a.py", src_code="Hello")
        m2 = Model(rel_path="b.py", src_code="Hello")
        m3 = Model(rel_path="c.py", src_code="Hello")

        models = {
            'a.py': m1,
            'b.py': m2,
            'c.py': m3
        }

        # Let's now add dependencies
        m1.add_dependency(m2)
        m1.add_dependency(m3)
        m2.add_dependency(m3)

        #for m in models.values():
        #    print (m)

        #print (f"Now let's change the model and update its dependencies...")

        # The dependencies should be updated now...
        #for m in models.values():
        #    print (m)

    def test_file_sync(self):
        """ test filesync """

        mmodel = MetaModel(src_dir_abs_path="data/code2", models={})
        mmodel.run_file_sync()
        #print (mmodel)

    def test_process_events_create(self):
        """ Let's test out process events """

        meta = MetaModel(src_dir_abs_path="data/tests/events1", models={})
        event = FileSystemEvent(
            action_type=FileSystemEventType.CREATED, 
            abs_path1="data/tests/events1/one.py"
        )
        meta.process_filesystem_event(event)

        self.assertEqual(len(meta.models.keys()), 1)

    def test_upstream_calcs(self):
        """ Test that we're calculating upstream models correctly """

        m1 = Model(rel_path="m1.py", src_code="")

        m2 = Model(rel_path="m2.py", src_code="")
        m2.add_dependency(m1)

        m3 = Model(rel_path="m3.py", src_code="")
        m3.add_dependency(m2)

        m4 = Model(rel_path="m4.py", src_code="")
        m4.add_dependency(m3)
        m4.add_dependency(m2) # this should not affect the total count below

        m5 = Model(rel_path="m5.py", src_code="")
        m5.add_dependency(m4)

        m6 = Model(rel_path="m6.py", src_code="")
        m6.add_dependency(m5)

        m7 = Model(rel_path="m7.py", src_code="")
        m7.add_dependency(m6)

        m8 = Model(rel_path="m8.py", src_code="")
        m8.add_dependency(m7)

        m9 = Model(rel_path="m9.py", src_code="")
        m9.add_dependency(m8)

        m10 = Model(rel_path="m10.py", src_code="")
        m10.add_dependency(m9)

        models = {}
        models['m1.py'] = m1
        models['m2.py'] = m2
        models['m3.py'] = m3
        models['m4.py'] = m4
        models['m5.py'] = m5
        models['m6.py'] = m6
        models['m7.py'] = m7
        models['m8.py'] = m8
        models['m9.py'] = m9
        models['m10.py'] = m10

        mmodel = MetaModel(src_dir_abs_path="", models=models)

        self.assertEqual(mmodel.calc_upstream_affected("m1.py") , 9)
        self.assertEqual(mmodel.calc_upstream_affected("m2.py") , 8)
        self.assertEqual(mmodel.calc_upstream_affected("m3.py") , 7)
        self.assertEqual(mmodel.calc_upstream_affected("m4.py") , 6)
        self.assertEqual(mmodel.calc_upstream_affected("m5.py") , 5)
        self.assertEqual(mmodel.calc_upstream_affected("m6.py") , 4)
        self.assertEqual(mmodel.calc_upstream_affected("m7.py") , 3)
        self.assertEqual(mmodel.calc_upstream_affected("m8.py") , 2)
        self.assertEqual(mmodel.calc_upstream_affected("m9.py") , 1)
        self.assertEqual(mmodel.calc_upstream_affected("m10.py"), 0)

    def test_path_with_dirs(self):

        m1 = Model(rel_path="hello.py")
        m2 = Model(rel_path="hello2.py")
        m3 = Model(rel_path="one/hello3.py")
        m4 = Model(rel_path="two/three/hello4.py")

        models = { m.rel_path : m for m in [m1, m2, m3, m4] }
        mmodel = MetaModel(src_dir_abs_path="data/code2", models = models)

        paths = mmodel.get_paths_with_dirs()


    def test_consolidated_model(self):
        """ """

        m1 = Model(rel_path="m1.py", src_code = "", agent_state=CLAgentState(iml_code="let m1 = 1;;"))
        m2 = Model(rel_path="m2.py", src_code = "", agent_state=CLAgentState(iml_code="let m2 = 2;;"))
        m3 = Model(rel_path="m3.py", src_code = "", agent_state=CLAgentState(iml_code="let m3 = 3;;"))
        m4 = Model(rel_path="m4.py", src_code = "", agent_state=CLAgentState(iml_code="let m4 = 4;;"))
        m5 = Model(rel_path="m5.py", src_code = "", agent_state=CLAgentState(iml_code="let m5 = 5;;"))
        m6 = Model(rel_path="m6.py", src_code = "", agent_state=CLAgentState(iml_code="let m6 = 6;;"))
        m7 = Model(rel_path="m7.py", src_code = "", agent_state=CLAgentState(iml_code="let m7 = 7;;"))

        m2.dependencies = [m1]
        m3.dependencies = [m2]
        m4.dependencies = [m1]
        m5.dependencies = [m3, m4]

        models = {
            'm1.py': m1,
            'm2.py': m2,
            'm3.py': m3,
            'm4.py': m4,
            'm5.py': m5,
            'm6.py': m6,
            'm7.py': m7
        }

        mmodel = MetaModel(src_dir_abs_path='data/test_dir', models=models)

        consolidated_iml, dep_models = mmodel.gen_consolidated_model('m4.py')
        exp_model = """
(* Starting m4.py *)
let m4 = 4;;
(* Ending m4.py)
(* Starting m1.py *)
let m1 = 1;;
(* Ending m1.py)
"""
        self.assertEqual(consolidated_iml.strip(), exp_model.strip())
   
if __name__ == "__main__":
    unittest.main()
