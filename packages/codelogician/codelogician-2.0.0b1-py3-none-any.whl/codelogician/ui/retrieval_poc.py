#
#   Imandra Inc.
#
#   tui.py

from __future__ import annotations

import httpx, json
from typing import Iterable
from rich.syntax import Syntax
from rich.json import *

from textual import work

from textual.containers import Container, Horizontal, VerticalScroll
from textual.app import App, ComposeResult, SystemCommand
from textual.widgets import Header, Footer, Static
from textual.screen import Screen

from strategy.state import PyIMLStrategyState
from strategy.config import PyIMLConfig
from strategy.metamodel import MetaModel

class CodeLogician(App):
  """ Demonstrate a command source. """
  
  CSS_PATH = "tui.tcss"
  cont = True # trick we use for the background thread that updates info
  srcDir = "data/code2"

  def compose(self) -> ComposeResult:
    """ Compose """ 
    yield Header()
    
    with Container(id="app-grid"):
      with Horizontal(id="top-right"):
        yield Static(PyIMLStrategyState(""), id="strategy_state")
        yield Static(PyIMLConfig(), id="strategy_config")
      with VerticalScroll(id="metamodel"):
        yield Static(MetaModel(), id="metamodel")
      
    yield Footer()

  def cmd_autoformalize(self):
    """ command to run autoformalization """
    pass

  def cmd_stop_workers (self):
    """ """
    pass

  def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
    """ Let's try to organize this right now and here... """
    yield from super().get_system_commands(screen)

    # These are the commands that we can send to the strategy thread to affect formalization
    yield SystemCommand("ChangeMode"    , "Start autoformalization" , self.cmd_autoformalize  ) 
    yield SystemCommand("Stopworkers"   , "Stop all workers"        , self.cmd_stop_workers   )

  def on_ready(self) -> None:
    """ This is run at start-up """

    self.cl_server_update_retriever()
    self.set_interval(1, self.cl_server_update_retriever)

  @work()
  async def cl_server_update_retriever(self):    
    configWidget = self.query_one("#strategy_config", Static)

    try:
      data = httpx.get('http://127.0.0.1:8000/strategy/config')
      configObj = PyIMLConfig.fromJSON(json.loads(data.text.strip("'")))
      configWidget.update(configObj)
    except Exception as e:
      configWidget.update(f"Error: {str(e)}")
      print (f"Failed to get any data: {str(e)} ")
    
    # Let's update the strategy state now
    stratStateWidget = self.query_one("#strategy_state", Static)

    try:
      data = httpx.get('http://127.0.0.1:8000/strategy/state')
      stateObj = PyIMLStrategyState.fromJSON(json.loads(data.text.strip("'")))
      stratStateWidget.update(stateObj)
    except Exception as e:
      stratStateWidget.update(f"Error: {str(e)}")
      print (f"Failed to update strategy state widget: {str(e)}")
    
    # Now let's update the metamodel
    metamodelWidget = self.query_one("#metamodel", Static)
    try:
      data = httpx.get('http://127.0.0.1:8000/metamodel/latest')
      metaModelObj = MetaModel.fromJSON(self.srcDir, json.loads(data.text.strip("'")))
      metamodelWidget.update(metaModelObj)
    except Exception as e:
      metamodelWidget.update(f"error: {str(e)}")
      print (f"Failed to update the metamodel widget: {str(e)}")

  def on_unmount(self) -> None:
    self.cont = False

if __name__ == "__main__":
  app = CodeLogician()
  app.run()
