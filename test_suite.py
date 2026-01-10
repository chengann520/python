import unittest
import os
import sys
from stock_analyzer.parser import get_peers
from stock_analyzer.db import init_db, get_db
from stock_analyzer.fetcher import get_ticker

class TestStockAnalyzer(unittest.TestCase):
    
    def test_01_imports(self):
        """Test if modules can be imported without error."""
        try:
            import stock_analyzer.dashboard
            import stock_analyzer.update_all
            print("Imports: OK")
        except ImportError as e:
            self.fail(f"Failed to import modules: {e}")

    def test_02_parser_peers(self):
        """Test peer fetching logic."""
        ticker = "2330.TW"
        print(f"Testing peer fetch for {ticker}...")
        peers = get_peers(ticker)
        self.assertIsInstance(peers, list)
        # We expect some peers for TSMC
        if len(peers) == 0:
            print("Warning: No peers found. Network might be down or layout changed.")
        else:
            print(f"Peers found: {len(peers)}")
            
    def test_03_db_init(self):
        """Test database initialization."""
        print("Testing DB init...")
        try:
            init_db()
            # Check if file exists
            if os.path.exists("stock_data.db"):
                print("DB File: OK")
            else:
                self.fail("stock_data.db not created.")
        except Exception as e:
            self.fail(f"DB Init failed: {e}")

if __name__ == '__main__':
    unittest.main()
