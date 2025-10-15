#
#   Imandra Inc.
#
#   tree_views.py
#

# ruff: noqa: E501, RUF012
from typing import Generic, TypeVar

from rich.style import Style
from rich.text import Text
from textual import on
from textual.containers import Container
from textual.message import Message
from textual.widgets import TabbedContent, Tree
from textual.widgets.tree import TreeNode

from codelogician.strategy.metamodel import MetaModel


TOGGLE_STYLE = Style.from_meta({"toggle": True})
T = TypeVar("T")

class GraphView(Tree):
    def __init__(
        self, root_label, mmodel, id, tree_type='models'
    ):
        Tree.__init__(self, root_label, id=id)

        self.mmodel = mmodel

        if mmodel is None: return

        self.root.expand()

        paths = self.mmodel.get_paths_with_dirs()

        def addElements(d, root : TreeNode):
            for key, value in d.items():
                if key == '<files>':
                    for model in value:
                        if tree_type == 'models':
                            root.add_leaf(model.rel_path)
                        elif tree_type == 'dependencies':
                            temproot = root.add(model.rel_path)
                            for d in model.dependencies:
                                temproot.add_leaf(d.rel_path)
                        elif tree_type == 'rev-dependencies':
                            temproot = root.add(model.rel_path)
                            for d in model.rev_dependencies:
                                temproot.add_leaf(d.rel_path)
                else:
                    root = root.add(key)
                    addElements(value, root)

        addElements(paths, self.root)

    def render_label(self, node, base_style, style):
        if self.mmodel is None:
            return Text()
        node_label = node._label.copy()
        node_label.stylize(style)

        def get_full_path(node, path):
            if node.parent is None:
                return path
            else:
                return get_full_path(node.parent, node.parent.label + "/" + path)

        fullpath = str(get_full_path(node, node.label))
        fullpath = fullpath.replace(self.mmodel.src_dir_abs_path + "/", "")

        if fullpath in self.mmodel.models:
            model = self.mmodel.models[fullpath]
        else:
            model = None

        def indicator(n):
            return Text("✓ ", "green") if (model and not (model.agent_state is None)) else Text("")

        def toggle_icon():
            icon = self.ICON_NODE_EXPANDED if node.is_expanded else self.ICON_NODE
            return icon, base_style + TOGGLE_STYLE

        prefix = toggle_icon() if node._allow_expand else ("", base_style)
        return Text.assemble(prefix, indicator(node.data), node_label)


class TreeViews(Container):
    IDS = {"src-tree", "module-deps", "rev-deps"}

    def __init__(self, mmodel : MetaModel):
        Container.__init__(self)
        self.mmodel = mmodel
        self.styles.width = "35%"

    def compose(self):
        if self.mmodel is None:
            src_dir = ""
        else:
            src_dir = self.mmodel.src_dir_abs_path
        with TabbedContent("Source tree", "Module deps", "Reverse deps", id="tree-views"):
            yield GraphView(src_dir, self.mmodel, "src-tree", "models")
            yield GraphView("<>", self.mmodel, "module-deps", "dependencies")
            yield GraphView("<>", self.mmodel, "rev-deps",  "rev-dependencies")
