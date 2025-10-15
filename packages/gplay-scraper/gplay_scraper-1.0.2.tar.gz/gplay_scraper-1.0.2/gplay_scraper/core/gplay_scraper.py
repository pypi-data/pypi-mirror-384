import json
import re
import logging
from typing import Dict
from ..utils.http_client import HttpClient
from ..config import Config
from ..exceptions import DataParsingError, InvalidAppIdError
from urllib.parse import quote

logger = logging.getLogger(__name__)


class AppScraper:
    """Scraper for fetching app details from Google Play Store."""
    
    def __init__(self, rate_limit_delay: float = None, http_client: str = None):
        """Initialize AppScraper with HTTP client.
        
        Args:
            rate_limit_delay: Delay between requests
            http_client: HTTP client name
        """
        self.http_client = HttpClient(rate_limit_delay, http_client)

    def fetch_playstore_page(self, app_id: str, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> str:
        """Fetch app page HTML from Google Play Store.
        
        Args:
            app_id: Google Play app ID
            lang: Language code
            country: Country code
            
        Returns:
            HTML content of app page
        """
        return self.http_client.fetch_app_page(app_id, lang, country)

    def scrape_play_store_data(self, app_id: str, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> Dict:
        """Extract dataset from app page HTML.
        
        Args:
            app_id: Google Play app ID
            lang: Language code
            country: Country code
            
        Returns:
            Dictionary containing ds:5 dataset
            
        Raises:
            DataParsingError: If dataset not found
        """
        html_content = self.fetch_playstore_page(app_id, lang, country)
        
        ds_match = re.search(r'AF_initDataCallback\s*\(\s*({\s*key:\s*["\']ds:5["\'][\s\S]*?})\s*\)\s*;', html_content, re.DOTALL)
        if ds_match:
            ds5_data = ds_match.group(1)
        else:
            all_callbacks = re.findall(r'AF_initDataCallback\s*\(\s*({[\s\S]*?})\s*\)\s*;', html_content, re.DOTALL)
            ds5_data = ""
            for callback in all_callbacks:
                if "'ds:5'" in callback or '"ds:5"' in callback:
                    ds5_data = callback
                    break
        
        if not ds5_data:
            raise DataParsingError(Config.ERROR_MESSAGES["DS5_NOT_FOUND"])
        
        return {"ds:5": ds5_data}


class SearchScraper:
    """Scraper for fetching search results from Google Play Store."""
    
    def __init__(self, rate_limit_delay: float = None, http_client: str = None):
        """Initialize SearchScraper with HTTP client."""
        self.http_client = HttpClient(rate_limit_delay, http_client)

    def fetch_playstore_search(self, query: str, count: int, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> str:
        """Fetch search page HTML from Google Play Store.
        
        Args:
            query: Search query string
            count: Number of results needed
            lang: Language code
            country: Country code
            
        Returns:
            HTML content of search page
            
        Raises:
            InvalidAppIdError: If query is invalid
        """
        if not query or not isinstance(query, str):
            raise InvalidAppIdError(Config.ERROR_MESSAGES["INVALID_QUERY"])
        
        if count <= 0:
            return ""
        
        return self.http_client.fetch_search_page(query, lang, country)

    def scrape_play_store_data(self, html_content: str) -> Dict:
        """Extract datasets from search page HTML.
        
        Args:
            html_content: HTML content of search page
            
        Returns:
            Dictionary containing all datasets
            
        Raises:
            DataParsingError: If no datasets found
        """
        script_regex = re.compile(r"AF_initDataCallback[\s\S]*?</script")
        key_regex = re.compile(r"(ds:.*?)'")
        value_regex = re.compile(r"data:([\s\S]*?), sideChannel: {}}\);</")
        
        matches = script_regex.findall(html_content)
        dataset = {}
        
        for match in matches:
            key_match = key_regex.findall(match)
            value_match = value_regex.findall(match)
            
            if key_match and value_match:
                key = key_match[0]
                try:
                    value = json.loads(value_match[0])
                    dataset[key] = value
                except json.JSONDecodeError:
                    continue
        
        if not dataset:
            raise DataParsingError(Config.ERROR_MESSAGES["NO_DS5_DATA"])
        
        return dataset


class ReviewsScraper:
    """Scraper for fetching user reviews from Google Play Store."""
    
    # Sort order mapping
    SORT_NAMES = {
        'RELEVANT': 1,  # Most relevant reviews
        'NEWEST': 2,    # Newest reviews first
        'RATING': 3     # Sorted by rating
    }
    
    def __init__(self, rate_limit_delay: float = None, http_client: str = None):
        """Initialize ReviewsScraper with HTTP client."""
        self.http_client = HttpClient(rate_limit_delay, http_client)

    def fetch_reviews_batch(self, app_id: str, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY, 
                           sort: int = Config.DEFAULT_REVIEWS_SORT, batch_count: int = Config.DEFAULT_REVIEWS_BATCH_SIZE, token: str = None) -> str:
        """Fetch single batch of reviews from API.
        
        Args:
            app_id: Google Play app ID
            lang: Language code
            country: Country code
            sort: Sort order (NEWEST, RELEVANT, RATING)
            batch_count: Number of reviews per batch
            token: Pagination token for next batch
            
        Returns:
            Raw API response content
        """
        sort_value = self.SORT_NAMES.get(sort, sort) if isinstance(sort, str) else sort
        return self.http_client.fetch_reviews_batch(app_id, lang, country, sort_value, batch_count, token)

    def scrape_reviews_data(self, app_id: str, count: int = Config.DEFAULT_REVIEWS_COUNT, lang: str = Config.DEFAULT_LANGUAGE, 
                           country: str = Config.DEFAULT_COUNTRY, sort: int = Config.DEFAULT_REVIEWS_SORT) -> Dict:
        """Scrape multiple batches of reviews.
        
        Args:
            app_id: Google Play app ID
            count: Total number of reviews to fetch
            lang: Language code
            country: Country code
            sort: Sort order
            
        Returns:
            Dictionary containing all review responses
        """
        all_responses = []
        token = None
        batch_size = Config.DEFAULT_REVIEWS_BATCH_SIZE
        
        while len(all_responses) * batch_size < count:
            remaining = count - (len(all_responses) * batch_size)
            fetch_count = min(batch_size, remaining)
            
            response = self.fetch_reviews_batch(app_id, lang, country, sort, fetch_count, token)
            
            if not response:
                break
                
            all_responses.append(response)
            
            try:
                regex = re.compile(r"\)]}'\n\n([\s\S]+)")
                matches = regex.findall(response)
                if matches:
                    data = json.loads(matches[0])
                    token = json.loads(data[0][2])[-2][-1]
                    if not token or isinstance(token, list):
                        break
            except (json.JSONDecodeError, IndexError, KeyError):
                break
        
        return {"reviews": all_responses}


class DeveloperScraper:
    """Scraper for fetching developer portfolio from Google Play Store."""
    
    def __init__(self, rate_limit_delay: float = None, http_client: str = None):
        """Initialize DeveloperScraper with HTTP client."""
        self.http_client = HttpClient(rate_limit_delay, http_client)

    def fetch_developer_page(self, dev_id: str, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> str:
        """Fetch developer page HTML from Google Play Store.
        
        Args:
            dev_id: Developer ID (numeric or string)
            lang: Language code
            country: Country code
            
        Returns:
            HTML content of developer page
        """
        return self.http_client.fetch_developer_page(dev_id, lang, country)

    def scrape_play_store_data(self, dev_id: str, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> Dict:
        """Extract dataset from developer page HTML.
        
        Args:
            dev_id: Developer ID
            lang: Language code
            country: Country code
            
        Returns:
            Dictionary containing ds:3 dataset and dev_id
            
        Raises:
            DataParsingError: If dataset not found
        """
        html_content = self.fetch_developer_page(dev_id, lang, country)
        
        ds_match = re.search(r'AF_initDataCallback\s*\(\s*({\s*key:\s*["\']ds:3["\'][\s\S]*?})\s*\)\s*;', html_content, re.DOTALL)
        if ds_match:
            ds3_data = ds_match.group(1)
        else:
            all_callbacks = re.findall(r'AF_initDataCallback\s*\(\s*({[\s\S]*?})\s*\)\s*;', html_content, re.DOTALL)
            ds3_data = ""
            for callback in all_callbacks:
                if "'ds:3'" in callback or '"ds:3"' in callback:
                    ds3_data = callback
                    break
        
        if not ds3_data:
            raise DataParsingError(Config.ERROR_MESSAGES["DS3_NOT_FOUND"])
        
        return {"ds:3": ds3_data, "dev_id": dev_id}


class SimilarScraper:
    """Scraper for fetching similar apps from Google Play Store."""
    
    def __init__(self, rate_limit_delay: float = None, http_client: str = None):
        """Initialize SimilarScraper with HTTP client."""
        self.http_client = HttpClient(rate_limit_delay, http_client)

    def fetch_similar_page(self, app_id: str, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> str:
        """Fetch app page HTML to extract similar apps cluster URL.
        
        Args:
            app_id: Google Play app ID
            lang: Language code
            country: Country code
            
        Returns:
            HTML content of app page
        """
        return self.http_client.fetch_app_page(app_id, lang, country)

    def scrape_play_store_data(self, app_id: str, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> Dict:
        """Extract similar apps dataset from cluster page.
        
        Args:
            app_id: Google Play app ID
            lang: Language code
            country: Country code
            
        Returns:
            Dictionary containing ds:3 dataset
            
        Raises:
            DataParsingError: If dataset not found
        """
        html_content = self.fetch_similar_page(app_id, lang, country)
        
        # Extract cluster URL from app page
        pattern1 = r'&quot;(/store/apps/collection/cluster\?gsr=[^&]+)&quot;'
        matches1 = re.findall(pattern1, html_content)
        pattern2 = r'"(/store/apps/collection/cluster\?gsr=[^"]+)"'
        matches2 = re.findall(pattern2, html_content)
        all_matches = list(set(matches1 + matches2))
        
        if not all_matches:
            return {"ds:3": None}
        
        cluster_url = all_matches[0].replace('&amp;', '&')
        cluster_html = self.http_client.fetch_cluster_page(cluster_url, lang, country)
        
        ds_match = re.search(r'AF_initDataCallback\s*\(\s*({\s*key:\s*["\']ds:3["\'][\s\S]*?})\s*\)\s*;', cluster_html, re.DOTALL)
        if ds_match:
            ds3_data = ds_match.group(1)
        else:
            all_callbacks = re.findall(r'AF_initDataCallback\s*\(\s*({[\s\S]*?})\s*\)\s*;', cluster_html, re.DOTALL)
            ds3_data = ""
            for callback in all_callbacks:
                if "'ds:3'" in callback or '"ds:3"' in callback:
                    ds3_data = callback
                    break
        
        if not ds3_data:
            raise DataParsingError(Config.ERROR_MESSAGES["DS3_NOT_FOUND"])
        
        return {"ds:3": ds3_data}


class ListScraper:
    """Scraper for fetching top charts from Google Play Store."""

    # Collection name mapping
    CLUSTER_NAMES = {
        'TOP_FREE': 'topselling_free',      # Top free apps
        'TOP_PAID': 'topselling_paid',      # Top paid apps
        'TOP_GROSSING': 'topgrossing'       # Top grossing apps
    }
    
    def __init__(self, rate_limit_delay: float = None, http_client: str = None):
        """Initialize ListScraper with HTTP client."""
        self.http_client = HttpClient(rate_limit_delay, http_client)

    def scrape_play_store_data(self, collection: str, category: str = Config.DEFAULT_LIST_CATEGORY, count: int = Config.DEFAULT_LIST_COUNT, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> Dict:
        """Scrape top charts data from Google Play Store.
        
        Args:
            collection: Collection type (TOP_FREE, TOP_PAID, TOP_GROSSING)
            category: App category (e.g., GAME, SOCIAL)
            count: Number of apps to fetch
            lang: Language code
            country: Country code
            
        Returns:
            Dictionary containing collection data
            
        Raises:
            DataParsingError: If JSON parsing fails
        """
        cluster = self.CLUSTER_NAMES.get(collection, collection)
        response_text = self.http_client.fetch_list_page(cluster, category, count, lang, country)
        
        try:
            lines = response_text.strip().split('\n')
            data = json.loads(lines[2])
            collection_data = json.loads(data[0][2])
            return {"collection_data": collection_data}
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            raise DataParsingError(Config.ERROR_MESSAGES["JSON_PARSE_FAILED"].format(error=str(e)))


class SuggestScraper:
    """Scraper for fetching search suggestions from Google Play Store."""
    
    def __init__(self, rate_limit_delay: float = None, http_client: str = None):
        """Initialize SuggestScraper with HTTP client."""
        self.http_client = HttpClient(rate_limit_delay, http_client)

    def scrape_suggestions(self, term: str, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> Dict:
        """Scrape search suggestions from Google Play Store.
        
        Args:
            term: Search term for suggestions
            lang: Language code
            country: Country code
            
        Returns:
            Dictionary containing list of suggestions
            
        Raises:
            DataParsingError: If JSON parsing fails
        """
        if not term:
            return {"suggestions": []}
        
        response_text = self.http_client.fetch_suggest_page(term, lang, country)
        
        try:
            input_data = json.loads(response_text[5:])
            data = json.loads(input_data[0][2])
            
            if data is None:
                return {"suggestions": []}
            
            suggestions = [s[0] for s in data[0][0]]
            return {"suggestions": suggestions}
        except (json.JSONDecodeError, IndexError, KeyError, TypeError) as e:
            raise DataParsingError(Config.ERROR_MESSAGES["JSON_PARSE_FAILED"].format(error=str(e)))

