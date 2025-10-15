#
#   Imandra Inc.
#
#   decomps.py
#

from pathlib import Path
from rich.text import Text
from textual import on, work
from textual.app import events
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    ScrollableContainer,
    VerticalGroup,
    VerticalScroll,
)
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Placeholder,
    Footer,
    Rule,
    Button,
    Label,
    Static,
    Pretty
)

from ..common import Border, MyHeader, opaques_rich
from ..step_view import StepView
from ..tree_views import TreeViews

from ...strategy.model import Model
from ...strategy.metamodel import MetaModel, MetaModelUtils
from ...strategy.state import StrategyState
from typing import Dict

class DecompsScreen(Screen):
    """ """

    mmodel = reactive("", recompose=True)

    def __init__(self):
        """ ctor """
        Screen.__init__(self)
        self.title = "Region Decompositions"
        self.mmodel = self.app.selected_strat_mmodel

    def watch_mmodel(
            self, 
            old_value : MetaModel, 
            new_value : MetaModel
        ):
        """ """
        pass

    def compose (self):
        """ """

        yield MyHeader()

        with VerticalScroll():
            if self.mmodel:
                for idx, path in enumerate(self.mmodel.models.keys()):

                    model = self.mmodel.models[path]

                    yield Rule()
                    yield Label("[$primary][b]%s[/b][/]" % path)
                    with Horizontal():
                        yield Button("View model", id=f"btn_{idx}_view_model")
                        with VerticalGroup() as v:
                            v.styles.padding = [0, 0, 0, 1]
                            for decomp in model.decomps():
                                yield Rule()
                                yield Pretty(decomp)
        
        yield Footer()

if __name__ == '__main__':
    pass