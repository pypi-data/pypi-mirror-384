import unittest
from unittest.mock import patch, mock_open
import json
from traia_tools.index import get_traia_tools_index

class TestIndexRetriever(unittest.TestCase):
    def setUp(self):
        self.sample_tools_index = {
            "tool1": {
                "name": "Test Tool 1",
                "version": "1.0.0"
            },
            "tool2": {
                "name": "Test Tool 2",
                "version": "2.0.0"
            }
        }
        
    @patch('builtins.open', new_callable=mock_open)
    def test_get_index_success(self, mock_file):
        # Mock the file content
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(self.sample_tools_index)
        
        # Call the function
        result = get_traia_tools_index()
        
        # Verify the result
        self.assertEqual(result, self.sample_tools_index)
        
    @patch('builtins.open', new_callable=mock_open)
    def test_get_index_invalid_json(self, mock_file):
        # Mock invalid JSON content
        mock_file.return_value.__enter__.return_value.read.return_value = "invalid json"
        
        # Verify the function raises the correct error
        with self.assertRaises(json.JSONDecodeError):
            get_traia_tools_index()

if __name__ == '__main__':
    unittest.main() 