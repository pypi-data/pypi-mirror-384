#
#   Imandra Inc.
#
#   app.py
#
from textual.app import App, SystemCommand, ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Footer, Label, MarkdownViewer, Placeholder, Static
)

class Splash(Screen):

    def on_mount(self):
        self.styles.align_vertical = "middle"
        self.styles.align_horizontal = "center"
        self.styles.background = "black"

    def compose(self):
        #from textual_image.widget import Image

        #banner = Image(local_file("data/splash.png"))
        #banner.styles.padding = [0, 0, 0, 0]
        #banner.styles.width = 99
        #banner.styles.height = 9
        #yield banner
        yield Label("[$primary]Imandra Code Logician, version 1.0")
        yield Footer()


class CodeLogician(App):
    CSS = "Collapsible { padding: 0 1 1 1 }\n* { scrollbar-size: 1 1 }"
    #SCREENS = {"splash": Splash}
    MODES = {
        "intro"     : Splash
    }
#        "overview"  : OverviewScreen,
#        "model"     : ModelScreen,
#        "sketch"    : SketchScreen,
#        "vgs"       : VGsScreen,
#        "decomps"   : DecompsScreen,
#        "help"      : HelpScreen
#    }
    DEFAULT_MODE = 'intro'
    BINDINGS = [
        ("i",  "intro", "Intro"),
    ]

    def __init__(self, mmodel = None, do_splash=True):
        App.__init__(self)
        self.mmodel = mmodel
        self.do_splash = do_splash



    def get_system_commands(self, screen: Screen):
        yield from super().get_system_commands(screen)
        yield SystemCommand("Bell", "Ring the bell", self.bell)


if __name__ == "__main__":

    #from strategy.state import PyIMLStrategyState
    #state = PyIMLStrategyState.from_directory("data/code2")
    #mmodel = state.curr_meta_model

    CodeLogician(None).run()