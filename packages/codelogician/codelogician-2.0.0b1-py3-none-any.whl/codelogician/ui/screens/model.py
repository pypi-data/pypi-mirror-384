# ruff: noqa: E741, UP031, RUF012

from pathlib import Path

from rich.text import Text
from rich.json import JSON
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
    Button,
    Collapsible,
    Footer,
    Label,
    Pretty,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
    Pretty, Rule
)

from typing import Dict
from rich.pretty import Pretty as RPretty
from ..common import Border, MyHeader, opaques_rich, vg_ui
from ..step_view import StepView
from ..tree_views import TreeViews

from ...strategy.model import Model
from ...strategy.metamodel import MetaModel
from .model_cmds import ModelCommandsView

def code_view(title, lang, code, collapsed=True, max_height=16):
    from rich.syntax import Syntax

    with Collapsible(title=title, collapsed=collapsed) as c:
        c.styles.max_height = max_height
        with VerticalScroll():
            renderable = Syntax(code, lang, line_numbers=True, indent_guides=True)
            yield Static(renderable, id=lang)

class OutputLog(RichLog):
    DEFAULT_CSS = "OutputLog { height: 10; background: $background; }"

    @on(events.Print)
    def on_print(self, event: events.Print) -> None:
        self.write(event.text)

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

class ModelStateView(VerticalGroup):
    DEFAULT_CSS = """StepView { margin: 0 1 0 0; }
    #output-group { padding: 0 1 1 1; background: $surface; }
    #button-group { align-horizontal: center; padding: 0 0 1 0 }
    #formalize-button { width: 50%; }
    OutputLog { padding: 0; }
    """
    gs = reactive(None, recompose=True)

    def __init__(self, model : Model, container):
        VerticalGroup.__init__(self)
        self.model = model
        self.container = container

    def compose(self):
        if self.model.agent_state is None:  # noqa
            with VerticalGroup(id="output-group"):
                with VerticalGroup(id="button-group"):
                    yield Button("Formalize", variant="primary", id="formalize-button")
                yield OutputLog()
        
        #elif isinstance(self.gs, tuple):
        #    exc, errors = self.gs
        #    with Collapsible(title="Errors"):
        #        yield Static(Text(errors))
        #        yield Static(Text(str(exc)))
        else:
            fstate = self.model.agent_state
            if fstate:
                yield from code_view("IML code", "ocaml", fstate.iml_code, collapsed=False)
                if len(fstate.opaque_funcs) > 0:
                    header, table = opaques_rich(fstate.opaque_funcs)
                    with Collapsible(title=header):  # "Opaque functions"):
                        yield Static(table)
                        # for f in fstate.opaques:
                        #     yield Static(f.opaque_func)

                if len(fstate.vgs) > 0:
                    with Collapsible(title="Verification goals", collapsed=False):
                        for i, vg in enumerate(fstate.vgs):
                            yield Border("VG #%d" % (i + 1), vg_ui(vg))

                if len(fstate.region_decomps) > 0:
                    with Collapsible(title="Region decomps", collapsed=False):
                        for i, d in enumerate(fstate.region_decomps):
                            yield Border("#%d" % (i + 1), Pretty(d))

                #for i, step in enumerate(self.gs.steps):
                #    with Collapsible(title="Step %d" % (i + 1)):
                #        yield StepView(step)

    def on_button_pressed(self, event):
        self.query_one("#button-group").loading = True
        # TODO This should be converted to a server command
        #self.container.formalize(self, self.module, self.query_one(OutputLog))
    

class ModelView(VerticalGroup):
    def __init__(self, model: Model, container):
        VerticalGroup.__init__(self)
        self.model = model
        self.container = container

    def compose(self):
        #yield Label(f"[$accent][b]{self.model.rel_path}[/b][/]")
        with VerticalScroll():
            yield Pretty(self.model.status())
            yield from code_view("Src code", "python", self.model.src_code, collapsed=False)
            yield ModelStateView(self.model, self.container)

class DecompsView(VerticalGroup):
    def __init__(self, model:Model, container):
        super().__init__()
        self.model = model
        self.container = container
    
    def compose(self):
        #yield Label("[$accent][b]{self.model.rel_path}[/b][/]")
        with VerticalScroll():
            Rule()

            if len(self.model.decomps()):
                for decomp in self.model.decomps():
                    yield Static(decomp.__rich__())
                    yield Rule()
            else:
                yield Static("No decomposition requests to list")

class VGsView(VerticalGroup):
    def __init__(self, model:Model, container):
        super().__init__()
        self.model = model
        self.container = container
    
    def compose(self):
        #yield Label(f"[$accent][b]{self.model.rel_path}[/b][/]")

        with VerticalScroll():
            Rule()

            if len(self.model.verification_goals()):
                for vg in self.model.verification_goals():
                    yield Static(vg.__rich__())
                    yield Rule()
            else:
                yield Static("No Verification Goals to list")

class OpaquesView(VerticalGroup):
    def __init__(self, model:Model, container):
        super().__init__()
        self.model = model
        self.container = container
    
    def compose(self):
        with VerticalScroll():
            Rule ()
            if len(self.model.opaque_funcs()):
                for opaque in self.model.opaque_funcs():
                    yield Static(opaque.__rich__())
                    yield Rule()
            else:
                yield Static("No opaque functions to list")

class ModelScreen(Screen):
    DEFAULT_CSS = """
        #panes { width: 65% }
        #panes TabPane { padding: 0 1 0 1; }
        """

    mmodel = reactive("", recompose=True)

    def __init__(self):
        Screen.__init__(self)
        self.title = "Model View"
        self.mmodel = self.app.selected_strat_mmodel

    def watch_mmodel (
            self, 
            old_value : MetaModel, 
            new_value : MetaModel
        ):
        """ """
        pass

    def compose(self):
        """ """

        yield MyHeader()

        with Horizontal():
            yield TreeViews(self.mmodel)
            with TabbedContent(id="panes"):
                with TabPane("Model state", id="model_tab"):
                    yield Static("<Nothing selected>")
                with TabPane("Command entry", id="commands_tab"):
                    yield Static("<Nothing selected")
                with TabPane("Opaque functions", id="opaques_tab"):
                    yield Static("<Nothing selected>")
                with TabPane("Decomposition requests", id="decomps_tab"):
                    yield Static("<Nothing selected")
                with TabPane("Verification goals", id="vgs_tab"):
                    yield Static("<Nothing selected>")
        
        # yield StatusBar()
        yield Footer()

    def action_switch_pane(self, pane):
        """  """
        self.query_one("#panes").active = pane
    
    def on_tree_node_selected(self, event):
        """ This gets called when the tree view (also part of this big screen) 
        receives event. """

        def get_full_path(node, path):
            if node.parent is None:
                return path
            else:
                return get_full_path(node.parent, node.parent.label + "/" + path)

        fullpath = str(get_full_path(event.node, event.node.label))
        fullpath = fullpath.replace(self.mmodel.src_dir_abs_path + '/', '')
        
        model = self.mmodel.get_model_by_path(fullpath)

        container = self.query_one("#model_tab")
        container.remove_children()
        if model: container.mount(ModelView(model, self))

        container = self.query_one("#commands_tab")
        container.remove_children()
        if model: container.mount(ModelCommandsView(model, self))

        container = self.query_one("#opaques_tab")
        container.remove_children()
        if model: container.mount(OpaquesView(model, self))

        container = self.query_one("#decomps_tab")
        container.remove_children()
        if model: container.mount(DecompsView(model, self))

        container = self.query_one("#vgs_tab")
        container.remove_children()
        if model: container.mount(VGsView(model, self))
    
    @on(Button.Pressed, "#send_commands")
    def add_model_cmmands (self, event):
        """ Add commands to the model """
        pass
