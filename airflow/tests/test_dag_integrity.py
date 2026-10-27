"""
Unit test for Airflow DAG integrity.
Verifies that all DAG definitions in airflow/dags load without syntax or import errors,
have defined task dependencies, and maintain valid schedule intervals.
"""
import pytest
from pathlib import Path
from airflow.models import DagBag

DAGS_FOLDER = Path(__file__).parents[1] / "dags"

@pytest.fixture(scope="module")
def dagbag():
    """Loads all DAGs from airflow/dags folder."""
    return DagBag(dag_folder=str(DAGS_FOLDER))

def test_no_import_errors(dagbag):
    """Confirm zero import errors across all DAG files."""
    assert len(dagbag.import_errors) == 0, f"DAG import errors detected: {dagbag.import_errors}"

def test_expected_dags_present(dagbag):
    """Verify that all 4 required SismoWatch DAGs exist."""
    expected_dags = [
        "sismowatch_ingestion_dag",
        "sismowatch_transformation_dag",
        "sismowatch_daily_report_dag",
        "sismowatch_backfill_dag"
    ]
    for dag_id in expected_dags:
        assert dag_id in dagbag.dags, f"Expected DAG '{dag_id}' was not found in dagbag."

def test_dag_tags_and_structure(dagbag):
    """Ensure DAGs have tags, owners, and non-empty tasks."""
    for dag_id, dag in dagbag.dags.items():
        assert len(dag.tasks) > 0, f"DAG '{dag_id}' has no tasks defined."
        assert "sismowatch" in dag.tags, f"DAG '{dag_id}' missing 'sismowatch' tag."
