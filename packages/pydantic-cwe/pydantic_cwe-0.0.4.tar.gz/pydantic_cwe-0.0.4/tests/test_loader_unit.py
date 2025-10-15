import unittest
from unittest.mock import patch, MagicMock

from pydantic_cwe.loader import Loader
from pydantic_cwe.models import WeaknessCatalog


class TestLoader(unittest.TestCase):
    """Unit tests for the Loader class."""

    @patch('pydantic_cwe.loader.Path.exists')
    @patch('pydantic_cwe.loader.etree.parse')
    def test_load(self, mock_parse, mock_exists):
        """Test that the loader correctly loads a catalog."""
        # Mock the file existence check
        mock_exists.return_value = True
        
        # Create a mock XML tree and root
        mock_root = MagicMock()
        mock_root.nsmap = {None: "test-namespace"}
        mock_root.attrib = {"Name": "Test Catalog", "Version": "1.0", "Date": "2023-01-01"}
        
        # Mock the XML parsing
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree
        
        # Mock the _xml_to_dict method to return a simple catalog structure
        with patch.object(Loader, '_xml_to_dict') as mock_xml_to_dict:
            mock_xml_to_dict.return_value = {
                "Name": "Test Catalog",
                "Version": "1.0",
                "Date": "2023-01-01",
                "Weaknesses": {
                    "Weakness": []
                }
            }
            
            # Create a loader and load the catalog
            loader = Loader()
            catalog = loader.load()
            
            # Check that the catalog was loaded correctly
            self.assertIsInstance(catalog, WeaknessCatalog)
            self.assertEqual(catalog.name, "Test Catalog")
            self.assertEqual(catalog.version, "1.0")
            self.assertEqual(catalog.date, "2023-01-01")
            self.assertEqual(len(catalog.weaknesses.weaknesses), 0)
            
            # Check that the methods were called with the correct arguments
            mock_exists.assert_called_once()
            mock_parse.assert_called_once()
            mock_xml_to_dict.assert_called_once_with(mock_root, "test-namespace")

    def test_file_not_found(self):
        """Test that the loader raises FileNotFoundError when the file doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            Loader("non_existent_file.xml")


if __name__ == "__main__":
    unittest.main()