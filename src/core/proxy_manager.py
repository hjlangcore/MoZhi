from typing import Optional, Dict, List
from loguru import logger
import os
import platform


class ProxyManager:
    def __init__(self):
        self.current_proxy = None
        self.system_proxy = self._detect_system_proxy()
        self.proxy_list: List[Dict[str, str]] = []

    def _detect_system_proxy(self) -> Optional[str]:
        try:
            if platform.system() == 'Windows':
                import winreg
                try:
                    with winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
                    ) as key:
                        proxy_enabled = winreg.QueryValueEx(key, "ProxyEnable")[0]
                        if proxy_enabled:
                            proxy_server = winreg.QueryValueEx(key, "ProxyServer")[0]
                            return proxy_server
                except Exception as e:
                    logger.debug(f"Failed to detect Windows proxy: {e}")
            else:
                http_proxy = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY')
                https_proxy = os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY')
                if https_proxy:
                    return https_proxy
                elif http_proxy:
                    return http_proxy
        except Exception as e:
            logger.debug(f"Proxy detection error: {e}")
        return None

    def set_proxy(self, proxy_url: Optional[str]):
        if proxy_url:
            if not proxy_url.startswith('http://') and not proxy_url.startswith('https://'):
                proxy_url = f'http://{proxy_url}'
            self.current_proxy = proxy_url
            logger.info(f"Proxy set to: {proxy_url}")
        else:
            self.current_proxy = None
            logger.info("Proxy disabled")

    def use_system_proxy(self):
        if self.system_proxy:
            self.current_proxy = self.system_proxy
            logger.info(f"Using system proxy: {self.system_proxy}")
        else:
            logger.info("No system proxy detected, disabling proxy")
            self.current_proxy = None

    def add_proxy_to_list(self, name: str, proxy_url: str):
        existing = next((p for p in self.proxy_list if p['name'] == name), None)
        if existing:
            existing['url'] = proxy_url
        else:
            self.proxy_list.append({'name': name, 'url': proxy_url})
        logger.info(f"Added proxy: {name} -> {proxy_url}")

    def remove_proxy_from_list(self, name: str):
        self.proxy_list = [p for p in self.proxy_list if p['name'] != name]
        logger.info(f"Removed proxy: {name}")

    def select_proxy_by_name(self, name: str) -> bool:
        proxy = next((p for p in self.proxy_list if p['name'] == name), None)
        if proxy:
            self.current_proxy = proxy['url']
            logger.info(f"Selected proxy: {name} -> {proxy['url']}")
            return True
        logger.warning(f"Proxy '{name}' not found in list")
        return False

    def get_proxy_list(self) -> List[Dict[str, str]]:
        return self.proxy_list

    def get_current_proxy(self) -> Optional[str]:
        return self.current_proxy

    def is_proxy_active(self) -> bool:
        return self.current_proxy is not None


_proxy_manager: Optional[ProxyManager] = None


def get_proxy_manager() -> ProxyManager:
    global _proxy_manager
    if _proxy_manager is None:
        _proxy_manager = ProxyManager()
    return _proxy_manager
