"""
Unit tests for List Methods
"""

import unittest
from gplay_scraper import GPlayScraper


class TestListMethods(unittest.TestCase):
    """Test suite for list methods (top charts)."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.scraper = GPlayScraper()
        self.collection = "TOP_FREE"  # Top free apps collection
        self.category = "GAME"  # Game category
    
    def test_list_analyze(self):
        """Test list_analyze returns list of top apps."""
        result = self.scraper.list_analyze(self.collection, self.category, count=10)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
    
    def test_list_get_field(self):
        """Test list_get_field returns list of field values."""
        result = self.scraper.list_get_field(self.collection, self.category, "title", count=5)
        self.assertIsInstance(result, list)
    
    def test_list_get_fields(self):
        """Test list_get_fields returns list of dictionaries."""
        result = self.scraper.list_get_fields(self.collection, self.category, ["title", "score"], count=5)
        self.assertIsInstance(result, list)
    
    def test_list_print_field(self):
        """Test list_print_field executes without error."""
        try:
            self.scraper.list_print_field(self.collection, self.category, "title", count=5)
        except Exception as e:
            self.fail(f"list_print_field raised {e}")
    
    def test_list_print_fields(self):
        """Test list_print_fields executes without error."""
        try:
            self.scraper.list_print_fields(self.collection, self.category, ["title", "score"], count=5)
        except Exception as e:
            self.fail(f"list_print_fields raised {e}")
    
    def test_list_print_all(self):
        """Test list_print_all executes without error."""
        try:
            self.scraper.list_print_all(self.collection, self.category, count=5)
        except Exception as e:
            self.fail(f"list_print_all raised {e}")

if __name__ == '__main__':
    unittest.main()
