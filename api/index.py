import sys
from pathlib import Path

# Add the project root to Python path so we can import from backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.server import app
