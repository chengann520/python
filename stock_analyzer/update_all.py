import sys
import os
from datetime import datetime
import pandas as pd
from fetcher import get_history, get_info, get_ticker
from db import init_db, get_db, save_tick
from indicators import moving_average, macd, rsi
from peers import build_peers_dataframe
from sentiment import sentiment_score_chinese

# List of tickers to track (can be moved to a config file or DB)
TICKERS = ["2330.TW", "2317.TW", "2454.TW", "2603.TW", "2618.TW"]
OUTPUT_DIR = "outputs"

def update_all():
    print(f"Starting update at {datetime.now()}")
    init_db()
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    db = next(get_db())
    
    for ticker in TICKERS:
        try:
            print(f"Updating {ticker}...")
            # Fetch latest data (e.g., last 1 year for indicators)
            df = get_history(ticker, period="1y", interval="1d")
            
            if not df.empty:
                # Calculate Indicators
                df['MA20'] = moving_average(df['Close'], 20)
                df['MA50'] = moving_average(df['Close'], 50)
                df['MACD'], _, _ = macd(df['Close'])
                df['RSI'] = rsi(df['Close'])
                
                # Get the last row
                last_row = df.iloc[-1]
                
                # Save to DB
                tick_data = {
                    "ticker": ticker,
                    "ts": last_row.name.to_pydatetime(),
                    "open": float(last_row["Open"]),
                    "high": float(last_row["High"]),
                    "low": float(last_row["Low"]),
                    "close": float(last_row["Close"]),
                    "volume": int(last_row["Volume"])
                }
                save_tick(db, tick_data)
                print(f"Saved {ticker} data to DB.")
                
                # Generate Report Data
                info = get_info(ticker)
                
                # Sentiment
                t = get_ticker(ticker)
                news = t.news
                avg_sentiment = 0.5
                if news:
                    scores = [sentiment_score_chinese(n.get('title')) for n in news[:5]]
                    if scores:
                        avg_sentiment = sum(scores) / len(scores)
                
                # Peers
                peers_list = [ticker]
                if "2330" in ticker: peers_list.extend(["2303.TW", "2454.TW"])
                elif "2603" in ticker: peers_list.extend(["2609.TW", "2615.TW"])
                
                peers_df = build_peers_dataframe(peers_list)
                peer_avg_pe = peers_df['pe'].mean() if not peers_df.empty else 0
                peer_median_mktcap = peers_df['marketCap'].median() if not peers_df.empty else 0
                
                # Save CSV
                report_data = {
                    "Date": [last_row.name.strftime("%Y-%m-%d")],
                    "Close": [last_row["Close"]],
                    "Volume": [last_row["Volume"]],
                    "MA20": [last_row["MA20"]],
                    "MA50": [last_row["MA50"]],
                    "MACD": [last_row["MACD"]],
                    "RSI": [last_row["RSI"]],
                    "Sentiment": [avg_sentiment],
                    "Peer_Avg_PE": [peer_avg_pe],
                    "Peer_Median_MarketCap": [peer_median_mktcap]
                }
                
                report_df = pd.DataFrame(report_data)
                csv_filename = os.path.join(OUTPUT_DIR, f"{ticker}_summary_{datetime.now().strftime('%Y%m%d')}.csv")
                report_df.to_csv(csv_filename, index=False)
                print(f"Saved report to {csv_filename}")

            else:
                print(f"No data found for {ticker}")
                
        except Exception as e:
            print(f"Error updating {ticker}: {e}")
            
    print("Update complete.")

if __name__ == "__main__":
    update_all()
