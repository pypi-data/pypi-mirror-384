#
#   Imandra Inc.
#
#   vgs.py
#

from rich.text import Text
from textual import on, work
from textual.reactive import reactive
from textual.app import events
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    ScrollableContainer,
    VerticalGroup,
    Vertical,
    VerticalScroll
)
from textual.screen import Screen
from textual.widgets import (
    Footer,
    Static,
    Rule, Label, Pretty, Button
)

from ..common import Border, MyHeader

from ...strategy.metamodel import MetaModel

class HScroll(ScrollableContainer):
    DEFAULT_CSS = """
    HScroll {
        width: 150;
        height: auto;
        layout: vertical;
        overflow-y: hidden;
        overflow-x: scroll;
    }
    """

def named_vals(name_val_pairs):
    def hg(name, val):
        l = Static(f"[$primary]{name}[/]: ")
        v = Static(str(val))
        v.styles.width = "1fr"
        l.styles.width = "auto"
        return HorizontalGroup(l, v)

    return VerticalGroup(*(hg(name, val) for name, val in name_val_pairs))


def vg_ui(vg):
    from rich.pretty import Pretty as RPretty

    def req_repr(req):
        return named_vals(
            [
                ("Src func names", req.src_func_names),
                ("IML func names", req.iml_func_names),
                ("Description", req.description),
                ("Logical statement", req.logical_statement),
            ]
        )

    def data_repr(data):
        return named_vals([("Predicate", data.predicate), ("Kind", data.kind)])

    def maybe_(f, x):
        return Static("None")
        #return maybe_else(Static("None"), f, x)

    def text_repr(x):
        return Text(repr(x))

    return VerticalGroup(
        Border("RawVerifyReq", maybe_(req_repr, vg.raw)),
        Border("VerifyReqData", maybe_(data_repr, vg.data)),
        Border(
            "Result", HScroll(Static(RPretty(vg.res, overflow="ellipsis", no_wrap=True)))
        ),
    )

class VGsScreen(Screen):
    """ """

    mmodel = reactive("", recompose=True)

    def __init__(self):
        """ """
        Screen.__init__(self)
        self.title = "Verification Goals"
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
                for model_idx, path in enumerate(self.mmodel.models.keys()):
                    model = self.mmodel.models[path]
                    yield Rule()
                    yield Label(f"Model path: [$primary][b]{path}[/b][/]")
                    yield Static()
                    with Horizontal():
                        yield Button("View model", id=f"view_{model_idx}")
                        yield Rule("vertical")
                        with VerticalScroll():
                            #v.styles.padding = [0, 0, 0, 1]
                            for i, vg in enumerate(model.verification_goals()):
                                yield Border("VG #%d" % (i + 1), vg_ui(vg))

        yield Footer()