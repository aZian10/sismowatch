import sys
from pathlib import Path

# Add airflow directory to sys.path so 'include' is importable directly
airflow_dir = Path(__file__).parents[1]
sys.path.insert(0, str(airflow_dir))
sys.path.insert(0, str(airflow_dir.parent))
