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

@st.cache_data(ttl=86400)  # 快取資料 24 小時，清單不需要頻繁更新
def get_stock_list():
    """從證交所與櫃買中心獲取股票清單"""
    try:
        # 上市股票
        url_tse = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        # 上櫃股票
        url_otc = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=4"
        
        tse_tables = pd.read_html(url_tse, encoding='big5-hkscs')
        otc_tables = pd.read_html(url_otc, encoding='big5-hkscs')
        
        tse_df = tse_tables[0]
        otc_df = otc_tables[0]
        
        # 整理資料：只保留第一欄「有價證券代號及名稱」，並過濾掉標題列
        def clean_stock_df(df, suffix):
            df = df.iloc[2:, [0]]
            df.columns = ['name']
            # 分離代號與名稱 (例如 "2330　台積電")
            df['code'] = df['name'].apply(lambda x: x.split('\u3000')[0] if '\u3000' in x else '')
            df['real_name'] = df['name'].apply(lambda x: x.split('\u3000')[1] if '\u3000' in x else '')
            # 過濾掉非股票類型的資料 (通常股票代號長度為 4)
            df = df[df['code'].str.len() == 4]
            df['display'] = df['code'] + ' ' + df['real_name']
            df['ticker'] = df['code'] + suffix
            return df[['display', 'ticker']]

        tse_clean = clean_stock_df(tse_df, ".TW")
        otc_clean = clean_stock_df(otc_df, ".TWO")
        
        full_list = pd.concat([tse_clean, otc_clean], ignore_index=True)
        return full_list
    except Exception as e:
        st.error(f"獲取股票清單時發生錯誤: {e}")
        return pd.DataFrame({'display': ['2330 台積電'], 'ticker': ['2330.TW']})

# --- 側邊欄 ---
st.sidebar.header("設定")

stock_df = get_stock_list()
stock_options = stock_df['display'].tolist()
default_index = stock_options.index("2330 台積電") if "2330 台積電" in stock_options else 0

selected_display = st.sidebar.selectbox(
    "搜尋股票 (代碼或名稱)",
    options=stock_options,
    index=default_index
)

# 取得對應的 Yahoo Finance 代號
ticker = stock_df[stock_df['display'] == selected_display]['ticker'].values[0]

time_period = st.sidebar.selectbox(
    "選擇時間範圍",
    options=("1d", "5d", "1mo", "6mo", "1y", "max"),
    index=2
)

st.sidebar.header("技術指標")
show_ma = st.sidebar.checkbox("MA (移動平均)", value=True)
show_macd = st.sidebar.checkbox("MACD", value=False)
show_vol = st.sidebar.checkbox("VOL (成交量)", value=True)
show_kd = st.sidebar.checkbox("KD", value=False)
show_rsi = st.sidebar.checkbox("RSI", value=False)
show_dmi = st.sidebar.checkbox("DMI", value=False)

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

    # --- 計算技術指標 ---
    if show_ma:
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()

    if show_macd:
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['Hist'] = df['MACD'] - df['Signal']

    if show_rsi:
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

    if show_kd:
        low_min = df['Low'].rolling(window=9).min()
        high_max = df['High'].rolling(window=9).max()
        df['RSV'] = (df['Close'] - low_min) / (high_max - low_min) * 100
        df['K'] = df['RSV'].ewm(com=2, adjust=False).mean()
        df['D'] = df['K'].ewm(com=2, adjust=False).mean()

    if show_dmi:
        high = df['High']
        low = df['Low']
        close = df['Close']
        window = 14
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=window).mean()
        
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        plus_dm = pd.Series([u if u > d and u > 0 else 0 for u, d in zip(up_move, down_move)], index=df.index)
        minus_dm = pd.Series([d if d > u and d > 0 else 0 for u, d in zip(up_move, down_move)], index=df.index)
        
        plus_di = 100 * (plus_dm.rolling(window=window).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=window).mean() / atr)
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
        adx = dx.rolling(window=window).mean()
        
        df['Plus_DI'] = plus_di
        df['Minus_DI'] = minus_di
        df['ADX'] = adx

    # --- 繪製圖表 ---
    st.markdown("### 股價走勢圖")
    
    # 建立多子圖（如果有成交量或指標需要分開顯示）
    from plotly.subplots import make_subplots
    
    # 計算需要的列數 (Row counts)
    rows = 1
    row_heights = [0.7]
    if show_vol:
        rows += 1
        row_heights.append(0.3)
    if show_macd or show_kd or show_rsi or show_dmi:
        # 為了簡化，指標放同一個區塊或分開？通常分開比較好。
        # 這裡先實作將 Close/MA 放在 row 1，Vol 放在 row 2，其他指標放在 row 3
        rows += 1
        row_heights.append(0.3)
        row_heights[0] = 0.5 # 調整比例

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, row_heights=row_heights)

    # 主圖：K線或收盤價
    if st.checkbox("顯示 K 線圖", value=True):
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='K線'
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=df.index, 
            y=df['Close'], 
            mode='lines', 
            name='收盤價',
            line=dict(color='#1f77b4', width=2)
        ), row=1, col=1)

    # 均線
    if show_ma:
        fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='MA5', line=dict(width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20', line=dict(width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], name='MA60', line=dict(width=1)), row=1, col=1)

    # 成交量
    if show_vol:
        colors = ['red' if df['Close'][i] < df['Open'][i] else 'green' for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color=colors), row=2, col=1)

    # 其他指標 (放在最後一列)
    idx_row = rows if rows > 1 else 1
    if show_macd:
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD'), row=idx_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal'), row=idx_row, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Hist'], name='Hist'), row=idx_row, col=1)
    
    if show_kd:
        fig.add_trace(go.Scatter(x=df.index, y=df['K'], name='K'), row=idx_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['D'], name='D'), row=idx_row, col=1)
    
    if show_rsi:
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI'), row=idx_row, col=1)

    if show_dmi:
        fig.add_trace(go.Scatter(x=df.index, y=df['Plus_DI'], name='+DI', line=dict(color='green')), row=idx_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Minus_DI'], name='-DI', line=dict(color='red')), row=idx_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['ADX'], name='ADX', line=dict(color='orange')), row=idx_row, col=1)

    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=800 if rows > 1 else 500,
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
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
