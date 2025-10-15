import logging
import time
from datetime import datetime
from urllib.parse import urlparse

default_delay_maps: dict[str, float] = {
    'dfcfw.com': 1,
    'eastmoney.com': 1.2,
    'sina.com.cn': 3,
    'sohu.com': 2,
    'tushare.pro': 0.3,
    '163.com': 1,
}

mod_logger = logging.getLogger(__name__)


class Throttle:
    def __init__(self, delay_maps: dict[str, float] | None = None):
        if delay_maps is not None:
            self.delay_maps = delay_maps.copy()
        else:
            self.delay_maps = default_delay_maps.copy()
        self.domains_last_accessed: dict[str, datetime] = {}

    def update_delay_maps(self, delay_maps_update: dict[str, float]) -> None:
        self.delay_maps.update(delay_maps_update)

    def calc_wait(self, url: str) -> tuple[str, float]:
        parsed = urlparse(url)
        hostname = parsed.hostname

        assert hostname is not None

        parts = hostname.split('.')

        if len(parts) >= 3 and ".".join(parts[-2:]) in ["com.cn"]:
            effective_domain = ".".join(parts[-3:])
        else:
            effective_domain = ".".join(parts[-2:])

        if effective_domain not in self.delay_maps:
            return effective_domain, 0

        last_accessed = self.domains_last_accessed.get(effective_domain)
        delay = self.delay_maps[effective_domain]

        if last_accessed is not None:
            cur_time = datetime.now()
            elapsed = (cur_time - last_accessed).total_seconds()
            sleep_secs = delay - elapsed
        else:
            sleep_secs = 0

        return effective_domain, sleep_secs

    def wait(self, url: str) -> None:
        domain, sleep_secs = self.calc_wait(url)

        if sleep_secs > 0:
            mod_logger.info(f"wait: domain {domain}, sleep {sleep_secs}")
            time.sleep(sleep_secs)
        self.domains_last_accessed[domain] = datetime.now()
