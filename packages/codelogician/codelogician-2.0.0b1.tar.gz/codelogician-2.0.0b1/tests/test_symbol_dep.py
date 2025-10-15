from pathlib import Path

from inline_snapshot import snapshot

from codelogician.dep_graph.file_tree import FileSystem
from codelogician.dep_graph.symbol_dep.python import build_py_dep_graph
from test_utils import find_pyproject


class TestResolveImport:
    def resolve_import(self, repo_name: str):
        data_dir = find_pyproject(Path(__file__)) / "data"
        py_repo_path = data_dir / repo_name
        fs = FileSystem.from_disk(py_repo_path, ["py"])
        symbol_dep = build_py_dep_graph(fs)
        # return "\n".join(sorted(symbol_dep.edges_repr().split("\n")))
        return symbol_dep.graph_repr()

    def test_sample_simple_math_lib(self):
        assert self.resolve_import("sample_simple_math_lib") == snapshot("""\
__init__.py
advanced/__init__.py
advanced/geometry/__init__.py
advanced/geometry/shapes.py
├── basic.py
└── utils/helpers.py
basic.py
math_ops.py
└── basic.py
utils/__init__.py
└── utils/helpers.py
utils/helpers.py
├── basic.py
└── math_ops.py
""")

    def test_sample_bank_app(self):
        assert self.resolve_import("sample_bank_app") == snapshot("""\
account.py
├── currency.py
└── transaction.py
asset.py
└── currency.py
bank.py
├── account.py
├── asset.py
├── currency.py
├── ledger.py
├── liability.py
└── transaction.py
currency.py
ledger.py
├── account.py
├── asset.py
├── currency.py
└── liability.py
liability.py
└── currency.py
transaction.py
└── currency.py
""")

    def test_sample_math_lib(self):
        assert self.resolve_import("sample_math_lib") == snapshot("""\
__init__.py
analysis/__init__.py
analysis/numerical/__init__.py
├── analysis/numerical/derivatives.py
└── analysis/numerical/integration.py
analysis/numerical/derivatives.py
└── core/arithmetic.py
analysis/numerical/integration.py
└── core/arithmetic.py
analysis/optimization/__init__.py
└── analysis/optimization/root_finding.py
analysis/optimization/root_finding.py
├── analysis/numerical/derivatives.py
├── core/arithmetic.py
└── core/comparison.py
core/__init__.py
├── core/arithmetic.py
└── core/comparison.py
core/advanced.py
├── core/arithmetic.py
└── core/comparison.py
core/arithmetic.py
core/comparison.py
stats/__init__.py
├── stats/basic.py
└── stats/measures.py
stats/basic.py
├── core/arithmetic.py
└── core/comparison.py
stats/measures.py
├── core/advanced.py
├── core/arithmetic.py
└── stats/basic.py
utils.py
├── core/advanced.py
├── core/arithmetic.py
├── stats/basic.py
└── stats/measures.py
""")
