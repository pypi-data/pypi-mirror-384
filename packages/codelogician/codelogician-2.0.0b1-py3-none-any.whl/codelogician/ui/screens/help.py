#
#   Imandra Inc.
#
#   help.py
#   

from textual.screen import Screen
from textual.widgets import Footer, MarkdownViewer
from ..common import MyHeader, text_read, local_file

class HelpScreen(Screen):
    def __init__(self):
        Screen.__init__(self)
        self.title = "Help"

    def compose(self):
        yield MyHeader()
        text = text_read(local_file("data/help.md"))
        markdown_viewer = MarkdownViewer(text, show_table_of_contents=True)
        markdown_viewer.code_indent_guides = False
        yield markdown_viewer
        yield Footer()