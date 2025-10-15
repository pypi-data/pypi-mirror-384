# ruff: noqa: E501
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from rich.text import Text

from textual.widgets._header import HeaderIcon, HeaderTitle
from textual.screen import Screen
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Header, Static, Footer, Button
from textual.widgets._header import HeaderIcon, HeaderTitle
from textual.containers import ScrollableContainer, HorizontalGroup, VerticalGroup

from pydantic import BaseModel
from enum import Enum
from typing import Optional
import datetime

class Source(Enum):
    NoSource = 'No_source'
    Server = 'Server'
    Disk = 'Disk'

class Status(BaseModel):
    source : Source
    
    disk_loaded : Optional[bool] = None
    disk_error : Optional[str] = None
    disk_path : Optional[Path] = None

    server_addr : Optional[str] = "http://127.0.0.1:8000"
    server_last_update : Optional[datetime.datetime] = None
    server_error : Optional[str] = None

class TUIConfig(BaseModel):
    using_server : bool = False
    disk_source : str = "/"
    server_source : str = "localhost:8000"

class InfoScreen(Screen):
    def __init__(self, msg, screen_type = "error", name = None, id = None, classes = None):
        super().__init__(name, id, classes)
        self._msg = msg 
        self._type = screen_type

    def compose(self):
        yield MyHeader()

        # TODO This is just a placeholder - we should do more advanced conditional styling
        if self._type == 'error':
            yield Static (f"Error: {self._msg}")
        elif self._type == 'info':
            yield Static (f"Info: {self._msg}")
        else:
            yield Static (f"Scucess: {self._msg}")

        yield Button("Ok")
        yield Footer()
    
    def on_button_pressed(self, event):
        self.app.pop_screen()

class Border(Widget):
    # foreground-muted?
    DEFAULT_CSS = """Border {
        border: round $foreground;
        border-title-align: left;
        height: auto;
        overflow-x: auto;
        }"""

    def __init__(self, title, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
        if title:
            self.border_title = title


class HeaderStatus(Static):
    DEFAULT_CSS = "HeaderStatus { height: 100%; width: auto; dock: right; content-align: center middle; }"
    status = reactive("", layout=True)

    def render(self):
        from rich.text import Text

        return Text(self.status)


class MyHeader(Header):
    """  """
    status = reactive("foo")
    DEFAULT_CSS = "MyHeader { background: black }"
    
    def compose(self):
        """ """
        i = HeaderIcon().data_bind(Header.icon)
        i.styles.width = "auto"
        self.icon = Text.assemble((" OIO", "bold #3363FF"), (" IMANDRA", "bold #00C6CF"))
        yield i
        yield HeaderTitle()
        yield HeaderStatus().data_bind(MyHeader.status)

def opaques_rich(opaques, limit=None):
    from rich.table import Table

    header = Text(f"Opaque Functions ({len(opaques)}):", style="bold")
    table = Table(show_header=False, box=None, padding=(0, 1))
    for i, opa in enumerate(opaques[:limit], 1):
        num_assumptions = len(opa.assumptions) if hasattr(opa, "assumptions") else 0
        has_approx = hasattr(opa, "approximation") and opa.approximation is not None
        status_icon = (
            "[bright_green]✓[/bright_green]"
            if has_approx
            else "[bright_yellow]○[/bright_yellow]"
        )
        table.add_row(
            f"{i}.",
            f"{status_icon} {opa.opaque_func}",
            f"({num_assumptions} assumptions)",
        )
    if limit is not None and len(opaques) > limit:
        table.add_row("...", f"[dim]({len(opaques) - limit} more)[/dim]", "")

    return header, table


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
    from rich.pretty import Pretty

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
            "Result", HScroll(Static(Pretty(vg.res, overflow="ellipsis", no_wrap=True)))
        ),
    )

def text_read(f):
    with open(f) as s: return s.read()

def local_file(name):
    return Path(__file__).parent / name