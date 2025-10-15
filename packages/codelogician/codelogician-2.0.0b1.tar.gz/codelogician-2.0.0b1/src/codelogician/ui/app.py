#
#   Imandra Inc.
#
#   app.py
#

from pathlib import Path
from textual import work
from textual.app import App
from textual.screen import Screen

from .screens.model import ModelScreen
from .screens.intro import IntroScreen
from .screens.overview import OverviewScreen
from .screens.decomps import DecompsScreen
from .screens.opaques import OpaquesScreen
from .screens.vgs import VGsScreen
from .screens.sketches import SketchScreen
from .screens.help import HelpScreen

from .commands import ServerCommandsProvider, ModelCommandsProvider
from .common import TUIConfig, InfoScreen, Source, Status

from ..strategy.state import StrategyState
from ..strategy.config import StratConfigUpdate
from ..strategy.metamodel import MetaModel

import os, httpx, json, argparse, datetime


class CodeLogicianTUI(App):
    CSS_PATH = "tui.tcss"

    SCREENS = {
        "intro"     : IntroScreen,
        "overview"  : OverviewScreen,
        "model"     : ModelScreen,
        "opaques"   : OpaquesScreen,
        "vgs"       : VGsScreen,
        "decomps"   : DecompsScreen,
        "sketch"    : SketchScreen,
        "help"      : HelpScreen        
    }

    MODES = {
        "intro"     : IntroScreen,
        "overview"  : OverviewScreen,
        "model"     : ModelScreen,
        "opaques"   : OpaquesScreen,
        "vgs"       : VGsScreen,
        "decomps"   : DecompsScreen,
        "sketch"    : SketchScreen,
        "help"      : HelpScreen
    }

    DEFAULT_MODE = 'intro'
    BINDINGS = [
        ("i", "switch_mode('intro')"    , "Intro"               ),
        ("o", "switch_mode('overview')" , "Overview"            ),
        ("m", "switch_mode('model')"    , "Model"               ),
        ("v", "switch_mode('vgs')"      , "Verification Goals"  ),
        ("d", "switch_mode('decomps')"  , "Decomps"             ),
        ("k", "switch_mode('opaques')"  , "Opaques"             ),
        ("s", "switch_mode('sketch')"   , "Sketches"            ),
        ("h", "switch_mode('help')"     , "Help"                ),
        ("q", "quit"                    , "Quit"                )
    ]

    
    COMMANDS = App.COMMANDS | {ServerCommandsProvider} | {ModelCommandsProvider}

    def __init__(self, status: Status):
        super().__init__()        
        self.status = status
        self.strat_states = None
        self.selected_strat_mmodel = None

        if status.source == Source.Disk and status.disk_path is not None:
            self.load_disk_strat_states(status.disk_path, True)
        elif status.source == Source.Server and status.server_addr is not None:
            self.set_server(status.server_addr)
        else:
            # By default we don't specify either one
            pass

        self.console.set_window_title("Imandra CodeLogician v1.0")

    @work()
    async def cl_server_state_retriever(self):
        if self.status.source != Source.Server: return

        self.strat_states = {}

        j = None

        try:
            endpoint = f"{self.status.server_addr}/strategy/states"
            data = httpx.get(endpoint)

            j = json.loads(data.text.strip("'"))

            for path in j:
                strat_state = StrategyState.fromJSON(j[path])
                self.strat_states[path] = strat_state

            self.status.server_last_update = datetime.datetime.now()

        except Exception as e:
            msg = f"Error when connecting to the server: {e}"
            self.status.server_error = msg

        self.status = Status(**self.status.model_dump())

        if j and self.selected_strat_mmodel is None and len(j.keys()):
            self.selected_strat_mmodel = self.strat_states[list(j.keys())[0]].curr_meta_model

        self.update_screens()
            
    def on_unmount(self) -> None:
        """ on_mount ->  """
        self.cont = False

    def do_update_strat_config (self, config : StratConfigUpdate):
        """
        This is the callback for PyIMLStrategy configuration 
        """
        pass

    def do_execute_server_command (self, command):
        """
        """
        pass

    def do_view_model (self, model_path : str):
        """ 
        Focus the view on a specific model 
        """
        pass

    def do_select_strategy(self, strat_path : str):
        """ 
        Select a specific strategy
        """

        if self.strat_states is not None and strat_path in self.strat_states:
            self.selected_strat_mmodel = self.strat_states[strat_path].curr_meta_model
        
        self.update_screens()

    def set_server(self, host:str):
        """
        Set the source to be the server 
        """

        self.status.source = Source.Server
        self.status.server_addr = host
        self.status.disk_error = None

        self.selected_strat = None

        self.timer = self.set_interval(1, self.cl_server_state_retriever)

        self.push_screen('overview')
        self.update_screens()

    def load_disk_strat_states(self, path : Path, startup:bool=False):
        """ Here, we're loading the strategy state directly from disk """

        self.status.source = Source.Disk
        self.status.server_error = None
        self.status.server_last_update = None

        try:
            state = StrategyState.fromFile(path)
            self.strat_states = {state.src_dir_abs_path:state}
        except Exception as e:
            errMsg = f"Caught an error: {str(e)}"
            if startup: print (errMsg)
            else: self.push_screen(InfoScreen(errMsg, 'error'))
            return
        
        # we only have this selected strat to go on with
        self.selected_strat_mmodel = state.curr_meta_model

        #if self.mmodel is None:
        #    errMsg = f"Loaded file, but current MetaModel doesn't exist!"
        #    self.status.disk_error = f"Failed to load MetaModel"
        #    if startup:
        #        print (errMsg)
        #    else:
        #        self.push_screen(InfoScreen(f"Loaded file, but current MetaModel doesn't exist!", 'info'))
        #    return
        #else:
        self.status.disk_error = None

        if not startup:
            # It could've only come from the overview screen, so we go back there
            self.push_screen('overview')
            self.update_screens()

    def get_system_commands(self, screen: Screen):
        yield from super().get_system_commands(screen)

    def update_screens(self):
        for screen_name in self.SCREENS:
            s = self.get_screen(screen_name)
            if hasattr(s, "status"):
                s.status = Status(**self.status.model_dump())
            if hasattr(s, "mmodel"):
                if self.selected_strat_mmodel:
                    s.mmodel = MetaModel(**self.selected_strat_mmodel.model_dump())
            if hasattr(s, "strat_states"):
                s.strat_states = self.strat_states


def set_tui_arguments(parser):
    parser.add_argument("-d", "--disk", type=str, default=None, help="Specify directory")
    parser.add_argument("-s", "--server", type=str, default=None, help="Specify connection to the server")
    parser.set_defaults(func = run_tui)

def run_tui(args):
    if args.disk:
        status = Status(source = Source.Disk, disk_path=args.disk)
    elif args.server:
        status = Status(source = Source.Server, server_addr=args.server, disk_path=os.getcwd())
    else:
        status = Status(source = Source.NoSource)

    CodeLogicianTUI(status=status).run()

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    set_tui_arguments(parser)
    
    args = parser.parse_args()
    run_tui(args)