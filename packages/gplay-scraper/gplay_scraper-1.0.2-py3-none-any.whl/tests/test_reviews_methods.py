"""
Unit tests for Reviews Methods
"""

import unittest
from gplay_scraper import GPlayScraper


class TestReviewsMethods(unittest.TestCase):
    """Test suite for reviews methods."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.scraper = GPlayScraper()
        self.app_id = "com.whatsapp"  # WhatsApp app ID for testing
    
    def test_reviews_analyze(self):
        """Test reviews_analyze returns list of reviews."""
        result = self.scraper.reviews_analyze(self.app_id, count=10)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
    
    def test_reviews_get_field(self):
        """Test reviews_get_field returns list of field values."""
        result = self.scraper.reviews_get_field(self.app_id, "userName", count=5)
        self.assertIsInstance(result, list)
    
    def test_reviews_get_fields(self):
        """Test reviews_get_fields returns list of dictionaries."""
        result = self.scraper.reviews_get_fields(self.app_id, ["userName", "score"], count=5)
        self.assertIsInstance(result, list)
    
    def test_reviews_print_field(self):
        """Test reviews_print_field executes without error."""
        try:
            self.scraper.reviews_print_field(self.app_id, "userName", count=5)
        except Exception as e:
            self.fail(f"reviews_print_field raised {e}")
    
    def test_reviews_print_fields(self):
        """Test reviews_print_fields executes without error."""
        try:
            self.scraper.reviews_print_fields(self.app_id, ["userName", "score"], count=5)
        except Exception as e:
            self.fail(f"reviews_print_fields raised {e}")
    
    def test_reviews_print_all(self):
        """Test reviews_print_all executes without error."""
        try:
            self.scraper.reviews_print_all(self.app_id, count=5)
        except Exception as e:
            self.fail(f"reviews_print_all raised {e}")

if __name__ == '__main__':
    unittest.main()
