"""
FinSecAI SOC Command Center - Streamlit Cloud Entry Point
"""

import subprocess
import sys
from pathlib import Path

# Run the main dashboard from dashboards folder
if __name__ == "__main__":
    dashboard_path = Path(__file__).resolve().parent / "dashboards" / "streamlit_app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_path)])
