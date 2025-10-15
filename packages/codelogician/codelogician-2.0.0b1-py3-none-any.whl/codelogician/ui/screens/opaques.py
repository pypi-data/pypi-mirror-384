#
#   Imandra Inc.
#
#   screen_opaques.py
#

from pathlib import Path

from textual import on, work
from textual.app import events
from textual.reactive import reactive
from textual.containers import (
    Horizontal,
    VerticalGroup,
    VerticalScroll,
)
from textual.screen import Screen
from textual.widgets import (
    Rule,
    Button,
    Collapsible,
    Footer,
    Label,
    Pretty,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
)

from ..common import Border, MyHeader, opaques_rich
from ..step_view import StepView
from ..tree_views import TreeViews

from ...strategy.metamodel import MetaModel, MetaModelUtils
from typing import Dict
from ...strategy.state import StrategyState

class OpaquesScreen(Screen):
    """ """

    mmodel = reactive("", recompose=True)

    def __init__(self, name = None, id = None, classes = None):
        super().__init__(name, id, classes)
        self.mmodel = self.app.selected_strat_mmodel

    def watch_mmodel (
            self, 
            old_value : MetaModel, 
            new_value : MetaModel
        ):
        pass       

    def compose(self):
        """ """
        yield MyHeader()
        
        with VerticalScroll():
            # mmodel can still be None - `curr_meta_model` doesn't guarantee anything
            if self.mmodel:
                for model_idx, path in enumerate(self.mmodel.models.keys()):
        
                    model = self.mmodel.models[path]

                    yield Rule()
                    yield Label("[$primary][b]%s[/b][/]" % path)
                    with Horizontal():
                        yield Button("View model", id=f"view_{model_idx}")
                        with VerticalGroup() as v:
                            v.styles.padding = [0, 0, 0, 1]
                            yield Rule()
                            if model.opaque_funcs():
                                header, table = opaques_rich(model.opaque_funcs())
                                yield Static(table)
        yield Footer()
    
    def on_button_pressed(self, event:Button.Pressed):
        """ Need to go to the `model` screen and focus on the specific model """
        # TODO Implement this
        pass