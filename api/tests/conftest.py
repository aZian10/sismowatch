import sys
from pathlib import Path

# Add project root and api directory to sys.path
root_dir = Path(__file__).parents[2]
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "api"))
sys.path.insert(0, str(root_dir / "airflow"))
