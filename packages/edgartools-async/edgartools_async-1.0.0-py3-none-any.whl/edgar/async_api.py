import os
from typing import Optional, Union

from edgar.core import set_identity
from edgar.httpclient import async_http_client
from edgar.httprequests import IdentityNotSetException, download_json_async
from edgar.entity.submissions import create_entity_from_submissions_json
from edgar.reference.tickers import company_tickers_json_url

__all__ = ["get_company_async", "find_cik_async"]


async def find_cik_async(ticker: str) -> Optional[int]:
    ticker = str(ticker).upper().replace('.', '-')
    async with async_http_client() as client:
        tickers_json = await download_json_async(client, company_tickers_json_url)
        for item in tickers_json.values():
            if item.get("ticker", "").upper() == ticker:
                return int(item["cik_str"])
    return None


async def get_company_async(cik_or_ticker: Union[str, int], user_agent: Optional[str] = None):
    """
    Fully async helper that resolves CIK and loads submissions without blocking.

    - Sets EDGAR identity if `user_agent` provided, else requires EDGAR_IDENTITY.
    - Resolves ticker -> CIK via async SEC file download.
    - Downloads submissions JSON asynchronously and constructs a Company object without extra network calls.
    """
    if user_agent:
        set_identity(user_agent)
    elif os.environ.get("EDGAR_IDENTITY") is None:
        raise IdentityNotSetException("User-Agent identity is not set. Pass user_agent or set EDGAR_IDENTITY.")

    # Resolve CIK
    if isinstance(cik_or_ticker, int) or (isinstance(cik_or_ticker, str) and cik_or_ticker.isdigit()):
        cik = int(str(cik_or_ticker).lstrip('0'))
    else:
        cik = await find_cik_async(str(cik_or_ticker))
        if cik is None:
            raise ValueError(f"Could not find CIK for ticker '{cik_or_ticker}'")

    # Download submissions and build Company without triggering sync I/O
    async with async_http_client() as client:
        submissions_json = await download_json_async(client, f"https://data.sec.gov/submissions/CIK{cik:010}.json")

    company = create_entity_from_submissions_json(submissions_json, entity_type='company')
    return company
