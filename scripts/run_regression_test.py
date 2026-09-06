import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Ensure project root is on sys.path so `import app` works
sys.path.insert(0, str(ROOT))
import os
# Ensure pytest imports see the backend package as top-level `app`
os.environ.setdefault("PYTHONPATH", str(ROOT / "backend"))
# Also ensure the backend dir is on sys.path for immediate imports
sys.path.insert(0, str(ROOT / "backend"))

import pytest

if __name__ == '__main__':
    pytest.main(["-q", "backend/tests/test_semantic_regression.py::test_regression_retrieves_test_a_and_respects_tenant_isolation"])