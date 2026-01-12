import sys
import os
import subprocess
from stock_analyzer.db import init_db
from stock_analyzer.update_all import update_all

import os
import certifi

# 這行代碼會自動抓取當前環境（不論是 Windows 還是 GitHub 的 Linux）的憑證位置
os.environ['SSL_CERT_FILE'] = certifi.where()

def run_dashboard():
    print("Starting Dashboard...")
    # Assuming dashboard.py is in stock_analyzer/dashboard.py
    dashboard_path = os.path.join("stock_analyzer", "dashboard.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path])

def main():
    while True:
        print("\n=== Stock Analyzer CLI ===")
        print("1. Run Dashboard")
        print("2. Update Data (Fetch & Save)")
        print("3. Initialize Database")
        print("4. Exit")
        
        choice = input("Select an option: ")
        
        if choice == "1":
            run_dashboard()
        elif choice == "2":
            update_all()
        elif choice == "3":
            print("Initializing database...")
            init_db()
            print("Database initialized.")
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":

    main()

