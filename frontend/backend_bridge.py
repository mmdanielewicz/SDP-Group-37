# frontend/backend_bridge.py
import os
import sys
from typing import Any, Dict

# --- Make project root importable ---
# backend_bridge.py is in: <project_root>/frontend/backend_bridge.py
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

#  import orchestration as a real package module
from src.orchestration.orchestration import main as orchestration_main


def handle_user_query(query: str, lat=41.2940, lon=-72.3768, state="CT"):
    """
    Wrapper that calls the existing backend orchestration.
    """
    try:
        result = orchestration_main(query)
    except Exception as e:
        return {"error": str(e), "query": query}

    return result
