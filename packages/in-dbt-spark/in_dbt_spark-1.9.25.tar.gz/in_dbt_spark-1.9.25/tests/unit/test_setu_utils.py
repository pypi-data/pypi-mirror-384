"""Unit tests for dbt.adapters.setu.utils module."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Mock the modules that aren't needed for our specific tests
sys.modules['pandas'] = MagicMock()
sys.modules['dbt.adapters.events.logging'] = MagicMock()
sys.modules['dbt.adapters.setu.imports'] = MagicMock()
sys.modules['dbt.adapters.setu.models'] = MagicMock()

# Mock constants with our DAG_CONFIG_MAPPINGS
mock_constants = MagicMock()
mock_constants.DAG_CONFIG_MAPPINGS = [
    ("POOL", "spark.hadoop.pool"),
    ("TASK_ID", "spark.hadoop.task.id"),
    ("TASK_URN", "spark.hadoop.task.urn"),
    ("DAG_ID", "spark.hadoop.dag.id"),
    ("DAG_URN", "spark.hadoop.dag.urn"),
    ("CLUSTER_ID", "spark.hadoop.cluster.id"),
    ("DAG_RUN_URN", "spark.hadoop.dag.run.urn"),
    ("TASK_RUN_URN", "spark.hadoop.task.run.urn"),
    ("ORCHESTRATOR", "spark.hadoop.orchestrator"),
    ("SPARK_YARN_TAG", "spark.yarn.tags")
]
mock_constants.DEFAULT_SPARK_CONF = {}
mock_constants.SPARK_CONF_APPEND_KEYS = []
sys.modules['dbt.adapters.setu.constants'] = mock_constants

# Now import our functions after mocking the dependencies  
from dbt.adapters.setu.utils import gather_dag_configs_for_yarn_tags, set_spark_conf_with_defaults


class TestGatherDagConfigsForYarnTags(unittest.TestCase):
    """Test the gather_dag_configs_for_yarn_tags function."""

    def test_empty_environment_returns_empty_string(self):
        """Test that no environment variables returns empty string."""
        with patch.dict(os.environ, {}, clear=True):
            result = gather_dag_configs_for_yarn_tags()
            self.assertEqual(result, "")

    def test_single_dag_config_creates_tag(self):
        """Test that a single DAG config creates a proper tag."""
        with patch.dict(os.environ, {"DAG_ID": "test_dag_id"}, clear=True):
            result = gather_dag_configs_for_yarn_tags()
            self.assertEqual(result, "dag.id:test_dag_id")

    def test_multiple_dag_configs_create_comma_separated_tags(self):
        """Test that multiple DAG configs create comma-separated tags."""
        env_vars = {
            "DAG_ID": "test_dag_id", 
            "DAG_URN": "urn:li:airflowDag:(mp=test,dag=test_dag)",
            "TASK_ID": "test_task_id"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            result = gather_dag_configs_for_yarn_tags()
            expected_tags = [
                "dag.id:test_dag_id",
                "dag.urn:urn:li:airflowDag:(mp=test,dag=test_dag)",
                "task.id:test_task_id"
            ]
            # Check that all expected tags are present
            for tag in expected_tags:
                self.assertIn(tag, result)
            # Check format is comma-separated
            self.assertEqual(len(result.split(", ")), 3)

    def test_all_dag_config_mappings(self):
        """Test all possible DAG config mappings from constants."""
        env_vars = {
            "POOL": "test_pool",
            "TASK_ID": "test_task_id",
            "TASK_URN": "urn:li:task:test",
            "DAG_ID": "test_dag_id",
            "DAG_URN": "urn:li:dag:test",
            "CLUSTER_ID": "test_cluster",
            "DAG_RUN_URN": "urn:li:dagrun:test",
            "TASK_RUN_URN": "urn:li:taskrun:test",
            "ORCHESTRATOR": "airflow"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            result = gather_dag_configs_for_yarn_tags()
            expected_tags = [
                "pool:test_pool",
                "task.id:test_task_id",
                "task.urn:urn:li:task:test",
                "dag.id:test_dag_id", 
                "dag.urn:urn:li:dag:test",
                "cluster.id:test_cluster",
                "dag.run.urn:urn:li:dagrun:test",
                "task.run.urn:urn:li:taskrun:test",
                "orchestrator:airflow"
            ]
            # Check that all expected tags are present
            for tag in expected_tags:
                self.assertIn(tag, result)

    def test_yarn_tags_env_var_skipped(self):
        """Test that SPARK_YARN_TAG env var is skipped in tag generation."""
        env_vars = {
            "DAG_ID": "test_dag_id",
            "SPARK_YARN_TAG": "existing_tag:value"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            result = gather_dag_configs_for_yarn_tags()
            # Should only contain dag.id, not the SPARK_YARN_TAG value
            self.assertEqual(result, "dag.id:test_dag_id")

    def test_non_hadoop_configs_skipped(self):
        """Test that non-hadoop spark configs are skipped."""
        # This test ensures only spark.hadoop.* configs are processed
        with patch.dict(os.environ, {"DAG_ID": "test_dag_id"}, clear=True):
            result = gather_dag_configs_for_yarn_tags()
            # DAG_ID maps to spark.hadoop.dag.id, so should be included
            self.assertEqual(result, "dag.id:test_dag_id")


class TestSetSparkConfWithDefaults(unittest.TestCase):
    """Test the set_spark_conf_with_defaults function with yarn tags integration."""

    def test_dag_tags_added_to_spark_conf(self):
        """Test that DAG tags are added to spark.yarn.tags in spark conf."""
        spark_conf = {}
        env_vars = {
            "DAG_ID": "test_dag_id",
            "TASK_ID": "test_task_id"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            result = set_spark_conf_with_defaults(spark_conf)
            
            # Check that spark.yarn.tags is set
            self.assertIn("spark.yarn.tags", result)
            self.assertIn("dag.id:test_dag_id", result["spark.yarn.tags"])
            self.assertIn("task.id:test_task_id", result["spark.yarn.tags"])

    def test_existing_yarn_tags_env_var_combined(self):
        """Test that existing SPARK_YARN_TAG env var is combined with DAG tags."""
        spark_conf = {}
        env_vars = {
            "DAG_ID": "test_dag_id",
            "SPARK_YARN_TAG": "existing:tag"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            result = set_spark_conf_with_defaults(spark_conf)
            
            # Check that both existing and new tags are present
            self.assertIn("spark.yarn.tags", result)
            yarn_tags = result["spark.yarn.tags"]
            self.assertIn("existing:tag", yarn_tags)
            self.assertIn("dag.id:test_dag_id", yarn_tags)

    def test_individual_hadoop_configs_still_set(self):
        """Test that individual hadoop configs are still set as before."""
        spark_conf = {}
        env_vars = {
            "DAG_ID": "test_dag_id",
            "POOL": "test_pool"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            result = set_spark_conf_with_defaults(spark_conf)
            
            # Check individual configs are set
            self.assertEqual(result["spark.hadoop.dag.id"], "test_dag_id")
            self.assertEqual(result["spark.hadoop.pool"], "test_pool")
            
            # Check yarn tags are also set
            self.assertIn("spark.yarn.tags", result)

    def test_no_dag_configs_no_yarn_tags(self):
        """Test that no DAG configs means no spark.yarn.tags is set."""
        spark_conf = {}
        
        with patch.dict(os.environ, {}, clear=True):
            result = set_spark_conf_with_defaults(spark_conf)
            
            # Check that spark.yarn.tags is not set when no DAG configs
            self.assertNotIn("spark.yarn.tags", result)

    def test_only_yarn_tag_env_var_no_hadoop_configs(self):
        """Test behavior when only SPARK_YARN_TAG is set without hadoop configs."""
        spark_conf = {}
        env_vars = {"SPARK_YARN_TAG": "existing:tag"}
        
        with patch.dict(os.environ, env_vars, clear=True):
            result = set_spark_conf_with_defaults(spark_conf)
            
            # Should have the SPARK_YARN_TAG value set directly
            self.assertEqual(result["spark.yarn.tags"], "existing:tag")

    def test_conf_prefix_handling_preserved(self):
        """Test that existing conf. prefix handling is preserved."""
        spark_conf = {"conf.spark.sql.adaptive.enabled": "true"}
        
        with patch.dict(os.environ, {}, clear=True):
            result = set_spark_conf_with_defaults(spark_conf)
            
            # Check that conf. prefix is removed
            self.assertIn("spark.sql.adaptive.enabled", result)
            self.assertNotIn("conf.spark.sql.adaptive.enabled", result)
            self.assertEqual(result["spark.sql.adaptive.enabled"], "true")


if __name__ == "__main__":
    unittest.main()
