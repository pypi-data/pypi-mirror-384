import unittest
import yaml
import sys
from unittest.mock import patch, mock_open

from dgraph_flex.dgraph_flex import DgraphFlex

class DgraphFlex2:
    def __init__(self, **kwargs):
        self.graph = {} # Initialize graph to avoid errors if not loaded

    def read_yaml(self, yamlpath, version=1.0):
        "read in the yaml config file"
        with open(yamlpath, 'r') as file:
            self.graph = yaml.safe_load(file)

        if self.graph['GENERAL']['version'] > version:
            print(f"Error: Supports up to {version}, this is version {self.graph['GENERAL']['version']}")
            sys.exit(1)

        return self.graph

class TestDgraphFlex(unittest.TestCase):

    @patch('sys.exit')
    def test_read_yaml_version_too_high(self, mock_exit):
        yaml_content = """
        GENERAL:
          version: 2.0
        """
        mock_file = mock_open(read_data=yaml_content)

        with patch("builtins.open", mock_file):
            dgraph_flex = DgraphFlex()
            dgraph_flex.read_yaml("dummy_path.yaml")

        mock_exit.assert_called_once_with(1)

    @patch('sys.exit')
    @patch('builtins.print')
    def test_read_yaml_version_too_high_print_correct_message(self, mock_print, mock_exit):
        yaml_content = """
        GENERAL:
          version: 2.0
        """
        mock_file = mock_open(read_data=yaml_content)

        with patch("builtins.open", mock_file):
            dgraph_flex = DgraphFlex()
            dgraph_flex.read_yaml("dummy_path.yaml")

        mock_print.assert_called_once_with("Error: Supports up to 1.0, this is version 2.0")
        mock_exit.assert_called_once_with(1)

    def test_read_yaml_version_ok(self):
        yaml_content = """
        GENERAL:
          version: 1.0
        """
        mock_file = mock_open(read_data=yaml_content)

        with patch("builtins.open", mock_file):
            dgraph_flex = DgraphFlex()
            result = dgraph_flex.read_yaml("dummy_path.yaml")

        self.assertEqual(result['GENERAL']['version'], 1.0)
        
    def test_read_yaml_version_lower(self):
        yaml_content = """
        GENERAL:
          version: 0.5
        """
        mock_file = mock_open(read_data=yaml_content)

        with patch("builtins.open", mock_file):
            dgraph_flex = DgraphFlex()
            result = dgraph_flex.read_yaml("dummy_path.yaml")

        self.assertEqual(result['GENERAL']['version'], 0.5)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)