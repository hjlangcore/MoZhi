from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from loguru import logger
import requests
import time
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)


class NetworkClient:
    def __init__(self, timeout: int = 30, max_retries: int = 3, verify_ssl: bool = True):
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self.session = self._create_session()
        self.request_count = 0
        self.last_request_time = None

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        return session

    def _exponential_backoff(self, attempt: int) -> float:
        return min(2 ** attempt, 10)

    def _add_rate_limit_delay(self):
        if self.last_request_time:
            time_since_last = (datetime.now() - self.last_request_time).total_seconds()
            if time_since_last < 1:
                time.sleep(1 - time_since_last)

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None
    ) -> Tuple[int, str, Dict[str, Any]]:
        return self._request('GET', url, params=params, headers=headers, proxy=proxy)

    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None
    ) -> Tuple[int, str, Dict[str, Any]]:
        return self._request('POST', url, data=data, json=json, headers=headers, proxy=proxy)

    def _request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Tuple[int, str, Dict[str, Any]]:
        self._add_rate_limit_delay()

        proxies = None
        proxy_url = kwargs.pop('proxy', None)
        if proxy_url:
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                    proxies=proxies,
                    **kwargs
                )
                
                self.request_count += 1
                self.last_request_time = datetime.now()
                
                return response.status_code, response.text, response.headers
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed for {url}")
                    return 0, f"Request failed: {str(e)}", {}

    def close(self):
        self.session.close()

    def reset(self):
        self.request_count = 0
        self.last_request_time = None
        self.session = self._create_session()


def create_network_client(
    timeout: int = 30,
    max_retries: int = 3,
    verify_ssl: bool = True
) -> NetworkClient:
    return NetworkClient(timeout=timeout, max_retries=max_retries, verify_ssl=verify_ssl)


_network_client: Optional[NetworkClient] = None


def get_network_client() -> NetworkClient:
    global _network_client
    if _network_client is None:
        _network_client = create_network_client()
    return _network_client
