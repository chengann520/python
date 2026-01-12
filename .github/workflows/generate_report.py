import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import os
import ssl

# SSL 修正
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

def generate_static_report():
    ticker_symbol = "2330.TW"
    print(f"正在為 {ticker_symbol} 產生靜態報表...")
    
    # 抓取資料 (使用強健邏輯)
    try:
        data = yf.download(ticker_symbol, period="1y")
        if data.empty:
            data = yf.Ticker(ticker_symbol).history(period="1y")
    except Exception as e:
        print(f"錯誤: {e}")
        return

    if data.empty:
        print("抓取失敗，無法產生報表。")
        return

    # 處理多層索引
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # 繪製圖表
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name="K線圖"
    )])

    fig.update_layout(
        title=f"{ticker_symbol} 年度股價趨勢圖 (自動更新)",
        yaxis_title="股價 (TWD)",
        xaxis_title="日期",
        template="plotly_white",
        height=700
    )

    # 儲存為 index.html (供 GitHub Pages 使用)
    fig.write_html("index.html")
    print("報表已成功儲存為 index.html")

if __name__ == "__main__":
    generate_static_report()
