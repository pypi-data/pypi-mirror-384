"""
Unit tests for Similar Methods
"""

import unittest
from gplay_scraper import GPlayScraper


class TestSimilarMethods(unittest.TestCase):
    """Test suite for similar methods (find related apps)."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.scraper = GPlayScraper()
        self.app_id = "com.whatsapp"  # WhatsApp app ID for testing
    
    def test_similar_analyze(self):
        """Test similar_analyze returns list of similar apps."""
        result = self.scraper.similar_analyze(self.app_id, count=10)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
    
    def test_similar_get_field(self):
        """Test similar_get_field returns list of field values."""
        result = self.scraper.similar_get_field(self.app_id, "title", count=5)
        self.assertIsInstance(result, list)
    
    def test_similar_get_fields(self):
        """Test similar_get_fields returns list of dictionaries."""
        result = self.scraper.similar_get_fields(self.app_id, ["title", "score"], count=5)
        self.assertIsInstance(result, list)
    
    def test_similar_print_field(self):
        """Test similar_print_field executes without error."""
        try:
            self.scraper.similar_print_field(self.app_id, "title", count=5)
        except Exception as e:
            self.fail(f"similar_print_field raised {e}")
    
    def test_similar_print_fields(self):
        """Test similar_print_fields executes without error."""
        try:
            self.scraper.similar_print_fields(self.app_id, ["title", "score"], count=5)
        except Exception as e:
            self.fail(f"similar_print_fields raised {e}")
    
    def test_similar_print_all(self):
        """Test similar_print_all executes without error."""
        try:
            self.scraper.similar_print_all(self.app_id, count=5)
        except Exception as e:
            self.fail(f"similar_print_all raised {e}")

if __name__ == '__main__':
    unittest.main()
