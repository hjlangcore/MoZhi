from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from loguru import logger
import requests
import time
import socket
import urllib3
import ipaddress
from urllib.parse import urlparse
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)


# SSRF 防护配置
ALLOWED_SCHEMES = ['http', 'https']
BLOCKED_IP_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('0.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('224.0.0.0/4'),
    ipaddress.ip_network('240.0.0.0/4'),
]


def is_safe_url(url: str) -> bool:
    """检查 URL 是否安全，防止 SSRF 攻击"""
    try:
        parsed = urlparse(url)
        
        # 检查协议白名单
        if parsed.scheme not in ALLOWED_SCHEMES:
            logger.warning(f"SSRF protection: blocked scheme '{parsed.scheme}' for URL: {url[:50]}")
            return False
        
        # 检查 hostname 是否存在
        if not parsed.hostname:
            logger.warning(f"SSRF protection: no hostname for URL: {url[:50]}")
            return False
        
        # 解析域名获取 IP
        ip = socket.gethostbyname(parsed.hostname)
        ip_obj = ipaddress.ip_address(ip)
        
        # 检查是否在阻止的 IP 范围内
        for blocked in BLOCKED_IP_RANGES:
            if ip_obj in blocked:
                logger.warning(f"SSRF protection: blocked IP {ip} for URL: {url[:50]}")
                return False
        
        return True
    except Exception as e:
        logger.error(f"SSRF protection: error checking URL {url[:50]}: {e}")
        return False


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
        # SSRF 防护检查
        if not is_safe_url(url):
            logger.error(f"SSRF protection: blocked request to unsafe URL: {url[:80]}")
            return 0, "SSRF protection: unsafe URL blocked", {}
        
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
