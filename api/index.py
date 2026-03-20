import sys
import os

# Add the project root to Python path so we can import from backend/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.server import app

# Vercel handler
handler = app
