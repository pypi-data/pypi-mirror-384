#
#   Imandra Inc.
#
#   test_imltools.py
#

import unittest
from codelogician.tools.iml_utils import (
    update_definition, 
    add_definition, 
    remove_definition, 
    sync_definitions_topo
)

class TestIMLUtils(unittest.TestCase):
    """
    Test for IML code operations
    """

    def test_vgs(self):
        """
        let see if we can insert,modify,remove vgs
        """
        modified = add_definition("", "verify(1 < 23)")
        self.assertTrue(modified == "verify(1 < 23)")

        modified = update_definition("verify(one)", "verify", "verify(two)", verify_index=0)
        self.assertTrue(modified == "verify(two)")

        test_iml = """
let a = 123

(* hello *)

verify (fun x -> 1000 < 444)

let b = 123
"""
        modified = remove_definition(test_iml, "verify", verify_index=0)

        exp_iml = """
let a = 123

(* hello *)



let b = 123
"""     
        self.assertTrue(modified.strip() == exp_iml.strip())

    def test_update(self):
        """ """
        iml_code = """
let my_func (x : int) = 123;;
let another_func (y: int)(z: int) = my_func (y + 4);;
let another_func2(y: int)(z: int) = my_func (y + (another_func y y));;
"""
        expected_code = """
let my_func (x : int) = 123;;
let another_func (y: int) (z: int) = my_func (y + 14);;
let another_func2(y: int)(z: int) = my_func (y + (another_func y y));;
"""
        modified_code = update_definition(iml_code, "another_func", "let another_func (y: int) (z: int) = my_func (y + 14);;")

        self.assertTrue(expected_code.strip() == modified_code.strip())

    def test_insertion(self):
        """ """
        iml_code = """
let my_func (x : int) = 123;;
let another_func (y: int)(z: int) = my_func (y + 14);;
"""
        expected_code = """
let my_func (x : int) = 123;;
let another_func (y: int)(z: int) = my_func (y + 14);;
let another_func2(y: int)(z: int) = my_func (y + (another_func y y));;
"""
        modified_code = add_definition(iml_code, "let another_func2(y: int)(z: int) = my_func (y + (another_func y y));;")
        self.assertTrue(expected_code.strip() == modified_code.strip())

    def test_deletion(self):
        """
        We should be able to delete definition
        """

        iml_code = """
let my_func (x : int) = 123;;
let another_func (y: int)(z: int) = my_func (y + 4);;
let another_func2(y: int)(z: int) = my_func (y + (another_func y y));;
"""
        expected_code = """
let my_func (x : int) = 123;;
let another_func2(y: int)(z: int) = my_func (y + (another_func y y));;
"""
        modified_code = remove_definition(iml_code, "another_func")

        self.assertTrue(expected_code.strip() == modified_code.strip())

    def test_split(self):
        """ We're going to test the ability """ 
        
        originals = {}
        originals['a.iml'] = """
let func_one(a:int) = 123;;
"""

        originals['b.iml'] = """
let func_two(b:int) = func_one (b * 34 + 5);;
"""

        originals['c.iml'] = """
let func_three(c:int) = func_two (c + 10);;
"""

        combined_with_change = """
let func_new1(h : int) = 1;;
let func_one(a:int) = 123 + (func_new1 1);;
let func_two(b:int) = func_one (b * 34 + 5 + (func_new1 100));;
let func_three(c:int) = func_two (c + 10 + (func_new1 1));;
"""

        new_files = {}
        new_files['a.iml'] = """let func_one(a:int) = 123 + (func_new1 1);;"""
        new_files['b.iml'] = """let func_two(b:int) = func_one (b * 34 + 5 + (func_new1 100));;"""
        new_files['c.iml'] = """let func_three(c:int) = func_two (c + 10 + (func_new1 1));;"""
        new_files['misc.iml'] = """let func_new1(h : int) = 1;;"""

        new_split = sync_definitions_topo (
            combined=combined_with_change, 
            originals=originals, 
            misc_file_name="misc.iml")

        self.assertTrue(new_files == new_split)


if __name__ == "__main__":
    unittest.main()