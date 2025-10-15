from __future__ import annotations

from functools import partial
from pathlib import Path

from textual.app import App, ComposeResult
from textual.command import Hit, Hits, Provider
from textual.containers import VerticalScroll
from textual.widgets import Static


class ViewCommandsProvider(Provider):
    """ A command provider for viewing model data """

    async def search(self, query : str) -> Hits:
        """ Search for appropriate server commands """

        matcher = self.matcher (query)

        


class ServerCommandsProvider(Provider):
    """ A command provider for sending commands to the server """

    async def search(self, query : str) -> Hits:
        """ Search for appropriate server commands """

        matcher = self.matcher(query)

        commands = [
            'autoformalize',
        ]
        for cmd in commands:
            command = f"cmd cl {cmd}"
            score = matcher.match(command)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(command),
                    partial(self.app.execute_server_command, command),
                    help = "Autoformalize is doing this!"
                )


class ModelCommandsProvider(Provider):
    """A command provider to open a Python file in the current working directory."""

    async def search(self, query: str) -> Hits:  
        """Search for Python files."""
        matcher = self.matcher(query)  

        model_paths = ['one.py', 'two.py', 'three.py', 'one/one.py', 'one/seven.py', 'two/three/four/five.py']

        app = self.app
        assert isinstance(app, ViewerApp)

        cmds = ['autoformalize', 'set_context', 'something else']

        for path in model_paths:
            for cmd in cmds:
                command = f"cmd model {cmd} {path}"
                score = matcher.match(command)
                if score > 0:
                    yield Hit(
                        score,
                        matcher.highlight(command),
                        partial(self.app.execute_model_command, cmd, path),
                        help = "Help about model commands!"
                    )

class ViewerApp(App):
    """Demonstrate a command source."""

    COMMANDS = App.COMMANDS | {ServerCommandsProvider} | {ModelCommandsProvider}

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(id="code", expand=True)

    def execute_server_command (self, cmd : str) -> None:
        """ We should execute server command here """
        pass

    def execute_model_command (self, cmd : str, path : Path) -> None:
        """ We should execute a command model. """
        pass

    def open_file(self, path: Path) -> None:
        """Open and display a file with syntax highlighting."""
        from rich.syntax import Syntax

        syntax = Syntax.from_path(
            str(path),
            line_numbers=True,
            word_wrap=False,
            indent_guides=True,
            theme="github-dark",
        )
        self.query_one("#code", Static).update(syntax)


if __name__ == "__main__":
    app = ViewerApp()
    app.run()