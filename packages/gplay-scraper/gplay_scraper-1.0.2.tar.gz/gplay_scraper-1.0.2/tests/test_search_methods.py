"""
Unit tests for Search Methods
"""

import unittest
from gplay_scraper import GPlayScraper


class TestSearchMethods(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.scraper = GPlayScraper()
        cls.query = "social media"
        cls.count = 10
        cls.lang = "en"
        cls.country = "us"
    
    def test_search_analyze(self):
        """Test search_analyze returns list of results"""
        result = self.scraper.search_analyze(self.query, count=self.count, lang=self.lang, country=self.country)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIn('title', result[0])
    
    def test_search_get_field(self):
        """Test search_get_field returns list of field values"""
        result = self.scraper.search_get_field(self.query, "title", count=self.count, lang=self.lang, country=self.country)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
    
    def test_search_get_fields(self):
        """Test search_get_fields returns list of dictionaries"""
        fields = ["title", "score"]
        result = self.scraper.search_get_fields(self.query, fields, count=self.count, lang=self.lang, country=self.country)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        for field in fields:
            self.assertIn(field, result[0])
    
    def test_search_print_field(self):
        """Test search_print_field executes without error"""
        try:
            self.scraper.search_print_field(self.query, "title", count=5, lang=self.lang, country=self.country)
        except Exception as e:
            self.fail(f"search_print_field raised {type(e).__name__}: {e}")
    
    def test_search_print_fields(self):
        """Test search_print_fields executes without error"""
        try:
            self.scraper.search_print_fields(self.query, ["title", "score"], count=5, lang=self.lang, country=self.country)
        except Exception as e:
            self.fail(f"search_print_fields raised {type(e).__name__}: {e}")
    
    def test_search_print_all(self):
        """Test search_print_all executes without error"""
        try:
            self.scraper.search_print_all(self.query, count=5, lang=self.lang, country=self.country)
        except Exception as e:
            self.fail(f"search_print_all raised {type(e).__name__}: {e}")


if __name__ == '__main__':
    unittest.main()
