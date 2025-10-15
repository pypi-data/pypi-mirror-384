# ruff: noqa: RUF012, E501
import imandra.u.agents.code_logician.command as cmd
from textual import on
from textual.app import App
from textual.binding import Binding
from textual.containers import HorizontalGroup, Vertical, VerticalGroup, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Input, Label, ListView, Select, Static

from ...strategy.model import Model

from ..common import MyHeader, Border

class AddCommand(Message):
    def __init__(self, command):
        self.command = command
        super().__init__()

class CommandForm(VerticalGroup):
    kind = reactive(None, recompose=True)

    DEFAULT_CSS = """
        #field { padding-left: 1 }
        #buttons { width: auto }
        #fields { padding-left: 1; padding-right: 1; }
        Markdown { margin-left: 0; margin-top: 1; height: auto }
        Button { margin-left: 1; }
        HorizontalGroup { margin-left: 1; margin-bottom: 0}
        VerticalScroll#md { height: auto; max-height: 45% }
        Input.invalid { border: tall $error 70%; }
        Input.invalid:focus { border: tall $error; }
        #command-result { display: none }
        #command-result.filled { display: block }
        #errors { height: 6; width: 1fr; padding-left: 1; margin-right: 1; margin-left: 1 }
        #errors.valid { border: round $success; }
        #errors.invalid { border: round $error; }
        """

    def compose(self):
        def cmd_editor(c):
            import textwrap
            import typing

            from pydantic_core import PydanticUndefined
            from rich.syntax import Syntax
            from rich.text import Text
            from textual.validation import Number
            from textual.widgets import Markdown, Pretty

            # fmt: off
            pl = {int: "Integer", str: "String", float: "Decimal number"}
            def str_of_type(t): return t.__name__ if isinstance(t, type) else str(t)
            def not_undef(x): return x != PydanticUndefined
            def field_placeholder(f):
                return []


            #return maybe_else(pl.get(f.annotation, ""), repr, guard(not_undef, f.default))
            # fmt: on

            fields = [(n, f) for n, f in c.model_fields.items() if n != "type"]

            with HorizontalGroup():
                with VerticalGroup(id="buttons"):
                    yield Button("Add", variant="primary", id="add")
                with VerticalScroll(id="errors"):
                    yield Pretty("", id="command-result")

            with VerticalScroll(id="md"):
                yield Markdown(textwrap.dedent(c.__doc__))

            if fields == []:
                yield Static("  (This command has no parameters.)")
            else:
                yield Label("  [b][$primary]Parameters[/][/b]")
                with VerticalScroll(id="fields"):
                    for name, field in fields:
                        with Border(Text(name, "bold")):
                            yield Markdown(field.description or "No description")
                            with VerticalGroup(id="field"):
                                with HorizontalGroup():
                                    req = "required" if field.is_required() else "optional"
                                    yield Label(Syntax(str_of_type(field.annotation), "Python"))
                                    yield Label(Text(f" ({req})", "dim"))
                                if type(field.annotation) is typing._LiteralGenericAlias:
                                    yield Select( [(v,v) for v in field.annotation.__args__], id=name)
                                else:
                                    #placeholder = field_placeholder(field)
                                    validator = Number() if field.annotation in [int, float] else []
                                    yield Input(
                                        placeholder="HELLO",
                                        validators=validator,
                                        validate_on=[],
                                        id=name,
                                    )

        if self.kind != None:  # noqa
            yield from cmd_editor(self.kind)

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed):
        print("---> Ignoring select event")
        event.stop()

    # @on(Input.Submitted)
    # def show_invalid_reasons(self, event: Input.Submitted):
    #     result = event.validation_result
    #     reasons = [] if result.is_valid else result.failure_descriptions
    #     # self.query_one("#errors").update(repr(reasons))

    @on(Button.Pressed)
    def build_command(self, event):
        from pydantic import ValidationError

        def input_(n):
            return self.query_one("#" + n, Input | Select)

        c = self.kind
        input_by_name = {n: input_(n) for n in c.model_fields if n != "type"}
        name_val_pairs = [(n, i.value) for n, i in input_by_name.items()]
        dict_val = {n: v for n, v in name_val_pairs if v != ""}
        w = self.query_one("#errors")
        r = self.query_one("#command-result")
        r.add_class("filled")
        for i in input_by_name.values():
            i.remove_class("invalid")
        try:
            command = c.model_validate(dict_val)
            r.update(command)
            w.border_title = "Valid"
            w.remove_class("invalid")
            w.add_class("valid")
            if event.button.id == "add":
                self.screen.post_message(AddCommand(command))
        except ValidationError as e:
            r.update(e)
            for err in e.errors():
                for n in err["loc"]:
                    input_by_name[n].add_class("invalid")

            w.border_title = "Error"
            w.remove_class("valid")
            w.add_class("invalid")


class CommandEditor(Vertical):
    DEFAULT_CSS = "Select { margin-bottom: 1 } CommandForm { height: 1fr }"

    def compose(self):
        command_classes = [
            cmd.AdmitModelCommand,
            cmd.AgentFormalizerCommand,
            cmd.CheckFormalizationCommand,
            cmd.EditStateElementCommand,
            cmd.GenFormalizationDataCommand,
            cmd.GenFormalizationFailureDataCommand,
            cmd.GenModelCommand,
            cmd.GenProgramRefactorCommand,
            cmd.GenRegionDecompsCommand,
            cmd.GenTestCasesCommand,
            cmd.GenVgsCommand,
            cmd.GetStateElementCommand,
            cmd.InitStateCommand,
            cmd.InjectFormalizationContextCommand,
            cmd.SearchFDBCommand,
            cmd.SetModelCommand,
            cmd.SuggestApproximationCommand,
            cmd.SuggestAssumptionsCommand,
            cmd.SuggestFormalizationActionCommand,
            cmd.SyncModelCommand,
            cmd.SyncSourceCommand,
        ]

        yield Select([(c.__name__, c) for c in command_classes])
        yield CommandForm(id="editor")

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed):
        editor = self.query_one("#editor")
        editor.kind = event.value
        #editor.kind = event: lambda x: x != Select.BLANK, event.value)


# fmt: off
def move_up(i, x):   return (i-1, [*x[:i-1], x[i], x[i-1], *x[i+1:]]) if i > 0        else (i, x)
def move_down(i, x): return (i+1, [*x[:i], x[i+1], x[i], *x[i+2:]])   if i < len(x)-1 else (i, x)
def rm_nth(i, x):    return (None, [*x[:i], *x[i+1:]])
def maybe_(f, i, x): return (i, x) if i is None else f(i, x)

class CommandsList(Vertical):
    DEFAULT_CSS = """Grid { grid-size: 3 1; height: auto }
    Button { border: none; min-width: 1; }"""
    class View(ListView):
        commands = reactive([], recompose=True)

        BINDINGS = [ Binding("backspace", "delete", "Delete", show=False)
                   , Binding("shift+up", "move_up", "Move up", show=False)
                   , Binding("shift+down", "move_down", "Move down", show=False) ]

        def action_delete(self):    self.index, self.commands = maybe_(rm_nth, self.index, self.commands)
        def action_move_up(self):   self.index, self.commands = maybe_(move_up, self.index, self.commands)
        def action_move_down(self): self.index, self.commands = maybe_(move_down, self.index, self.commands)

        def compose(self):
            from textual.widgets import ListItem
            for c in  self.commands:
                yield ListItem(Static(c.__rich__()))

    def on_mount(self): self.lv = self.query_one(CommandsList.View)

    def compose(self):
        from textual.containers import Grid
        with Grid():
            yield Button("move up", id="up")
            yield Button("move down", id="down")
            yield Button("delete", id="del")
        yield CommandsList.View()

    @on(Button.Pressed)
    def edit(self, event):
        { "del":  self.lv.action_delete
        , "up":   self.lv.action_move_up
        , "down": self.lv.action_move_down
        }[event.button.id]()

    def add_command(self, command):
        v = self.query_one(CommandsList.View)
        v.commands = [*v.commands, command]
# fmt: on


class ModelCommandsView(VerticalScroll):
    #DEFAULT_CSS = "Grid { grid-size: 2 1 }"

    def __init__(self, model:Model, container):
        super().__init__()
        self.styles.height = "auto"
        self.model = model
        self.container = container

    def compose(self):
        #from textual.containers import Grid

        with Vertical():
            yield CommandEditor()
            yield CommandsList(id="commands")

    @on(AddCommand)
    def add_command(self, event):
        commands = self.query_one("#commands")
        commands.add_command(event.command)

class TestApp(App):
    #MODES = { "model_commands": ModelCommandScreen }

    def compose(self):
        yield ModelCommandsView()

if __name__ == "__main__":

    TestApp().run()