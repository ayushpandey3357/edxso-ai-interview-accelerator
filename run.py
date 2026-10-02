import os
import subprocess
import sys
from app.database import Database

def main():
    print("Initializing SQLite Database...")
    db = Database()
    print("Database initialized successfully.")
    
    print("Launching Streamlit Dashboard...")
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
    cmd = [sys.executable, "-m", "streamlit", "run", dashboard_path]
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
