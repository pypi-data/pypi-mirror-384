import os
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import AsyncGenerator, Generator, Optional

import httpx

from edgar.core import get_identity, strtobool, log

from .core import edgar_data_dir

MAX_SUBMISSIONS_AGE_SECONDS = 10 * 60  # Check for submissions every 10 minutes
MAX_INDEX_AGE_SECONDS = 30 * 60  # Check for updates to index (ie: daily-index) every 30 minutes

# rules are regular expressions matching the request url path: 
# The value determines whether it is cached or not:
# - int > 0: how many seconds it'll be considered valid. During this time, the cached object will not be revalidated.
# - False or 0: Do not cache
# - True: Cache forever, never revalidate
# - None: Determine cachability using response cache headers only. 
#
# Note that: revalidation consumes rate limit "hit", but will be served from cache if the data hasn't changed.


CACHE_RULES = {
    r".*\.sec\.gov": {
        "/submissions.*": MAX_SUBMISSIONS_AGE_SECONDS,
        r"/include/ticker\.txt.*": MAX_SUBMISSIONS_AGE_SECONDS,
        r"/files/company_tickers\.json.*": MAX_SUBMISSIONS_AGE_SECONDS,
        ".*index/.*": MAX_INDEX_AGE_SECONDS,
        "/Archives/edgar/data": True,  # cache forever
    }
}

def get_cache_directory() -> str:
    cachedir = Path(edgar_data_dir) / "_tcache"
    cachedir.mkdir(parents=True, exist_ok=True)

    return str(cachedir)


def get_edgar_verify_ssl():
    """
    Returns True if using SSL verification on http requests
    """

    if "EDGAR_VERIFY_SSL" in os.environ:
        return strtobool(os.environ["EDGAR_VERIFY_SSL"])
    else:
        return True


def get_http_mgr(cache_enabled: bool = True, request_per_sec_limit: int = 9):
    if cache_enabled:
        cache_dir = get_cache_directory()
        cache_mode = "Hishel-File"
    else:
        cache_dir = None
        cache_mode = "Disabled"

    # Try throttle/cache manager lazily; fall back to simple manager on failure
    try:
        from httpxthrottlecache import HttpxThrottleCache  # lazy import
        http_mgr = HttpxThrottleCache(
            user_agent_factory=get_identity,
            cache_dir=cache_dir,
            cache_mode=cache_mode,
            request_per_sec_limit=request_per_sec_limit,
            cache_rules=CACHE_RULES,
        )
        http_mgr.httpx_params["verify"] = get_edgar_verify_ssl
        return http_mgr
    except Exception as e:
        log.warning("Failed to initialize httpxthrottlecache (%s). Falling back to SimpleHTTPManager.", e)

        class SimpleHTTPManager:
            def __init__(self):
                self.httpx_params = {"verify": get_edgar_verify_ssl}

            def _populate_user_agent(self, params: dict) -> dict:
                headers = params.get("headers", {}) or {}
                try:
                    ua = get_identity()
                except Exception:
                    ua = None
                if ua:
                    headers["User-Agent"] = ua
                params["headers"] = headers
                return params

            @asynccontextmanager
            async def async_http_client(self, client: Optional[httpx.AsyncClient] = None, **kwargs):
                params = self._populate_user_agent(self.httpx_params.copy())
                params.update(kwargs)
                if client is None:
                    async with httpx.AsyncClient(**params) as c:
                        yield c
                else:
                    yield client

            @contextmanager
            def http_client(self, **kwargs):
                params = self._populate_user_agent(self.httpx_params.copy())
                params.update(kwargs)
                with httpx.Client(**params) as c:
                    yield c

            def close(self):
                pass

        return SimpleHTTPManager()


@asynccontextmanager
async def async_http_client(client: Optional[httpx.AsyncClient] = None, **kwargs) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with HTTP_MGR.async_http_client(client=client, **kwargs) as client:
        yield client


@contextmanager
def http_client(**kwargs) -> Generator[httpx.Client, None, None]:
    with HTTP_MGR.http_client(**kwargs) as client:
        yield client


def get_http_params():
    return HTTP_MGR._populate_user_agent(HTTP_MGR.httpx_params.copy())


def close_clients():
    HTTP_MGR.close()


HTTP_MGR = get_http_mgr()
