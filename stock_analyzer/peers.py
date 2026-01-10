import pandas as pd
from fetcher import get_info

def build_peers_dataframe(tickers):
    """
    Builds a DataFrame comparing peers based on key metrics.
    """
    rows = []
    for t in tickers:
        try:
            info = get_info(t)
            rows.append({
                "ticker": t,
                "price": info.get("currentPrice") or info.get("previousClose"),
                "pe": info.get("trailingPE"),
                "pb": info.get("priceToBook"),
                "marketCap": info.get("marketCap"),
                "roe": info.get("returnOnEquity"),
                "revenueGrowth": info.get("revenueGrowth")
            })
        except Exception as e:
            print(f"Error fetching info for {t}: {e}")
            
    df = pd.DataFrame(rows)
    if not df.empty:
        # Sort by PE (ascending) as a default, handling NaNs
        df = df.sort_values("pe", na_position='last')
    return df
