#
#   Imandra Inc.
#
#   sketches.py
#

from textual.app import on, App, ComposeResult
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Placeholder, Footer, Static, ListView, ListItem, 
    TabbedContent, TabPane, Label, Select, Input, Button, Rule, TextArea
)
from textual.containers import Horizontal, Vertical
from codelogician.ui.common import Border, MyHeader
from rich.panel import Panel

from codelogician.strategy.sketch import (
    SketchContainer, 
    Sketch, 
    SketchState, 
)

class SketchScreen(Screen):
    """
    SketchScreen 
    """

    mmodel = reactive("", recompose=True)
    selected_sketch = reactive("")
    selected_sketch_state = reactive("")

    def __init__(self):
        """
        """
        Screen.__init__(self)

        self.mmodel = self.app.selected_strat_mmodel
        if self.mmodel:
            self.sketch_container = self.mmodel.sketches
        else:
            self.sketch_container = None

        self.selected_sketch = None
        self.selected_sketch_state = None
        self.title = "Sketches"

    def watch_selected_sketch(self):
        """
        Updated state of the selected sketch 
        """

        sk : Sketch = self.selected_sketch

        if not sk: return

        sketch_id = self.query_one("#sk_sketch_id")
        sketch_id.update(f"ID : {sk.sketch_id}")

        anchor_model_path = self.query_one("#sk_anchor_model_path")
        anchor_model_path.update(f"Anchor model: {sk.anchor_model_path}")

        processing = self.query_one("#sk_processing")
        processing.update(f"Is processing: {sk.processing}")

        state_list : ListView = self.query_one("#sketch_state_list_view", ListView)
        state_list.clear()
        state_id_items = [ListItem(Static(str(idx))) for idx in sk.state_ids()]
        state_list.extend(state_id_items)
        
        #if len(state_id_items):
        state_list.index = 0 # let's select the first one 

        # Let's also make sure that the next tab has 'Existing sketch' selected
        tabbed_view = self.query_one("#tabbed_content")
        tabbed_view.active = "tab_existing"

    def watch_selected_sketch_state(self):
        """
        Update the specific sketch state
        """

        state : SketchState = self.selected_sketch_state

        if not state: return

        state_id = self.query_one("#sketch_state_id")
        state_id.update(f"State id: {state.state_id}")

        state_change = self.query_one("#sketch_state_change")
        state_change.update(f"State change: {str(state.change)}")

        state_frm_status = self.query_one("#sketch_state_frm_status")
        state_frm_status.update(f"Formalization status: {str(state.status)}")

        state_error = self.query_one("#sketch_state_error")
        state_error.update(f"Error: {state.error if state.error else "N/A" }")
        
        state_iml_code = self.query_one("#sketch_state_iml")
        state_iml_code.text = state.iml_code

    def compose(self) -> ComposeResult:
        """
        """
        #yield MyHeader()
        
        with Horizontal() as h:
            h.styles.layout = "grid"
            h.styles.grid_size_columns = 2
            h.styles.grid_columns = "1fr 3fr"

            with Vertical():
                yield Static("Existing sketches:")
                if self.sketch_container:
                    if self.sketch_container.ids():
                        items = []
                        for sketch_id in self.sketch_container.ids():
                            items.append(ListItem(Label(sketch_id)))
                        yield (ListView(*items, id="sketch_list_view"))
                    else:
                        yield Static("N/A")
                else:
                    yield Static("N/A")

            with TabbedContent(id="tabbed_content"):
                with TabPane("Existing", id="tab_existing"):
                    with Vertical():
                        yield Static("ID: N/A", id="sk_sketch_id")
                        yield Static("Anchor model: N/A", id="sk_anchor_model_path")
                        yield Static("Is processing:  N/A", id="sk_processing")
                        with Horizontal():
                            yield ListView(id="sketch_state_list_view")
                            yield Rule("vertical")                            
                            with Vertical():
                                yield Static("State id: N/A", id="sketch_state_id")
                                yield Static("State id: N/A", id="sketch_state_change")
                                yield Static("Formalization status: N/A", id="sketch_state_frm_status")
                                yield Static("Error: N/A", id="sketch_state_error")
                                yield TextArea.code_editor(
                                    "N/A", 
                                    language=None,
                                    id="sketch_state_iml", 
                                    read_only=True
                                )

                with TabPane("Create new", id="tab_new"):
                    with Vertical():
                        yield Static("Select anchor model:")
                        yield Select("")
                        yield Input("Name")
                        yield Button("Create sketch", id="btn_create_sketch")

        #yield StatusBar()

    @on(ListView.Highlighted, "#sketch_state_list_view")
    def on_sketch_state_highlighted(self):
        lv = self.query_one("#sketch_state_list_view")
        idx = lv.index
        state = self.selected_sketch.get_state_by_idx(idx)

        if state:
            self.selected_sketch_state = state


    @on(ListView.Highlighted, "#sketch_list_view")
    def on_list_view_highlighted(self, event:ListView.Highlighted):
        """ An existing sketch has been selected from this """
        lv = self.query_one("#sketch_list_view")
        idx = lv.index
        sketch = list(self.sketch_container.sketches.values())[idx]
        self.selected_sketch = sketch

    @on(Button.Pressed, "#btn_create_sketch")
    def on_create_sketch(self):
        """ """
        anchor_model = self.query_one("#anchor_model")
        

class TestSketchesApp(App):
    """
    Minimalist setup to test out Sketches screen
    """

    SCREENS = {'sketches': SketchScreen}

    def __init__(self, sk):
        super().__init__()
        self.sk = sk
    def compose (self):
        yield SketchScreen()

    def on_mount(self):
        self.push_screen("sketches")


if __name__ == "__main__":

    import json
    with open("src/codelogician/data/sketches/sketch1.json") as inFile:
        j = json.load(inFile)
        sketchC = SketchContainer.fromJSON(j)

    app = TestSketchesApp(sketchC)
    app.run()
