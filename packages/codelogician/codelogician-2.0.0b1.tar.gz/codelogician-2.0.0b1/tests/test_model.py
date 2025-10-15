#
#   Imandra Inc.
#
#   test_model.py
#   

from codelogician.strategy.cl_agent_state import CLAgentState
from codelogician.strategy.model import Model

from imandra.u.agents.code_logician.base import (
    FormalizationDependency,
    #FormalizationStatus,
    ModuleInfo,
)

from codelogician.tools.cl_caller import clAutoformalize

import unittest, json
from pathlib import Path

class TestModelMethods(unittest.TestCase):
    """ TestModelMethods """

    def testModelDepGeneration(self):
        m1_code = """
            def hello_m1():
            return 1
            """

        m1 = Model(rel_path="m1.py", src_code=m1_code)

        imlModuleInfo = m1.to_CL_iml_module_info()
        self.assertTrue(imlModuleInfo is None)

        srcModuleInfo = m1.to_CL_src_module_info()

        srcModuleInfo2 = ModuleInfo(
            name = "m1.py",
            relative_path = Path("m1.py"),
            content = m1_code,
            src_lang = "Python"
        )

        self.assertEqual(srcModuleInfo, srcModuleInfo2)

        # This should update the
        m1AgentState = CLAgentState(iml_code="let hello_m1() = 1")
        m1.apply_agent_state(m1AgentState)

    def testSrcCodeSetting(self):
        """ Test how updates to the model's source code changes its need for formalization """

        some_code = """
            def denis_function(x):
                if x > 4:
                3
                else:
                12
        """

        # The model has no formalizaiton state, no instructions, etc.
        # And no dependencies, so we should be ready to formalize it
        m1 = Model(rel_path="my_path.py", src_code=some_code)

        self.assertTrue (m1.formalization_reasons())
        self.assertFalse(m1.context_provided())
        self.assertFalse(m1.deps_changed())
        self.assertFalse(m1.deps_need_formalization())

        m1.context = "try harder"
        self.assertTrue(m1.context_provided())

        m1.context = ""
        self.assertFalse(m1.context_provided())

    def testModelDependencies(self):
        """ Test out how the model keeps accounting of what the  """

        m1_code = """
            def hello_m1():
            return 1
            """

        m2_code = """
            def hello_m2():
            return 2
            """

        m3_code = """
            def hello_m3():
            return 3
            """

        m1 = Model(rel_path="m1.py", src_code=m1_code)
        m2 = Model(rel_path="m2.py", src_code=m2_code)
        m3 = Model(rel_path="m3.py", src_code=m3_code)

        # Add dependencies
        m3.dependencies.append(m1)
        m3.dependencies.append(m2)

        # Since m1 and m2 have no formal state, they should be formalized
        self.assertTrue(m3.deps_need_formalization())

        # This should be False because m3 is not formalized and m1/m2 are not formalized
        self.assertFalse(m3.deps_changed(), "Should be False since m1/m2/m3 have no formal states")

        # Apply agent states
        from codelogician.strategy.cl_agent_state import CLAgentState

        m1.apply_agent_state(CLAgentState(src_code="New code"))
        m2.apply_agent_state(CLAgentState(src_code="New code"))

        self.assertTrue(m1.formalization_reasons())
        self.assertTrue(m2.formalization_reasons())

        # This should now return False because the models have been formalized
        self.assertTrue(m3.formalization_reasons())
        self.assertTrue(m3.deps_changed())

        # Let's now apply agent state to our model along with dependencies
        m3AgentState = CLAgentState(iml_code="let hello_m3() = 3")

        dependencies = [
        FormalizationDependency(
            src_module = ModuleInfo (
            name = "m1.py"
            , relative_path=Path("m1.py")
            , content = m1_code
            , src_lang = "python"
            ),
            iml_module = ModuleInfo(
            name = "m1.py"
            , relative_path=Path("m1.py")
            , content = "let hello_m1() = 1"
            , src_lang = "IML"
            )
        )
        , FormalizationDependency(
            src_module = ModuleInfo (
            name = "m2.py"
            , relative_path=Path("m2.py")
            , content = m2_code
            , src_lang = "python"
            ),
            iml_module = ModuleInfo(
            name = "m2.py"
            , relative_path=Path("m2.py")
            , content = "let hello_m2() = 2"
            , src_lang = "IML"
            )
        )
        ]

        dependencies2 = [
        FormalizationDependency (
            src_module = ModuleInfo (
            name = "m1.py"
            , relative_path=Path("m1.py")
            , content = m1_code
            , src_lang = "python"
            ),
            iml_module = ModuleInfo (
            name = "m1.py"
            , relative_path=Path("m1.py")
            , content = "let hello_m1() = 100"
            , src_lang = "iml"
            )
        )
        , FormalizationDependency (
            src_module = ModuleInfo (
            name = "m2.py"
            , relative_path=Path("m2.py")
            , content = m2_code
            , src_lang = "python"
            ),
            iml_module = ModuleInfo (
            name = "m2.py"
            , relative_path=Path("m2.py")
            , content = "let hello_m2() = 200"
            , src_lang = "IML"
            )
        )
        ]

        m3.apply_agent_state(m3AgentState, dependencies=dependencies)
        self.assertFalse(m3.deps_changed(), "Dependencies' IML code did not change at all")

        dependencies = [
        FormalizationDependency(
            src_module = ModuleInfo (
            name = "m1.py"
            , relative_path=Path("m1.py")
            , content = m1_code
            , src_lang = "python"
            ),
            iml_module = ModuleInfo(
            name = "m1.py"
            , relative_path=Path("m1.py")
            , content = "let hello_m1() = 1"
            , src_lang = "IML"
            )
        )
        , FormalizationDependency(
            src_module = ModuleInfo (
            name = "m2.py"
            , relative_path=Path("m2.py")
            , content = m2_code
            , src_lang = "python"
            ),
            iml_module = ModuleInfo(
            name = "m2.py"
            , relative_path=Path("m2.py")
            , content = "let hello_m2() = 200"
            , src_lang = "IML"
            )
        )
        ]

        m3.apply_agent_state(m3AgentState, dependencies=dependencies)
        self.assertTrue(m3.deps_changed(), "We should now pick up that the latest code is different from what we have for m2")

    def testSavingLoading(self):
        """ Test to make sure we can Save to/Load from disk """

        some_code = """
        def denis_function(x):
            if x > 4:
                3
            else:
                12
        """

        m1 = Model(rel_path="my_path.py", src_code=some_code)
        agentstate = clAutoformalize (some_code)

        m1.apply_agent_state(agentstate)
        with open('data/tests/text.json', 'w') as outfile:
            json.dump(m1.toJSON(), outfile)

        with open('data/tests/text.json') as infile:
            contents = json.load(infile)

        print (contents)
        m2 = Model.fromJSON(contents)

        self.assertEqual(m1, m2, "m1 and m2 should be equal now!")

    def test_ModelWithDependencies(self):
        """ Let's test model with """
        pass

if __name__ == "__main__":
    unittest.main()
