"""Launch SkyjarBot from the project root."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.main import main

if __name__ == "__main__":
    main()
