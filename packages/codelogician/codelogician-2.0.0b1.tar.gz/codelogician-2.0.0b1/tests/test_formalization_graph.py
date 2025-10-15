from pathlib import Path

import pytest
from inline_snapshot import snapshot

from codelogician.dep_graph.formalization import FormalizationGraph
from codelogician.dep_graph.symbol_dep import ModuleDep

fixtures_dir = Path(__file__).parent / "fixtures"


@pytest.fixture
def fgraph() -> FormalizationGraph:
    return FormalizationGraph.load(fixtures_dir / "formalization_graph_joblib_cache")


def test_to_iml_dep_graph(fgraph: FormalizationGraph):
    assert fgraph.graph_repr() == snapshot("""\
__init__
(unformalized)
advanced.__init__
(unformalized)
advanced.geometry.__init__
(unformalized)
advanced.geometry.shapes
(transparent)
├── basic
│   (transparent)
└── utils.helpers
    (transparent)
basic
(transparent)
math_ops
(transparent)
└── basic
    (transparent)
utils.__init__
(unformalized)
└── utils.helpers
    (transparent)
utils.helpers
(transparent)
├── basic
│   (transparent)
└── math_ops
    (transparent)
""")
    iml_dep_graph = fgraph.into_iml_dep_graph()
    assert iml_dep_graph.graph_repr() == snapshot("""\
advanced/geometry/init.iml
advanced/geometry/shapes.iml
├── basic.iml
└── utils/helpers.iml
advanced/init.iml
basic.iml
init.iml
math_ops.iml
└── basic.iml
utils/helpers.iml
├── basic.iml
└── math_ops.iml
utils/init.iml
└── utils/helpers.iml
""")


def test_to_file_system(fgraph: FormalizationGraph):
    iml_dep_graph: ModuleDep = fgraph.into_iml_dep_graph()
    fs = iml_dep_graph.into_file_system(Path("root"), filter_empty=True)
    assert fs.graph_repr() == snapshot("""\
.
├── advanced
├── basic.iml
├── math_ops.iml
└── utils
advanced
└── advanced/geometry
advanced/geometry
└── shapes.iml
basic.iml
helpers.iml
math_ops.iml
shapes.iml
utils
└── helpers.iml
""")
