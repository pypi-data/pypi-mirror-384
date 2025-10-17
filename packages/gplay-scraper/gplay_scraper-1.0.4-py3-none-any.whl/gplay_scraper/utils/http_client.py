"""HTTP client with support for 7 different libraries and automatic fallback.

This module provides a unified HTTP client interface that supports:
- requests
- curl_cffi
- tls_client
- httpx
- urllib3
- cloudscraper
- aiohttp

With automatic fallback if the primary client fails.
"""

import time
import logging
from typing import Optional
from urllib.parse import quote

from ..config import Config
from ..exceptions import AppNotFoundError, NetworkError

logger = logging.getLogger(__name__)

class HttpClient:
    """HTTP client with automatic fallback support for 7 libraries."""
    def __init__(self, rate_limit_delay: float = None, client_type: str = None):
        """Initialize HTTP client with specified or default client type.
        
        Args:
            rate_limit_delay: Delay between requests in seconds
            client_type: HTTP client to use (requests, curl_cffi, tls_client, etc.)
        """
        self.headers = Config.get_headers()
        self.timeout = Config.DEFAULT_TIMEOUT
        self.rate_limit_delay = rate_limit_delay or Config.RATE_LIMIT_DELAY
        self.last_request_time = 0
        self.client_type = client_type or Config.DEFAULT_HTTP_CLIENT
        self._setup_client()
    
    def _setup_client(self):
        """Setup HTTP client based on client_type with automatic fallback."""
        # Try to initialize the specified client, fallback to next if unavailable
        if self.client_type == "requests" or self.client_type is None:
            self._try_requests()
        elif self.client_type == "curl_cffi":
            self._try_curl_cffi()
        elif self.client_type == "tls_client":
            self._try_tls_client()
        elif self.client_type == "urllib3":
            self._try_urllib3()
        elif self.client_type == "cloudscraper":
            self._try_cloudscraper()
        elif self.client_type == "aiohttp":
            self._try_aiohttp()
        elif self.client_type == "httpx":
            self._try_httpx()
        else:
            self._try_requests()
    
    def _try_requests(self):
        """Try to initialize requests client, fallback to curl_cffi if unavailable."""
        try:
            import requests
            self.client = requests
            self.client_type = "requests"
        except ImportError:
            self._try_curl_cffi()
    
    def _try_curl_cffi(self):
        """Try to initialize curl_cffi client, fallback to tls_client if unavailable."""
        try:
            from curl_cffi import requests as curl_requests
            self.client = curl_requests.Session(impersonate="chrome110")
            self.client_type = "curl_cffi"
        except ImportError:
            self._try_tls_client()
    
    def _try_tls_client(self):
        """Try to initialize tls_client, fallback to urllib3 if unavailable."""
        try:
            import tls_client
            self.client = tls_client.Session(
                client_identifier="chrome112",
                random_tls_extension_order=True
            )
            self.client_type = "tls_client"
        except ImportError:
            self._try_urllib3()
    
    def _try_urllib3(self):
        """Try to initialize urllib3 client, fallback to cloudscraper if unavailable."""
        try:
            import urllib3
            self.client = urllib3.PoolManager()
            self.client_type = "urllib3"
        except ImportError:
            self._try_cloudscraper()
    
    def _try_cloudscraper(self):
        """Try to initialize cloudscraper client, fallback to aiohttp if unavailable."""
        try:
            import cloudscraper
            self.client = cloudscraper.create_scraper()
            self.client_type = "cloudscraper"
        except ImportError:
            self._try_aiohttp()

    def _try_aiohttp(self):
        """Try to initialize aiohttp client, fallback to httpx if unavailable."""
        try:
            import aiohttp
            self.client = aiohttp
            self.client_type = "aiohttp"
        except ImportError:
            self._try_httpx()
    
    def _try_httpx(self):
        """Try to initialize httpx client, raise error if unavailable."""
        try:
            import httpx
            self.client = httpx.Client(timeout=self.timeout)
            self.client_type = "httpx"
        except ImportError:
            raise ImportError(Config.ERROR_MESSAGES["NO_HTTP_CLIENT"])
    
    def fetch_app_page(self, app_id: str, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> str:
        """Fetch app details page from Google Play Store.
        
        Args:
            app_id: Google Play app ID
            lang: Language code
            country: Country code
            
        Returns:
            HTML content of app page
            
        Raises:
            AppNotFoundError: If app not found
            NetworkError: If request fails
        """
        self.rate_limit()
        
        url = f"{Config.PLAY_STORE_BASE_URL}{Config.APP_DETAILS_ENDPOINT}?id={app_id}&hl={lang}&gl={country}"
        
        try:
            response = self._make_request("GET", url)
            return response.text
        except Exception as e:
            if self._is_404_error(e):
                raise AppNotFoundError(Config.ERROR_MESSAGES["APP_NOT_FOUND"].format(app_id=app_id))
            # Retry without country parameter
            url = f"{Config.PLAY_STORE_BASE_URL}{Config.APP_DETAILS_ENDPOINT}?id={app_id}&hl={lang}"
            try:
                response = self._make_request("GET", url)
                return response.text
            except Exception as e2:
                if self._is_404_error(e2):
                    raise AppNotFoundError(Config.ERROR_MESSAGES["APP_NOT_FOUND"].format(app_id=app_id))
                logger.error(Config.ERROR_MESSAGES["APP_FETCH_FAILED"].format(app_id=app_id, error=e))
                raise NetworkError(Config.ERROR_MESSAGES["APP_FETCH_FAILED"].format(app_id=app_id, error=e))
    
    def fetch_app_page_no_locale(self, app_id: str) -> str:
        """Fetch app page without hl/gl parameters for fallback data.
        
        Args:
            app_id: Google Play app ID
            
        Returns:
            HTML content of app page
        """
        self.rate_limit()
        
        url = f"{Config.PLAY_STORE_BASE_URL}{Config.APP_DETAILS_ENDPOINT}?id={app_id}"
        
        try:
            response = self._make_request("GET", url)
            return response.text
        except Exception as e:
            logger.error(f"Fallback fetch failed for {app_id}: {e}")
            return ""

    def fetch_search_page(self, query: str = None, token: str = None, needed: int = None, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> str:
        """Fetch search results from Google Play Store (initial or paginated).
        
        Args:
            query: Search query string (for initial search)
            token: Pagination token (for paginated search)
            needed: Number of results needed (for pagination)
            lang: Language code
            country: Country code
            
        Returns:
            HTML content (initial) or raw API response (pagination)
            
        Raises:
            AppNotFoundError: If search fails
            NetworkError: If request fails
        """
        self.rate_limit()
        
        # Pagination request
        if token and needed:
            url = f"{Config.PLAY_STORE_BASE_URL}/_/PlayStoreUi/data/batchexecute"
            params = f"rpcids=qnKhOb&source-path=%2Fwork%2Fsearch&hl={lang}&gl={country}"
            
            body = f'f.req=%5B%5B%5B%22qnKhOb%22%2C%22%5B%5Bnull%2C%5B%5B10%2C%5B10%2C{needed}%5D%5D%2Ctrue%2Cnull%2C%5B96%2C27%2C4%2C8%2C57%2C30%2C110%2C79%2C11%2C16%2C49%2C1%2C3%2C9%2C12%2C104%2C55%2C56%2C51%2C10%2C34%2C77%5D%5D%2Cnull%2C%5C%22{token}%5C%22%5D%5D%22%2Cnull%2C%22generic%22%5D%5D%5D'
            
            headers = {
                **self.headers,
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
            }
            
            try:
                response = self._make_request("POST", f"{url}?{params}", data=body, headers=headers)
                return response.text
            except Exception as e:
                logger.error(Config.ERROR_MESSAGES["SEARCH_PAGINATION_FAILED"].format(error=e))
                raise NetworkError(Config.ERROR_MESSAGES["SEARCH_PAGINATION_FAILED"].format(error=e))
        
        # Initial search request
        elif query:
            encoded_query = quote(query)
            url = f"{Config.PLAY_STORE_BASE_URL}/work/search?q={encoded_query}&hl={lang}&gl={country}&price=0"
            
            try:
                response = self._make_request("GET", url)
                return response.text
            except Exception as e:
                if self._is_404_error(e):
                    raise AppNotFoundError(Config.ERROR_MESSAGES["SEARCH_NOT_FOUND"].format(query=query))
                url = f"{Config.PLAY_STORE_BASE_URL}/work/search?q={encoded_query}&hl={lang}&price=0"
                try:
                    response = self._make_request("GET", url)
                    return response.text
                except Exception as e2:
                    if self._is_404_error(e2):
                        raise AppNotFoundError(Config.ERROR_MESSAGES["SEARCH_NOT_FOUND"].format(query=query))
                    logger.error(Config.ERROR_MESSAGES["SEARCH_FETCH_FAILED"].format(query=query, error=e))
                    raise NetworkError(Config.ERROR_MESSAGES["SEARCH_FETCH_FAILED"].format(query=query, error=e))
        
        else:
            raise ValueError("Either query or (token and needed) must be provided")


    def fetch_reviews_batch(self, app_id: str, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY, 
                           sort: int = Config.DEFAULT_REVIEWS_SORT, batch_count: int = Config.DEFAULT_REVIEWS_BATCH_SIZE, token: str = None) -> str:
        """Fetch single batch of reviews from Google Play Store API.
        
        Args:
            app_id: Google Play app ID
            lang: Language code
            country: Country code
            sort: Sort order (1=RELEVANT, 2=NEWEST, 3=RATING)
            batch_count: Number of reviews per batch
            token: Pagination token for next batch
            
        Returns:
            Raw API response text
            
        Raises:
            AppNotFoundError: If reviews not found
            NetworkError: If request fails
        """
        self.rate_limit()
        
        url = f"{Config.PLAY_STORE_BASE_URL}{Config.BATCHEXECUTE_ENDPOINT}?hl={lang}&gl={country}"
        
        headers = {
            **self.headers,
            "content-type": "application/x-www-form-urlencoded"
        }
        
        if token:
            payload = f"f.req=%5B%5B%5B%22oCPfdb%22%2C%22%5Bnull%2C%5B2%2C{sort}%2C%5B{batch_count}%2Cnull%2C%5C%22{token}%5C%22%5D%2Cnull%2C%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%5D%5D%2C%5B%5C%22{app_id}%5C%22%2C7%5D%5D%22%2Cnull%2C%22generic%22%5D%5D%5D"
        else:
            payload = f"f.req=%5B%5B%5B%22oCPfdb%22%2C%22%5Bnull%2C%5B2%2C{sort}%2C%5B{batch_count}%5D%2Cnull%2C%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%5D%5D%2C%5B%5C%22{app_id}%5C%22%2C7%5D%5D%22%2Cnull%2C%22generic%22%5D%5D%5D"
        
        try:
            response = self._make_request("POST", url, data=payload, headers=headers)
            return response.text
        except Exception as e:
            if self._is_404_error(e):
                raise AppNotFoundError(Config.ERROR_MESSAGES["REVIEWS_NOT_FOUND"].format(app_id=app_id))
            logger.error(Config.ERROR_MESSAGES["REVIEWS_FETCH_FAILED"].format(app_id=app_id, error=e))
            raise NetworkError(Config.ERROR_MESSAGES["REVIEWS_FETCH_FAILED"].format(app_id=app_id, error=e))

    def fetch_developer_page(self, dev_id: str, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> str:
        """Fetch developer portfolio page from Google Play Store.
        
        Args:
            dev_id: Developer ID (numeric or string)
            lang: Language code
            country: Country code
            
        Returns:
            HTML content of developer page
            
        Raises:
            AppNotFoundError: If developer not found
            NetworkError: If request fails
        """
        self.rate_limit()
        
        if dev_id.isdigit():
            url = f"{Config.PLAY_STORE_BASE_URL}{Config.DEVELOPER_NUMERIC_ENDPOINT}?id={quote(dev_id)}&hl={lang}&gl={country}"
        else:
            url = f"{Config.PLAY_STORE_BASE_URL}{Config.DEVELOPER_STRING_ENDPOINT}?id={quote(dev_id)}&hl={lang}&gl={country}"
        
        try:
            response = self._make_request("GET", url)
            return response.text
        except Exception as e:
            if self._is_404_error(e):
                raise AppNotFoundError(Config.ERROR_MESSAGES["DEVELOPER_NOT_FOUND"].format(dev_id=dev_id))
            if dev_id.isdigit():
                url = f"{Config.PLAY_STORE_BASE_URL}{Config.DEVELOPER_NUMERIC_ENDPOINT}?id={quote(dev_id)}&hl={lang}"
            else:
                url = f"{Config.PLAY_STORE_BASE_URL}{Config.DEVELOPER_STRING_ENDPOINT}?id={quote(dev_id)}&hl={lang}"
            try:
                response = self._make_request("GET", url)
                return response.text
            except Exception as e2:
                if self._is_404_error(e2):
                    raise AppNotFoundError(Config.ERROR_MESSAGES["DEVELOPER_NOT_FOUND"].format(dev_id=dev_id))
                logger.error(Config.ERROR_MESSAGES["DEVELOPER_FETCH_FAILED"].format(dev_id=dev_id, error=e))
                raise NetworkError(Config.ERROR_MESSAGES["DEVELOPER_FETCH_FAILED"].format(dev_id=dev_id, error=e))

    def fetch_cluster_page(self, cluster_url: str, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> str:
        """Fetch cluster page (similar apps collection) from Google Play Store.
        
        Args:
            cluster_url: Cluster URL path
            lang: Language code
            country: Country code
            
        Returns:
            HTML content of cluster page
            
        Raises:
            AppNotFoundError: If cluster not found
            NetworkError: If request fails
        """
        self.rate_limit()
        
        url = f"{Config.PLAY_STORE_BASE_URL}{cluster_url}&gl={country}&hl={lang}"
        
        try:
            response = self._make_request("GET", url)
            return response.text
        except Exception as e:
            if self._is_404_error(e):
                raise AppNotFoundError(Config.ERROR_MESSAGES["CLUSTER_NOT_FOUND"].format(cluster_url=cluster_url))
            logger.error(Config.ERROR_MESSAGES["CLUSTER_FETCH_FAILED"].format(error=e))
            raise NetworkError(Config.ERROR_MESSAGES["CLUSTER_FETCH_FAILED"].format(error=e))

    def fetch_list_page(self, collection: str, category: str = Config.DEFAULT_LIST_CATEGORY, count: int = Config.DEFAULT_LIST_COUNT, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> str:
        """Fetch top charts list page from Google Play Store.
        
        Args:
            collection: Collection type (topselling_free, topselling_paid, topgrossing)
            category: App category
            count: Number of apps to fetch
            lang: Language code
            country: Country code
            
        Returns:
            Raw API response text
            
        Raises:
            AppNotFoundError: If list not found
            NetworkError: If request fails
        """
        self.rate_limit()
        
        body = f'f.req=%5B%5B%5B%22vyAe2%22%2C%22%5B%5Bnull%2C%5B%5B8%2C%5B20%2C{count}%5D%5D%2Ctrue%2Cnull%2C%5B64%2C1%2C195%2C71%2C8%2C72%2C9%2C10%2C11%2C139%2C12%2C16%2C145%2C148%2C150%2C151%2C152%2C27%2C30%2C31%2C96%2C32%2C34%2C163%2C100%2C165%2C104%2C169%2C108%2C110%2C113%2C55%2C56%2C57%2C122%5D%2C%5Bnull%2Cnull%2C%5B%5B%5Btrue%5D%2Cnull%2C%5B%5Bnull%2C%5B%5D%5D%5D%2Cnull%2Cnull%2Cnull%2Cnull%2C%5Bnull%2C2%5D%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B1%5D%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B1%5D%5D%2C%5Bnull%2C%5B%5Bnull%2C%5B%5D%5D%5D%5D%2C%5Bnull%2C%5B%5Bnull%2C%5B%5D%5D%5D%2Cnull%2C%5Btrue%5D%5D%2C%5Bnull%2C%5B%5Bnull%2C%5B%5D%5D%5D%5D%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5B%5Bnull%2C%5B%5D%5D%5D%5D%2C%5B%5B%5Bnull%2C%5B%5D%5D%5D%5D%5D%2C%5B%5B%5B%5B7%2C1%5D%2C%5B%5B1%2C73%2C96%2C103%2C97%2C58%2C50%2C92%2C52%2C112%2C69%2C19%2C31%2C101%2C123%2C74%2C49%2C80%2C38%2C20%2C10%2C14%2C79%2C43%2C42%2C139%5D%5D%5D%5D%5D%5D%2Cnull%2Cnull%2C%5B%5B%5B1%2C2%5D%2C%5B10%2C8%2C9%5D%2C%5B%5D%2C%5B%5D%5D%5D%5D%2C%5B2%2C%5C%22{collection}%5C%22%2C%5C%22{category}%5C%22%5D%5D%5D%22%2Cnull%2C%22generic%22%5D%5D%5D&at=AFSRYlx8XZfN8-O-IKASbNBDkB6T%3A1655531200971&'
        
        url = f"{Config.PLAY_STORE_BASE_URL}{Config.BATCHEXECUTE_ENDPOINT}?rpcids=vyAe2&source-path=%2Fstore%2Fapps&hl={lang}&gl={country}"
        
        headers = {
            **self.headers,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }
        
        try:
            response = self._make_request("POST", url, data=body, headers=headers)
            return response.text
        except Exception as e:
            if self._is_404_error(e):
                raise AppNotFoundError(Config.ERROR_MESSAGES["LIST_NOT_FOUND"].format(collection=collection, category=category))
            logger.error(Config.ERROR_MESSAGES["LIST_FETCH_FAILED"].format(error=e))
            raise NetworkError(Config.ERROR_MESSAGES["LIST_FETCH_FAILED"].format(error=e))

    def fetch_suggest_page(self, term: str, lang: str = Config.DEFAULT_LANGUAGE, country: str = Config.DEFAULT_COUNTRY) -> str:
        """Fetch search suggestions from Google Play Store.
        
        Args:
            term: Search term for suggestions
            lang: Language code
            country: Country code
            
        Returns:
            Raw API response text
            
        Raises:
            AppNotFoundError: If suggestions not found
            NetworkError: If request fails
        """
        self.rate_limit()
        
        encoded_term = quote(term)
        url = f"{Config.PLAY_STORE_BASE_URL}{Config.BATCHEXECUTE_ENDPOINT}?rpcids=IJ4APc&f.sid=-697906427155521722&bl=boq_playuiserver_20190903.08_p0&hl={lang}&gl={country}&authuser&soc-app=121&soc-platform=1&soc-device=1&_reqid=1065213"
        
        body = f"f.req=%5B%5B%5B%22IJ4APc%22%2C%22%5B%5Bnull%2C%5B%5C%22{encoded_term}%5C%22%5D%2C%5B10%5D%2C%5B2%5D%2C4%5D%5D%22%5D%5D%5D"
        
        headers = {
            **self.headers,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }
        
        try:
            response = self._make_request("POST", url, data=body, headers=headers)
            return response.text
        except Exception as e:
            if self._is_404_error(e):
                raise AppNotFoundError(Config.ERROR_MESSAGES["SUGGEST_NOT_FOUND"].format(term=term))
            logger.error(Config.ERROR_MESSAGES["SUGGEST_FETCH_FAILED"].format(term=term, error=e))
            raise NetworkError(Config.ERROR_MESSAGES["SUGGEST_FETCH_FAILED"].format(term=term, error=e))

    def _make_request(self, method: str, url: str, **kwargs):
        """Make HTTP request with automatic client fallback.
        
        Args:
            method: HTTP method (GET or POST)
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response object
            
        Raises:
            Exception: If all clients fail
        """
        # Build list of clients to try, starting with preferred client
        clients_to_try = [self.client_type]
        all_clients = ["requests", "curl_cffi", "tls_client", "urllib3", "cloudscraper", "aiohttp", "httpx"]
        for client in all_clients:
            if client != self.client_type:
                clients_to_try.append(client)
        
        last_error = None
        
        # Try each client until one succeeds
        for client_type in clients_to_try:
            try:
                return self._try_request_with_client(client_type, method, url, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(Config.ERROR_MESSAGES["CLIENT_FAILED_TRYING_NEXT"].format(client_type=client_type, error=e))
                continue
        
        raise last_error
    
    def _try_request_with_client(self, client_type: str, method: str, url: str, **kwargs):
        """Attempt request with specific HTTP client.
        
        Args:
            client_type: HTTP client name
            method: HTTP method (GET or POST)
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Response object
            
        Raises:
            Exception: If client unavailable or request fails
        """
        headers = kwargs.get('headers', self.headers)
        
        if client_type == "requests":
            try:
                import requests
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=self.timeout)
                else:
                    response = requests.post(url, data=kwargs.get('data'), headers=headers, timeout=self.timeout)
                response.raise_for_status()
                return response
            except ImportError:
                raise Exception(Config.ERROR_MESSAGES["HTTP_CLIENT_NOT_AVAILABLE"].format(client="requests"))
        
        elif client_type == "curl_cffi":
            try:
                from curl_cffi import requests as curl_requests
                session = curl_requests.Session(impersonate="chrome110")
                if method == "GET":
                    response = session.get(url, headers=headers, timeout=self.timeout)
                else:
                    response = session.post(url, data=kwargs.get('data'), headers=headers, timeout=self.timeout)
                response.raise_for_status()
                return response
            except ImportError:
                raise Exception(Config.ERROR_MESSAGES["HTTP_CLIENT_NOT_AVAILABLE"].format(client="curl_cffi"))
        
        elif client_type == "tls_client":
            try:
                import tls_client
                session = tls_client.Session(client_identifier="chrome112", random_tls_extension_order=True)
                if method == "GET":
                    response = session.get(url, headers=headers)
                else:
                    response = session.post(url, data=kwargs.get('data'), headers=headers)
                if response.status_code >= 400:
                    raise Exception(Config.ERROR_MESSAGES["HTTP_ERROR"].format(status_code=response.status_code))
                return response
            except ImportError:
                raise Exception(Config.ERROR_MESSAGES["HTTP_CLIENT_NOT_AVAILABLE"].format(client="tls_client"))
        
        elif client_type == "httpx":
            try:
                import httpx
                with httpx.Client(timeout=self.timeout) as client:
                    if method == "GET":
                        response = client.get(url, headers=headers)
                    else:
                        response = client.post(url, data=kwargs.get('data'), headers=headers)
                    response.raise_for_status()
                    return response
            except ImportError:
                raise Exception(Config.ERROR_MESSAGES["HTTP_CLIENT_NOT_AVAILABLE"].format(client="httpx"))
        
        elif client_type == "urllib3":
            try:
                import urllib3
                http = urllib3.PoolManager()
                if method == "GET":
                    response = http.request('GET', url, headers=headers)
                else:
                    response = http.request('POST', url, body=kwargs.get('data'), headers=headers)
                if response.status >= 400:
                    raise Exception(Config.ERROR_MESSAGES["HTTP_ERROR"].format(status_code=response.status))
                class MockResponse:
                    def __init__(self, data, status):
                        self.text = data.decode('utf-8')
                        self.status_code = status
                    def raise_for_status(self):
                        pass
                return MockResponse(response.data, response.status)
            except ImportError:
                raise Exception(Config.ERROR_MESSAGES["HTTP_CLIENT_NOT_AVAILABLE"].format(client="urllib3"))
        
        elif client_type == "cloudscraper":
            try:
                import cloudscraper
                scraper = cloudscraper.create_scraper()
                if method == "GET":
                    response = scraper.get(url, headers=headers, timeout=self.timeout)
                else:
                    response = scraper.post(url, data=kwargs.get('data'), headers=headers, timeout=self.timeout)
                response.raise_for_status()
                return response
            except ImportError:
                raise Exception(Config.ERROR_MESSAGES["HTTP_CLIENT_NOT_AVAILABLE"].format(client="cloudscraper"))
        

        elif client_type == "aiohttp":
            try:
                import asyncio
                return asyncio.run(self._async_request(method, url, **kwargs))
            except ImportError:
                raise Exception(Config.ERROR_MESSAGES["HTTP_CLIENT_NOT_AVAILABLE"].format(client="aiohttp"))
        
        raise Exception(Config.ERROR_MESSAGES["UNKNOWN_CLIENT_TYPE"].format(client_type=client_type))
    
    async def _async_request(self, method: str, url: str, **kwargs):
        """Async HTTP request using aiohttp.
        
        Args:
            method: HTTP method (GET or POST)
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            MockResponse object with text attribute
        """
        import aiohttp
        headers = kwargs.get('headers', self.headers)
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            if method == "GET":
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    text = await response.text()
                    class MockResponse:
                        def __init__(self, text):
                            self.text = text
                        def raise_for_status(self):
                            pass
                    return MockResponse(text)
            else:
                async with session.post(url, data=kwargs.get('data'), headers=headers) as response:
                    response.raise_for_status()
                    text = await response.text()
                    class MockResponse:
                        def __init__(self, text):
                            self.text = text
                        def raise_for_status(self):
                            pass
                    return MockResponse(text)
    
    def _is_404_error(self, error: Exception) -> bool:
        """Check if error is a 404 not found error.
        
        Args:
            error: Exception to check
            
        Returns:
            True if 404 error, False otherwise
        """
        error_str = str(error).lower()
        return "404" in error_str or "not found" in error_str
    
    def rate_limit(self):
        """Apply rate limiting delay between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug(Config.ERROR_MESSAGES["RATE_LIMIT_SLEEP"].format(sleep_time=sleep_time))
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()