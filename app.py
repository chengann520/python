import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import ssl
import os

# --- 頁面設定 ---
st.set_page_config(
    page_title="台股即時監測 - 2330 台積電",
    page_icon="📈",
    layout="wide"
)

# --- 解決 SSL 認證問題 (針對特定環境) ---
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

# --- 資料抓取函式 ---
@st.cache_data(ttl=600)  # 快取資料 10 分鐘，避免頻繁請求被封鎖
def fetch_stock_data(ticker_symbol, period="1mo"):
    try:
        # 嘗試使用 download
        data = yf.download(ticker_symbol, period=period, timeout=30)
        
        if data.empty:
            # 備援方案：使用 Ticker
            ticker = yf.Ticker(ticker_symbol)
            data = ticker.history(period=period)
            
        return data
    except Exception as e:
        st.error(f"抓取資料時發生錯誤: {e}")
        return pd.DataFrame()

# --- 側邊欄 ---
st.sidebar.header("設定")
ticker = st.sidebar.text_input("股票代碼", value="2330.TW")
time_period = st.sidebar.selectbox(
    "選擇時間範圍",
    options=("1d", "5d", "1mo", "6mo", "1y", "max"),
    index=2
)

# --- 主頁面 ---
st.title("📈 台股即時數據看板")
st.subheader(f"目前查看：{ticker}")

with st.spinner("正在獲取最新股價資料..."):
    df = fetch_stock_data(ticker, period=time_period)

if not df.empty:
    # 整理資料（處理多層索引如果是 yfinance 新版）
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 最新資訊卡片
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    col1, col2, col3, col4 = st.columns(4)
    
    change = latest['Close'] - prev['Close']
    change_pct = (change / prev['Close']) * 100
    
    col1.metric("最新收盤價", f"{latest['Close']:.2f}", f"{change:.2f} ({change_pct:.2f}%)")
    col2.metric("當日最高", f"{latest['High']:.2f}")
    col3.metric("當日最低", f"{latest['Low']:.2f}")
    col4.metric("成交量", f"{int(latest['Volume']):,}")

    # 繪製圖表
    st.markdown("### 股價走勢圖")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['Close'], 
        mode='lines', 
        name='收盤價',
        line=dict(color='#1f77b4', width=2)
    ))
    
    # 針對日線加入蠟燭圖 (如果資料夠多)
    if st.checkbox("顯示 K 線圖"):
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close']
        )])
    
    fig.update_layout(
        template="plotly_dark",
        xaxis_title="日期",
        yaxis_title="股價 (TWD)",
        margin=dict(l=20, r=20, t=20, b=20),
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    # 顯示原始資料
    with st.expander("查看原始數據表格"):
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
else:
    st.warning("無法獲取資料，請確認股票代碼是否正確或稍後再試。")
    st.info("提示：台股請記得加上 .TW (例如 2330.TW)")

# 頁尾
st.markdown("---")
st.caption(f"最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
