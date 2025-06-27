# Helper module to add external repositories to sys.path in a cross-platform way

import sys
from pathlib import Path

def add_repo_to_path(relative_path):
    # Resolve absolute path based on the current file's location
    base_dir = Path(__file__).resolve().parent
    repo_path = (base_dir / relative_path).resolve()

    if str(repo_path) not in sys.path:
        sys.path.insert(0, str(repo_path))

# Add external repositories
add_repo_to_path('../OPOTEK')
add_repo_to_path('../autolab')

