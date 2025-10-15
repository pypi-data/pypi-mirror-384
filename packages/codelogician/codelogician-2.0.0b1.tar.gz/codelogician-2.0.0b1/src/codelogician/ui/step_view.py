#
#   Imandra Inc.
#
#   step_view.py
#

from rich.text import Text
from textual.containers import VerticalGroup
from textual.widgets import (
    Collapsible,
    DataTable,
    Label,
    Pretty,
    Static,
    TabbedContent,
    TabPane,
)

def command_widget(command):
    args = command.model_dump(exclude={"type"})

    # Arguments table (if any)
    def do_args(args):
        max_width = 40
        yield Label("[b]Parameters:[/b]")

        # fmt: off
        def truncate(s): return s[:max_width - 3] + "..." if len(s) > max_width - 3 else s
        def fmt_list(l): return f"[{len(value)} items]" if l else "[]"
        def fmt_dict(l): return f"{{{len(value)} items}}" if l else "{}"
        def fmt_bool(t, f): return lambda b: f"[{t}]{b}[/{t}]" if b else f"[{f}]{b}[/{f}]"

        args_table = DataTable(show_header=False)
        for key, value in args.items():
            fmt = (truncate if isinstance(value, str) else
                   fmt_list if isinstance(value, list) else
                   fmt_dict if isinstance(value, dict) else
                   fmt_bool('bright_green','bright_red') if isinstance(value, bool) else
                   str)
            args_table.add_column("name")
            args_table.add_column("value")
            args_table.add_row(f"[dim]{key}:[/dim]", fmt(value))
        yield args_table
        # fmt: on

    cmd_name = command.type
    return VerticalGroup(
        Label(f"[b]Command: {cmd_name}[/b]"),
        *(do_args(args) if args else [Label("\n[dim]No parameters[/dim]")]),
    )


class TaskView(VerticalGroup):
    DEFAULT_CSS = """
        TaskView {
        border: round $foreground-muted;
        border-title-align: center;
        padding: 0 1 0 1;
        }"""

    def __init__(self, task):
        def trajectory_summary(formalizations):
            table = DataTable()  # title="Summary of Formalizations")
            table.add_column("#", width=2)
            table.add_column("Action", width=25)
            table.add_column("Status", width=15)
            table.add_column("Time", width=20)
            for i, f in enumerate(formalizations, 1):
                table.add_row(
                    str(i),
                    f.action,
                    f.fstate.status.__rich__(),
                    f.time_str,
                )
            yield table
            for f in formalizations:
                yield Static(f.__rich__())

        def formalizations_view(formalizations):
            with VerticalGroup():
                for i, f in enumerate(formalizations, 1):
                    title = (
                        Text(f"{i} {f.action} ")
                        + f.fstate.status.__rich__()
                        + Text(" " + f.time_str)
                    )
                    yield Collapsible(Static(f.__rich__()), title=title)

        def summary_parts():
            yield Static(Text("Status: ", "bold") + task.render_status())

            if task.precheck_failures:
                yield Static(
                    Text(
                        f"\nPrecheck Failures ({len(task.precheck_failures)}):",
                        style="bold bright_red",
                    )
                )
                for failure in task.precheck_failures:
                    yield Static(failure.__rich__())

            yield from trajectory_summary(task.formalizations)
            # yield from formalizations_view(task.formalizations)

            if task.hitl_qas:
                yield Static(
                    Text.assemble(
                        ("Human-in-the-Loop Interactions: ", "bold"),
                        (str(len(task.hitl_qas)), "bright_cyan"),
                    )
                )

            if task.metadata:
                yield Static(Text("Metadata: ", "bold"))
                yield Pretty(task.metadata)

        # Create panel
        VerticalGroup.__init__(self, *summary_parts())
        self.border_title = "Formalization Task"


class StepView(VerticalGroup):
    def __init__(self, step, *args, **kwargs):
        VerticalGroup.__init__(self, *args, **kwargs)
        self.step = step

    def compose(self):
        def response(i):
            response_type = i.response_type
            return {
                "Task": lambda: TaskView(i.task),
                "Message": lambda: Pretty(i.message),
            }[response_type]()

        with TabbedContent(initial="response"):
            with TabPane("Command", id="command"):
                yield command_widget(self.step.command.root)
            with TabPane("Response", id="response"):
                yield response(self.step)