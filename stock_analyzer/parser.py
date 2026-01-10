import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; StockBot/1.0; +your_email@example.com)"
}

def fetch_html(url: str, timeout=10) -> str:
    """
    Fetches HTML content from a URL.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return ""

def parse_price_and_basic(html: str) -> Dict[str, Optional[float]]:
    """
    Parses price and volume from Yahoo Finance HTML.
    """
    if not html:
        return {"price": None, "volume": None}
        
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator="\n")
    
    # Regex to find price like "成交 33.50"
    # Note: This regex might need adjustment based on actual page content
    m = re.search(r"成交\s*([0-9]+(?:\.[0-9]+)?)", text)
    price = float(m.group(1)) if m else None

    # Regex to find volume like "總量 12,345"
    m_vol = re.search(r"總量\s*([0-9,]+)", text)
    volume = int(m_vol.group(1).replace(",", "")) if m_vol else None

    return {"price": price, "volume": volume}

def parse_peers(html: str) -> List[str]:
    """
    Parses peer tickers from "People also watch" section.
    """
    if not html:
        return []

    # Simple regex to find tickers like 2610.TW
    # This is a heuristic; might need refinement
    peers = re.findall(r"(\d{3,4}\.TW)", html)
    
    # Deduplicate and sort
    return sorted(list(set(peers)))

def get_peers(ticker: str) -> List[str]:
    """
    Fetches peer tickers for a given ticker from Yahoo Finance.
    """
    # Construct URL (Yahoo Finance TW)
    url = f"https://tw.stock.yahoo.com/quote/{ticker}"
    html = fetch_html(url)
    if html:
        return parse_peers(html)
    return []
