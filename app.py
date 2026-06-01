"""
FinSecAI SOC Command Center - Streamlit Cloud Entry Point
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    # Import the Streamlit app module directly so Streamlit Cloud can execute it.
    import dashboards.streamlit_app  # noqa: F401
