#
#   Imandra Inc.
#
#   test_search.py
#

import unittest

from codelogician.strategy.model import Model
from codelogician.strategy.metamodel import MetaModel
from codelogician.strategy.cl_agent_state import Embedding

from imandra.u.agents.code_logician.command import (
    EditStateElementCommand,
    EmbedCommand,
    InitStateCommand,
)

from imandra.u.agents.code_logician.graph import GraphState

import random

class TestSearch(unittest.TestCase):
    """
    """

    def test_search_simple(self):
        """
        Test that MetaModel can correctly find models with precalculated embedding vectors
        """

        def rand_vector():
            return [ random.random() for i in range(3054)]

        m1e = Embedding(source="hello", vector = rand_vector() )
        m1 = Model(rel_path='one.py', src_code_embeddings=[m1e])

        m2e = Embedding(source="hello", vector = rand_vector() )
        m2 = Model(rel_path='two.py', src_code_embeddings=[m2e])

        m3e = Embedding(source="hello", vector = rand_vector() )
        m3 = Model(rel_path='three.py', src_code_embeddings=[m3e])

        models = { 'one.py': m1, 'two.py': m2, 'three.py': m3 }

        mmodel = MetaModel(src_dir_abs_path="data/code5", models=models)

        results = mmodel.search(rand_vector())

        for result in results:
            print (result)


    def test_search_call_cl_src_only(self):
        """
        Call CL to generate embeddings then insert them and do the search
        """
        pass

if __name__ == "__main__":
    unittest.main()