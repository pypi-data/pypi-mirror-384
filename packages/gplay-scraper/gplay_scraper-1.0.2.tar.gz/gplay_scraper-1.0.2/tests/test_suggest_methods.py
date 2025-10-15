"""
Unit tests for Suggest Methods
"""

import unittest
from gplay_scraper import GPlayScraper


class TestSuggestMethods(unittest.TestCase):
    """Test suite for suggest methods (search suggestions)."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.scraper = GPlayScraper()
        self.term = "fitness"  # Search term for testing
    
    def test_suggest_analyze(self):
        """Test suggest_analyze returns list of suggestions."""
        result = self.scraper.suggest_analyze(self.term, count=5)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
    
    def test_suggest_get_field(self):
        """Test suggest_get_field returns list of field values."""
        result = self.scraper.suggest_get_field(self.term, "term", count=5)
        self.assertIsInstance(result, list)
    
    def test_suggest_print_field(self):
        """Test suggest_print_field executes without error."""
        try:
            self.scraper.suggest_print_field(self.term, "term", count=5)
        except Exception as e:
            self.fail(f"suggest_print_field raised {e}")
    
    def test_suggest_print_all(self):
        """Test suggest_print_all executes without error."""
        try:
            self.scraper.suggest_print_all(self.term, count=5)
        except Exception as e:
            self.fail(f"suggest_print_all raised {e}")

if __name__ == '__main__':
    unittest.main()
