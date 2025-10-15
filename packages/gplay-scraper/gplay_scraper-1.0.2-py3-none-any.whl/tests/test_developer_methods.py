"""
Unit tests for Developer Methods
"""

import unittest
from gplay_scraper import GPlayScraper


class TestDeveloperMethods(unittest.TestCase):
    """Test suite for developer methods."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.scraper = GPlayScraper()
        self.dev_id = "5700313618786177705"  # WhatsApp Inc. developer ID
    
    def test_developer_analyze(self):
        """Test developer_analyze returns list of apps."""
        result = self.scraper.developer_analyze(self.dev_id, count=10)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
    
    def test_developer_get_field(self):
        """Test developer_get_field returns list of field values."""
        result = self.scraper.developer_get_field(self.dev_id, "title", count=5)
        self.assertIsInstance(result, list)
    
    def test_developer_get_fields(self):
        """Test developer_get_fields returns list of dictionaries."""
        result = self.scraper.developer_get_fields(self.dev_id, ["title", "score"], count=5)
        self.assertIsInstance(result, list)
    
    def test_developer_print_field(self):
        """Test developer_print_field executes without error."""
        try:
            self.scraper.developer_print_field(self.dev_id, "title", count=5)
        except Exception as e:
            self.fail(f"developer_print_field raised {e}")
    
    def test_developer_print_fields(self):
        """Test developer_print_fields executes without error."""
        try:
            self.scraper.developer_print_fields(self.dev_id, ["title", "score"], count=5)
        except Exception as e:
            self.fail(f"developer_print_fields raised {e}")
    
    def test_developer_print_all(self):
        """Test developer_print_all executes without error."""
        try:
            self.scraper.developer_print_all(self.dev_id, count=5)
        except Exception as e:
            self.fail(f"developer_print_all raised {e}")

if __name__ == '__main__':
    unittest.main()
