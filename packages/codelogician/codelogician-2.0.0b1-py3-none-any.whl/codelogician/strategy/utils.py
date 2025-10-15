#
#   Imandra Inc.
#
#   dep_graph.py
#

from .model import Model
from .model_status import ModelStatus, SrcCodeStatus
from typing import Dict

class DependencyGraph:
    """ Set of utilities for checking that there are no cycles in the models """

    @staticmethod
    def checkNoCycles(models : Dict[str, Model]):
        """ Returns True if there're no loops, False otherwise """

        return True

    @staticmethod
    def setDependencyChanges(model : Model, models : Dict[str, Model]):
        """ For a given model, go through everything that it affects and change depsChanges to True for it """

        for path, m in models.values():
            if path == model.rel_path(): continue

            if model in m.dependencies():
                m.setDependenciesChanged(True)

                DependencyGraph.setDependencyChanges(m, models)

    @staticmethod  
    def getAffected(model : Model, existing_list : list[Model] = []):
        """ Return the list of paths for all models ultimately affected by changes to this model """

        for m in model.affects():
            pass

        return existing_list 

    @staticmethod
    def identifyNextBatch (models : Dict[str, Model]):
        """ Given the various models -> figure out which ones we can work on next """

        pass
  
def testOne():
    """ testOne """

    m1 = Model("a.py", "hello")
    m2 = Model("b.py", "hello")
    m3 = Model("c.py", "Hello")

    models = {
        'a.py': m1,
        'b.py': m2,
        'c.py': m3
    }

    m1.dependencies(m2)
    m1.dependencies(m3)

    m2.dependencies(m3)

    for _, m in models.values():
        print (m)
  
    print (f"Now let's change the model and update its depdendencies")

    # This should now make the model require formalization task to be performed
    m3.setFileSyncStatus(SrcCodeStatus.SRC_CODE_CHANGED)
    DependencyGraph.setDependencyChanges(m3, models)

    # The depdendencies should be updated now...
    for _, m in models.values():
        print (m)


if __name__ == "__main__":

    try:
        testOne()
    except Exception as e:
        print (f"Failed testOne: {str(e)}")
