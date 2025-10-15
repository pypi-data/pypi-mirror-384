#
#   Imandra Inc.
#
#   overview.py
#

import os
from textual.app import on
from textual.screen import Screen
from textual.reactive import reactive
from textual.widgets import (
    Footer, Input, Static, Button, 
    RadioButton, RadioSet, Rule, DirectoryTree, Select
)
from textual.containers import Horizontal, Vertical, VerticalGroup, VerticalScroll
from rich.pretty import Pretty
from rich.panel import Panel

from ..common import MyHeader, Source, InfoScreen
from ...strategy.state import StrategyState
from ...strategy.metamodel import MetaModel
from typing import Iterable, Dict
from pathlib import Path

class FilteredDirectoryTree(DirectoryTree):
    """ We just want to show directories and `cl_cache` files. """
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        l = lambda x: x.name.startswith(".cl_cache") or os.path.isdir(x)
        return [path for path in paths if l(path)]

class SelectFileDirectory(Screen):
    """ """

    def __init__(self, name = None, id = None, classes = None):
        super().__init__(name, id, classes)
        self.styles.align_horizontal = 'center'
        self.styles.align_vertical = 'middle'

    def compose(self):
        self._path_selected = None
        with VerticalGroup() as vg:
            vg.styles.align_horizontal = "center"
            vg.styles.align_vertical = "middle"

            yield Static("Select directory or cache file location")

            if self.app.status.disk_path:
                path = self.app.status.disk_path
                if os.path.isfile(path):
                    path = Path(path).parent
            else:
                path = os.getcwd()
            
            yield FilteredDirectoryTree(path=path, id="directory_tree")

            with Horizontal():
                yield Button("Go up", id="go_up_button")
                yield Button("Select", id="sfdirectory_select")
                yield Button("Cancel", id="sfdirectory_cancel")

    def on_directory_tree_file_selected(self, event):
        self._path_selected = event.path

    @on(Button.Pressed, selector="#go_up_button")
    def go_up_directory_view(self):
        
        directoryTree = self.query_one("#directory_tree")
        directoryTree.path = Path(directoryTree.path).parent
        directoryTree.reload() 


    @on(Button.Pressed, selector="#sfdirectory_cancel")
    def cancel(self):
        self.app.pop_screen()
    
    @on(Button.Pressed, selector="#sfdirectory_select")
    def select(self):
        if self._path_selected:
            self.app.status.disk_path = self._path_selected

        self.dismiss(self._path_selected)
        #self.app.pop_screen()

class SourceSelectionView(VerticalGroup):
    """ """
    def __init__(self, app, status, disk_path):
        super().__init__()
        self._app = app
        self.status = status
        self.disk_path = disk_path
    
    def compose (self):
        self.styles.padding = (2, 4)

        yield Static("Select CL source (server/disk):")

        with RadioSet(id="radioset"):
            yield RadioButton("Server", id="configure_server_source", value=(self.status.source == Source.Server))
            with VerticalGroup(id="server_vg") as vg:
                vg.styles.padding = (2, 4)
                yield Static("Enter CodeLogician server details:")
                if self.status.server_addr:
                    yield Input(value=self.status.server_addr, id="server_address")
                else:
                    yield Input(value="", id="server_address")
                yield Button("Apply", id="apply_server")
                if self.status.source == Source.Disk:
                    vg.disabled = True
            yield Rule()
            
            yield RadioButton("Disk", id="configure_disk_source", value=(self.status.source == Source.Disk))
            with VerticalGroup(id="disk_vg") as vg:
                vg.styles.padding = (2, 4)
                path = self.disk_path if self.disk_path else ""
                yield Static(content=f"Current selection: {path}", id="current_disk_path")

                yield Button("Select source", id="directory_view")
                yield Button("Apply", id="apply_disk")
                if self.status.source == Source.Server:
                    vg.disabled = True

    @on(RadioSet.Changed, "#radioset")
    def make_source_selection(self, event:RadioSet.Changed):
        """ make_source_selection """

        if event.index == 0:
            server_vg = self.query_one("#server_vg")
            server_vg.disabled = False
            server_input = self.query_one("#server_address")
            server_input.focus()

            disk_vg = self.query_one("#disk_vg")
            disk_vg.disabled = True

        else:
            server_vg = self.query_one("#server_vg")
            server_vg.disabled = True

            disk_vg = self.query_one("#disk_vg")
            disk_vg.disabled = False

            button = self.query_one("#directory_view")
            button.focus()

    @on(Button.Pressed, "#apply_server")
    def on_apply_server (self) -> None:
        host = self.query_one("#server_address")
        self._app.set_server(host.value)

    @on(Button.Pressed, "#apply_disk")
    def on_apply_disk (self, event : Button.Pressed) -> None:
        self._app.load_disk_strat_states(self.disk_path)

    @on(Button.Pressed, "#directory_view")
    def on_directory_view (self, event : Button.Pressed) -> None:
        def get_path(path : str | None):
            self.disk_path = path

        self.app.push_screen(SelectFileDirectory(), get_path)


class OverviewScreen(Screen):
    """ Overview Screen """

    strat_states    = reactive("", recompose=True)
    mmodel          = reactive("", recompose=True)
    disk_path       = reactive("")
    status          = reactive(None)

    def __init__(self):
        """ """
        Screen.__init__(self)
        self.title = "Overview"
        self.strat_states = self.app.strat_states
        self.mmodel = self.app.selected_strat_mmodel
        self.status = self.app.status
        self.disk_path = self.app.status.disk_path

    def watch_disk_path(self, new_path):
        """ """
        try:
            s = self.query_one("#current_disk_path", Static)
            s.update(f"Selection: {self.disk_path}")
        except: pass
    
    def watch_mmodel(
            self,
            old_value : MetaModel,
            new_value : MetaModel
        ):
        pass

    def watch_strat_states(
            self, 
            old_value : Dict[str, StrategyState], 
            new_model : Dict[str, StrategyState]
        ):
        """ When the StratStates value gets updated, this will be called """
        if not self.strat_states or not len(self.strat_states.values()): return

        for idx, strat in enumerate(self.strat_states.values()):
            mmodel = strat.curr_meta_model
            path = strat.src_dir_abs_path
            if mmodel:
                pretty = Pretty(mmodel.summary(), indent_size=2, expand_all=True)
            else:
                pretty = "N\\A"

            overviewPanel = Panel(pretty, title=f"Overview:{path}", border_style="green")

            try:
                panel = self.query_one(f"#strat_summary_{idx}")
                panel.update(overviewPanel)
            except: pass

        # mmodel = list(self.strat_states.values())[0].curr_meta_model
        # if mmodel:
        #     pretty = Pretty(mmodel.summary(), indent_size=2, expand_all=True)
        #     overviewPanel = Panel(pretty, title="MetaModel Overview", border_style="green")
        #     try:
        #         p = self.query_one("#strat_summary_{idx}")
        #         p.update(overviewPanel)
        #     except Exception as e:
        #         self.app.push_screen(InfoScreen(f"Caught an error: {str(e)}; {mmodel.summary()}", 'error'))

    def watch_status(self, new_status):
        try:
            pretty = Pretty(self.status.model_dump(), indent_size=2, expand_all=True)
            panel = Panel(pretty, title="TUI Status", border_style="green")
            s = self.query_one("#status")
            s.update(panel)
        except: pass

    def compose(self):
        yield MyHeader()


        with Vertical():
            with Horizontal():
                yield SourceSelectionView(self.app, self.status, self.disk_path)
                
                with Vertical():
                    yield Static("Select an available strategy:")

                    if self.strat_states:
                        paths_values = []
                        idx = None

                        for curr_idx, path in enumerate(self.strat_states.keys()):
                            paths_values.append((path, curr_idx))
                            if self.mmodel and path == self.mmodel.src_dir_abs_path:
                                idx = curr_idx
                        
                        if idx:
                            yield Select(options=paths_values, prompt="Click to make selection", allow_blank=False, id="strat_selection")
                        else:
                            yield Select(options=paths_values, prompt="Click to make selection", allow_blank=False, id="strat_selection")
                    else:
                        yield Select(options=[], id="strat_selection")

                    yield Rule()

                    if self.status:
                        pretty = Pretty(self.status.model_dump(), indent_size=2, expand_all=True)
                    else:
                        pretty = "N\\A"
                    panel = Panel(pretty, title="TUI Status", border_style="green")
                    yield Static(panel, id="status")
                    
            yield Rule()

            with VerticalScroll() as vs:
                vs.styles.background = 'blue'
                if self.strat_states:
                    for idx, strat in enumerate(self.strat_states.values()):
                        mmodel = strat.curr_meta_model
                        path = strat.src_dir_abs_path
                        if mmodel:
                            pretty = Pretty(mmodel.summary(), indent_size=2, expand_all=True)
                        else:
                            pretty = "N\\A"

                        overviewPanel = Panel(pretty, title=f"Overview:{path}", border_style="green")
                        yield Static(content=overviewPanel, id=f"strat_summary_{idx}")
                
        yield Footer()

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.curr_strat_selection = event.value
        self.app.do_select_strategy(event.value)
