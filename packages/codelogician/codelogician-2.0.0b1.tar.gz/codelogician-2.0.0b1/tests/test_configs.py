#
#   Imandra Inc.
#
#   test_configs.py
#

from codelogician.server.config import ServerConfig
from codelogician.strategy.config import StratConfig
import unittest


class TestConfigStuff(unittest.TestCase):
  """ TestConfigStuff """

  def test_Load(self):
    """ Test that we can successfully load a configuration """
    path = "data/tests/pyiml_config.yaml"
    config = StratConfig.fromYAML(path)

    assert config

class TestServerConfig(unittest.TestCase):
  """  """

  def test_Load (self):
    path = "data/tests/server_config.yaml"
    config = ServerConfig.fromYAML(path)
    
    print (config)

if __name__ == "__main__":
  unittest.main()