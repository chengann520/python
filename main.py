import yfinance as yf
import pandas as pd
import os
import ssl

# 解決 SSL 驗證問題 (保留之前的修正，這對於繞過本地認證錯誤很重要)
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

def get_stock():
    # 情況 B：yfinance 抓不到資料 (Empty Data)
    # 解決方法：加入更強健的抓取邏輯
    
    print("正在抓取 2330.TW 的資料...")
    # 使用 download 並加入 timeout 防止卡死
    data = yf.download("2330.TW", period="1d", timeout=30)
    
    if data.empty:
        print("yf.download 抓取失敗 (Empty Data)，嘗試使用 yf.Ticker 備用方案...")
        # 如果失敗，嘗試另外一種寫法
        ticker = yf.Ticker("2330.TW")
        data = ticker.history(period="1d")
    
    if not data.empty:
        print("成功獲取數據：")
        print(data)
        data.to_csv("stock_price.csv")
        print("資料已儲存至 stock_price.csv")
    else:
        raise Exception("無法從 Yahoo Finance 獲取資料。這可能是因為 IP 被封鎖或網路問題。")

if __name__ == "__main__":
    get_stock()
