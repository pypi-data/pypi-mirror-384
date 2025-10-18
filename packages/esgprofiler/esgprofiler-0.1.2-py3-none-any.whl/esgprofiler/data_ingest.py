import yfinance as yf
import pandas as pd
from bs4 import BeautifulSoup
import os

# Try to import requests, but provide a urllib fallback so the module can be used
# even if the requests package isn't available in the environment.
try:
    import requests
except Exception:
    requests = None

import urllib.request
import urllib.error

class _SimpleResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

def _http_get(url, headers=None):
    """
    Make an HTTP GET request using requests if available, otherwise urllib.
    Returns an object with .text and .status_code to be compatible with requests.Response.
    """
    try:
        if requests is not None:
            resp = requests.get(url, headers=headers)
            return resp
        else:
            req = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(req) as r:
                text = r.read().decode("utf-8", errors="replace")
                status = getattr(r, "status", 200)
                return _SimpleResponse(text, status_code=status)
    except urllib.error.HTTPError as e:
        try:
            text = e.read().decode("utf-8", errors="replace")
        except Exception:
            text = str(e)
        return _SimpleResponse(text, status_code=getattr(e, "code", 500))
    except Exception as e:
        return _SimpleResponse(str(e), status_code=500)

# (removed duplicate implementation; the working fetch_news_headlines is defined further below)

def fetch_yahoo_profile(ticker):
    """
    Fetch basic company info and ESG scores from Yahoo Finance as a starting point.
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        info = getattr(ticker_obj, "info", {}) or {}
        profile = {
            "longName": info.get("longName"),
            "industry": info.get("industry"),
            "sector": info.get("sector"),
            "esgScores": info.get("esgScores", {})
        }
        return profile
    except Exception as e:
        print(f"Error fetching Yahoo profile for {ticker}: {e}")
        return {}

# duplicate stub definitions removed
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    all_headlines = []
    for page in range(pages):
        start = page * 10
        url = f"https://www.bing.com/news/search?q={query}+sustainability&FORM=HDRSC6&first={start}"
        resp = _http_get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        headlines = [h.text for h in soup.find_all("a", {"class": "title"})]
        all_headlines.extend(headlines)
    return all_headlines

def fetch_url_text(url):
    """
    Download and extract text from a web page (e.g., online sustainability report).
    """
    try:
        response = _http_get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator="\n")
        return text
    except Exception as e:
        print(f"Error extracting text from {url}: {e}")
        return ""

def fetch_sec_filings(cik_or_ticker):
    """
    Download recent SEC filings (10-K, 20-F, etc.) using the sec-edgar-downloader package.
    """
    try:
        # sec_edgar_downloader exposes Downloader from its internal module _Downloader
        from sec_edgar_downloader._Downloader import Downloader
        # sec_edgar_downloader requires an email address; read from env var with a sensible default
        email = os.environ.get("SEC_EDGAR_EMAIL", "noreply@example.com")
        dl = Downloader("esgprofiler_data", email_address=email)
        # Call get with two positional args (filing type and company); use the default amount.
        dl.get("10-K", cik_or_ticker)
        path = os.path.join("esgprofiler_data", "SEC-Edgar-Data", str(cik_or_ticker))
        files = []
        for dirpath, _, filenames in os.walk(path):
            for fname in filenames:
                if fname.lower().endswith(".txt") or fname.lower().endswith(".html"):
                    files.append(os.path.join(dirpath, fname))
        return files
    except Exception as e:
        print(f"Error downloading SEC filings for {cik_or_ticker}: {e}")
        return []
