#
#   Imandra Inc.
#
#   intro.py
#

from textual_image.widget import HalfcellImage as Image
from textual.screen import Screen
from textual.widgets import (
    Footer, Label
)

from pathlib import Path

def local_file(name):
    return Path(__file__).parent / name

class IntroScreen(Screen):
    def on_mount(self):
        self.styles.align_vertical = "middle"
        self.styles.align_horizontal = "center"
        self.styles.background = "black"

    def compose(self):
        banner = Image(local_file("../data/splash.png"))
        banner.styles.padding = [0, 0, 0, 0]
        banner.styles.width = 99
        banner.styles.height = 9
        yield banner
        yield Label("[$primary]Imandra CodeLogician, version 1.0")
        yield Footer()


if __name__ == '__main__':
    pass