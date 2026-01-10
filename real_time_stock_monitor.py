"""
即時股市資訊監控系統
Real-time Stock Market Information Monitor
支援台灣股市即時資料讀取與分析
"""

import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional
import json

class RealTimeStockMonitor:
    """即時股市監控系統"""
    
    def __init__(self):
        self.watched_stocks = []
        self.stock_data = {}
        
    def add_tw_stock(self, stock_code: str, stock_name: str = ""):
        """
        加入台灣股票到監控列表
        
        Args:
            stock_code: 股票代碼（4位數字）
            stock_name: 股票名稱（選填）
        """
        # 台灣股票需要加上 .TW 後綴
        if not stock_code.endswith('.TW') and not stock_code.endswith('.TWO'):
            if len(stock_code) == 4:
                stock_code = f"{stock_code}.TW"
        
        self.watched_stocks.append({
            'code': stock_code,
            'name': stock_name or stock_code
        })
        print(f"✓ 已加入監控：{stock_name or stock_code} ({stock_code})")
    
    def get_latest_price(self, stock_code: str) -> Optional[Dict]:
        """
        獲取最新股價資訊
        
        Args:
            stock_code: 股票代碼
            
        Returns:
            包含股價資訊的字典
        """
        try:
            ticker = yf.Ticker(stock_code)
            
            # 獲取即時資料
            info = ticker.info
            hist = ticker.history(period='5d')
            
            if hist.empty:
                print(f"⚠ 警告：無法獲取 {stock_code} 的歷史資料")
                return None
            
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            # 計算漲跌
            change = latest['Close'] - previous['Close']
            change_percent = (change / previous['Close']) * 100
            
            data = {
                'code': stock_code,
                'name': info.get('longName', stock_code),
                'current_price': latest['Close'],
                'open': latest['Open'],
                'high': latest['High'],
                'low': latest['Low'],
                'volume': latest['Volume'],
                'previous_close': previous['Close'],
                'change': change,
                'change_percent': change_percent,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return data
            
        except Exception as e:
            print(f"✗ 錯誤：無法獲取 {stock_code} 的資料 - {str(e)}")
            return None
    
    def get_detailed_info(self, stock_code: str) -> Optional[Dict]:
        """
        獲取股票詳細資訊
        
        Args:
            stock_code: 股票代碼
            
        Returns:
            詳細資訊字典
        """
        try:
            ticker = yf.Ticker(stock_code)
            info = ticker.info
            
            detailed = {
                '公司名稱': info.get('longName', 'N/A'),
                '產業': info.get('industry', 'N/A'),
                '市值': self._format_number(info.get('marketCap', 0)),
                '本益比 (P/E)': round(info.get('trailingPE', 0), 2),
                '股息殖利率': f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') else 'N/A',
                '52週最高': info.get('fiftyTwoWeekHigh', 'N/A'),
                '52週最低': info.get('fiftyTwoWeekLow', 'N/A'),
                '平均成交量': self._format_number(info.get('averageVolume', 0)),
            }
            
            return detailed
            
        except Exception as e:
            print(f"✗ 錯誤：無法獲取詳細資訊 - {str(e)}")
            return None
    
    def get_technical_indicators(self, stock_code: str, period: str = '1mo') -> Optional[Dict]:
        """
        計算技術指標
        
        Args:
            stock_code: 股票代碼
            period: 資料期間
            
        Returns:
            技術指標字典
        """
        try:
            ticker = yf.Ticker(stock_code)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return None
            
            # 計算移動平均線
            ma5 = hist['Close'].rolling(window=5).mean().iloc[-1]
            ma10 = hist['Close'].rolling(window=10).mean().iloc[-1]
            ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            
            # 計算RSI
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_price = hist['Close'].iloc[-1]
            
            indicators = {
                'MA5': round(ma5, 2),
                'MA10': round(ma10, 2),
                'MA20': round(ma20, 2),
                'RSI': round(rsi.iloc[-1], 2),
                '當前價格': round(current_price, 2),
                '相對MA5': '↑ 多頭' if current_price > ma5 else '↓ 空頭',
                '相對MA20': '↑ 多頭' if current_price > ma20 else '↓ 空頭',
                'RSI狀態': self._get_rsi_status(rsi.iloc[-1])
            }
            
            return indicators
            
        except Exception as e:
            print(f"✗ 錯誤：無法計算技術指標 - {str(e)}")
            return None
    
    def _get_rsi_status(self, rsi: float) -> str:
        """判斷RSI狀態"""
        if rsi > 70:
            return "超買 (>70)"
        elif rsi < 30:
            return "超賣 (<30)"
        else:
            return "正常 (30-70)"
    
    def _format_number(self, num: float) -> str:
        """格式化大數字"""
        if num >= 1e12:
            return f"{num/1e12:.2f}兆"
        elif num >= 1e8:
            return f"{num/1e8:.2f}億"
        elif num >= 1e4:
            return f"{num/1e4:.2f}萬"
        else:
            return f"{num:,.0f}"
    
    def print_stock_info(self, stock_code: str):
        """
        印出完整股票資訊
        
        Args:
            stock_code: 股票代碼
        """
        print("\n" + "="*80)
        print(f"📊 股票資訊：{stock_code}")
        print("="*80)
        
        # 最新價格
        price_data = self.get_latest_price(stock_code)
        if price_data:
            print(f"\n【即時報價】")
            print(f"公司名稱：{price_data['name']}")
            print(f"當前價格：${price_data['current_price']:.2f}")
            print(f"漲跌：{price_data['change']:+.2f} ({price_data['change_percent']:+.2f}%)")
            print(f"開盤：${price_data['open']:.2f}")
            print(f"最高：${price_data['high']:.2f}")
            print(f"最低：${price_data['low']:.2f}")
            print(f"成交量：{self._format_number(price_data['volume'])}")
            print(f"更新時間：{price_data['timestamp']}")
        
        # 詳細資訊
        detailed = self.get_detailed_info(stock_code)
        if detailed:
            print(f"\n【詳細資訊】")
            for key, value in detailed.items():
                print(f"{key}：{value}")
        
        # 技術指標
        indicators = self.get_technical_indicators(stock_code)
        if indicators:
            print(f"\n【技術指標】")
            for key, value in indicators.items():
                print(f"{key}：{value}")
        
        print("="*80)
    
    def monitor_all_stocks(self):
        """監控所有已加入的股票"""
        if not self.watched_stocks:
            print("⚠ 監控列表為空，請先加入股票")
            return
        
        print("\n" + "="*80)
        print(f"📈 監控股票列表（共 {len(self.watched_stocks)} 檔）")
        print("="*80)
        print(f"{'股票代碼':<15} {'名稱':<20} {'當前價格':<12} {'漲跌':<12} {'漲跌幅':<12}")
        print("-"*80)
        
        for stock in self.watched_stocks:
            data = self.get_latest_price(stock['code'])
            if data:
                change_symbol = "🔴" if data['change'] < 0 else "🟢" if data['change'] > 0 else "⚪"
                print(f"{stock['code']:<15} {stock['name']:<20} ${data['current_price']:<11.2f} "
                      f"{data['change']:+.2f}     {change_symbol} {data['change_percent']:+.2f}%")
        
        print("="*80)
        print(f"更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    def continuous_monitor(self, interval: int = 60):
        """
        持續監控模式
        
        Args:
            interval: 更新間隔（秒）
        """
        print(f"🔄 開始持續監控（每{interval}秒更新一次，按Ctrl+C停止）")
        
        try:
            while True:
                self.monitor_all_stocks()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n⏹ 監控已停止")


def demo_basic_monitoring():
    """基本監控示範"""
    print("="*80)
    print("🚀 即時股市資訊監控系統 - 基本示範")
    print("="*80)
    
    monitor = RealTimeStockMonitor()
    
    # 加入熱門台股
    monitor.add_tw_stock("2330", "台積電")
    monitor.add_tw_stock("2317", "鴻海")
    monitor.add_tw_stock("2454", "聯發科")
    monitor.add_tw_stock("2603", "長榮")
    monitor.add_tw_stock("2618", "長榮航")
    
    # 顯示監控列表
    monitor.monitor_all_stocks()
    
    # 顯示單一股票詳細資訊
    monitor.print_stock_info("2330.TW")


def demo_custom_monitoring():
    """自訂監控示範"""
    print("="*80)
    print("🎯 即時股市資訊監控系統 - 自訂監控")
    print("="*80)
    
    monitor = RealTimeStockMonitor()
    
    while True:
        print("\n請選擇操作：")
        print("1. 加入股票到監控列表")
        print("2. 查看監控列表")
        print("3. 查看單一股票詳細資訊")
        print("4. 開始持續監控")
        print("5. 退出")
        
        choice = input("\n請輸入選項 (1-5): ").strip()
        
        if choice == '1':
            code = input("請輸入股票代碼（4位數字）: ").strip()
            name = input("請輸入股票名稱（選填）: ").strip()
            monitor.add_tw_stock(code, name)
            
        elif choice == '2':
            monitor.monitor_all_stocks()
            
        elif choice == '3':
            code = input("請輸入股票代碼: ").strip()
            if not code.endswith('.TW'):
                code = f"{code}.TW"
            monitor.print_stock_info(code)
            
        elif choice == '4':
            interval = input("請輸入更新間隔（秒，預設60）: ").strip()
            interval = int(interval) if interval.isdigit() else 60
            monitor.continuous_monitor(interval)
            
        elif choice == '5':
            print("👋 感謝使用！")
            break
            
        else:
            print("❌ 無效的選項，請重新輸入")


if __name__ == "__main__":
    print("\n請選擇執行模式：")
    print("1. 基本示範（預設監控熱門股票）")
    print("2. 自訂監控（手動加入股票）")
    
    mode = input("\n請輸入選項 (1-2): ").strip()
    
    if mode == '2':
        demo_custom_monitoring()
    else:
        demo_basic_monitoring()
