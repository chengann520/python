import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fetcher import get_history, get_info, get_ticker
from parser import get_peers
from indicators import moving_average, macd, rsi
from db import get_db, Tick
from sqlalchemy.orm import Session
from peers import build_peers_dataframe
from sentiment import sentiment_score_chinese

st.set_page_config(page_title="Stock Analyzer", layout="wide")

st.title("Taiwan Stock Analyzer")

sidebar = st.sidebar
ticker = sidebar.text_input("Enter Ticker (e.g., 2330.TW)", "2330.TW")
period = sidebar.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)

if ticker:
    try:
        # Fetch Data
        df = get_history(ticker, period=period)
        info = get_info(ticker)
        
        # Display Basic Info
        st.header(f"{info.get('longName', ticker)} ({ticker})")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Price", info.get("currentPrice", "N/A"))
        col2.metric("Market Cap", f"{info.get('marketCap', 0):,}")
        col3.metric("PE Ratio", info.get("trailingPE", "N/A"))
        col4.metric("52W High", info.get("fiftyTwoWeekHigh", "N/A"))

        # Calculate Indicators
        df['MA20'] = moving_average(df['Close'], 20)
        df['MA50'] = moving_average(df['Close'], 50)
        df['MACD'], df['Signal'], df['Hist'] = macd(df['Close'])
        df['RSI'] = rsi(df['Close'])

        # Plot Price & MA
        fig_price = go.Figure()
        fig_price.add_trace(go.Candlestick(x=df.index,
                        open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'], name='OHLC'))
        fig_price.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='MA 20'))
        fig_price.add_trace(go.Scatter(x=df.index, y=df['MA50'], line=dict(color='blue', width=1), name='MA 50'))
        fig_price.update_layout(title="Price & Moving Averages", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig_price, use_container_width=True)

        col_left, col_right = st.columns(2)

        with col_left:
            # Plot MACD
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='blue', width=1), name='MACD'))
            fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'], line=dict(color='orange', width=1), name='Signal'))
            fig_macd.add_trace(go.Bar(x=df.index, y=df['Hist'], name='Histogram'))
            fig_macd.update_layout(title="MACD", height=300)
            st.plotly_chart(fig_macd, use_container_width=True)

        with col_right:
            # Plot RSI
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=1), name='RSI'))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
            fig_rsi.update_layout(title="RSI", height=300, yaxis=dict(range=[0, 100]))
            st.plotly_chart(fig_rsi, use_container_width=True)

        # Peers Comparison
        st.subheader("Peers Comparison")
        # Ideally, this comes from parser.py or a DB.
        # Using parser to fetch peers dynamically
        with st.spinner("Fetching peers..."):
            peers_list = get_peers(ticker)
        
        # Fallback if no peers found
        if not peers_list:
            peers_list = [ticker]
            if "2330" in ticker:
                peers_list.extend(["2303.TW", "2454.TW", "2317.TW"])
            elif "2603" in ticker: # Shipping
                peers_list.extend(["2609.TW", "2615.TW"])
        
        # Ensure current ticker is in the list for comparison
        if ticker not in peers_list:
            peers_list.insert(0, ticker)
        
        peers_df = build_peers_dataframe(peers_list)
        st.dataframe(peers_df)

        # News Sentiment
        st.subheader("News Sentiment")
        t = get_ticker(ticker)
        news = t.news
        if news:
            for n in news[:5]: # Show top 5
                title = n.get('title')
                link = n.get('link')
                sentiment = sentiment_score_chinese(title)
                st.write(f"**[{title}]({link})**")
                st.progress(sentiment, text=f"Sentiment: {sentiment:.2f}")
        else:
            st.write("No news found.")

        # Show Raw Data
        with st.expander("View Raw Data"):
            st.dataframe(df)
            
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")

