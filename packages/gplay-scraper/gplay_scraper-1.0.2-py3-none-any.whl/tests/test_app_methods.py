import unittest
from gplay_scraper import GPlayScraper


class TestAppMethods(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.scraper = GPlayScraper()
        cls.app_id = "com.whatsapp"
        cls.lang = "en"
        cls.country = "us"
    
    def test_app_analyze(self):
        """Test app_analyze returns dictionary with data"""
        result = self.scraper.app_analyze(self.app_id, lang=self.lang, country=self.country)
        self.assertIsInstance(result, dict)
        self.assertIn('title', result)
        self.assertIn('score', result)
    
    def test_app_get_field(self):
        """Test app_get_field returns single field value"""
        result = self.scraper.app_get_field(self.app_id, "title", lang=self.lang, country=self.country)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
    
    def test_app_get_fields(self):
        """Test app_get_fields returns multiple fields"""
        fields = ["title", "score", "installs"]
        result = self.scraper.app_get_fields(self.app_id, fields, lang=self.lang, country=self.country)
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), len(fields))
        for field in fields:
            self.assertIn(field, result)
    
    def test_app_print_field(self):
        """Test app_print_field executes without error"""
        try:
            self.scraper.app_print_field(self.app_id, "title", lang=self.lang, country=self.country)
        except Exception as e:
            self.fail(f"app_print_field raised {type(e).__name__}: {e}")
    
    def test_app_print_fields(self):
        """Test app_print_fields executes without error"""
        try:
            self.scraper.app_print_fields(self.app_id, ["title", "score"], lang=self.lang, country=self.country)
        except Exception as e:
            self.fail(f"app_print_fields raised {type(e).__name__}: {e}")
    
    def test_app_print_all(self):
        """Test app_print_all executes without error"""
        try:
            self.scraper.app_print_all(self.app_id, lang=self.lang, country=self.country)
        except Exception as e:
            self.fail(f"app_print_all raised {type(e).__name__}: {e}")


if __name__ == '__main__':
    unittest.main()
