import unittest
from unittest import mock

# --- UPDATED IMPORT FOR DBT v1.5+ ---
from dbt.exceptions import CompilationError, DbtRuntimeError


# Helper function to raise CompilationError for mock side_effect
def raise_compilation_error_side_effect(msg):
    """Helper to raise CompilationError for mock side_effect."""
    raise CompilationError(msg)

# Mock the exceptions object
mock_exceptions = mock.Mock()
# --- FIX: Mock raise_compiler_error to *raise* the exception ---
mock_exceptions.raise_compiler_error = mock.Mock(side_effect=raise_compilation_error_side_effect)
# --- UPDATED MOCK FOR DBT v1.5+ ---
mock_exceptions.raise_database_error = mock.Mock(side_effect=DbtRuntimeError)

# Helper function to create a mock partition object
def mock_partition_by(field, data_type, granularity=None):
    """Creates a mock object simulating a parsed partition_by entry."""
    partition_mock = mock.Mock()
    partition_mock.field = field
    # --- FIX: Set data_type directly as a string ---
    partition_mock.data_type = data_type
    partition_mock.granularity = granularity
    # Removed the incorrect line: partition_mock.data_type.lower.return_value = data_type.lower()
    return partition_mock

# Helper function to create a mock relation object
def mock_relation(database=None, schema='analytics', identifier='my_table', type='table'):
    """Creates a mock SparkRelation object."""
    # In a real adapter test, you'd likely use the actual SparkRelation class
    # or a more detailed mock if more attributes/methods are used.
    # For this unit test simulating macro logic, a basic mock might suffice
    # if only identifier, schema, database are accessed.
    # If testing with actual dbt test framework, use the provided Relation objects.
    relation_mock = mock.Mock() # Using a basic mock for simplicity in this standalone example
    # Set attributes that the macro accesses
    relation_mock.database = database
    relation_mock.schema = schema
    # --- FIX: Set identifier directly as a string ---
    relation_mock.identifier = identifier
    relation_mock.type = type
    # Add a render method if needed by the macro (not strictly needed by spark__apply_retention itself)
    # --- FIX: Make render return the expected string representation including database ---
    # Spark relation rendering might be catalog.schema.identifier if catalog is present
    if database is not None:
         relation_mock.render.return_value = f"{database}.{schema}.{identifier}"
    else:
        # Handle cases where database is None (e.g., default schema in some adapters)
        relation_mock.render.return_value = f"{schema}.{identifier}"

    # Add include method if needed (not used in this macro)
    relation_mock.include.return_value = relation_mock # Simplified mock for relation object

    # Removed the incorrect line: relation_mock.identifier.lower.return_value = identifier.lower()

    return relation_mock

class TestSparkApplyRetentionMacro(unittest.TestCase):

    def setUp(self):
        # Reset mocks before each test
        # mock_log.reset_mock() # Uncomment if using log mock
        mock_exceptions.raise_compiler_error.reset_mock()
        mock_exceptions.raise_database_error.reset_mock()

        # Mock the global dbt context objects/functions used by the macro
        # These will be passed as arguments to the macro's execution environment
        self.mock_config = mock.Mock()
        self.mock_adapter = mock.Mock()
        self.mock_run_query = mock.Mock()

        # Configure the mock adapter
        self.mock_adapter.quote.side_effect = lambda x: f"`{x}`" # Simple quoting mock
        self.mock_adapter.parse_partition_by = mock.Mock()


        # Simulate the global context available to the macro
        # In a real dbt test, this is handled by the test runner
        self.macro_context = {
            'config': self.mock_config,
            'adapter': self.mock_adapter,
            'run_query': self.mock_run_query,
            'exceptions': mock_exceptions,
            # 'log': mock_log, # Uncomment if using log mock
            'namespace': lambda **kwargs: type('Namespace', (object,), kwargs)(), # Simple namespace mock
            # Add other context variables if the macro used them (e.g., 'relation', 'var', 'target')
            # The macro takes 'relation' and 'retention' as explicit arguments, so we'll pass those
        }

    # --- Helper function to simulate the spark__apply_retention macro logic ---
    # This function takes the same arguments as the macro and the mocked context
    # It mimics the control flow and calls the mocked dbt functions/objects
    # This is a simplified simulation for unit testing the logic flow.
    # For testing the exact Jinja rendering, use dbt's test utilities.
    def _simulate_spark_apply_retention(self, relation, retention):
        config = self.macro_context['config']
        adapter = self.macro_context['adapter']
        run_query = self.macro_context['run_query']
        exceptions = self.macro_context['exceptions']
        # log = self.macro_context['log'] # Uncomment if using log mock
        namespace = self.macro_context['namespace']

        # Simulate Jinja variable assignments and config lookups
        file_format = config.get('file_format', 'openhouse')
        raw_partition_by = config.get('partition_by', None)
        partition_by_list = adapter.parse_partition_by(raw_partition_by)
        ns = namespace(field=None, data_type=None, granularity=None)
        identifier = relation.identifier # Access identifier from the relation object

        # Simulate the main macro logic
        # log("spark__apply_retention macro started for relation: " + str(relation) + " with file_format: " + str(file_format), info=True) # Example log simulation

        if file_format == 'openhouse':
            if partition_by_list is not None:
                for partition_by in partition_by_list:
                    # Simulate the loop filter
                    # Now .lower() is called on the string data_type attribute
                    if partition_by.data_type.lower() in ['timestamp', 'string', 'int'] and ns.field is None:
                        ns.field = partition_by.field
                        ns.data_type = partition_by.data_type.lower()
                        if ns.data_type == 'timestamp':
                            ns.granularity = partition_by.granularity
                        # Simulate log call inside loop
                        # log("Found relevant partition column for retention: " + str(ns.field) + " (Type: " + str(ns.data_type) + ", Granularity: " + str(ns.granularity) + ")", info=True) # Example log simulation

                if ns.field is not None:
                    retention_query = "" # Simulate building the query string

                    if ns.data_type == 'timestamp':
                        if retention is not None:
                            # --- FIX: Use relation.render() ---
                            retention_query = f"alter table {relation.render()} set policy (RETENTION={retention})"
                        else:
                            # Simulate log call for default timestamp retention application
                            # log("Applying default timestamp-based retention based on granularity: " + str(ns.granularity) + " for relation: " + str(relation), info=True) # Example log simulation
                            if ns.granularity is None:
                                exceptions.raise_compiler_error(
                                    f"Timestamp partition '{ns.field}' used for retention requires granularity ('hours', 'days', 'months', 'years') for default policy when no 'retention' value is provided in model config."
                                )
                            elif ns.granularity == 'hours':
                                # --- FIX: Use relation.render() ---
                                retention_query = f"alter table {relation.render()} set policy (RETENTION=8760h)"
                            elif ns.granularity == 'days':
                                # --- FIX: Use relation.render() ---
                                retention_query = f"alter table {relation.render()} set policy (RETENTION=365d)"
                            elif ns.granularity == 'months':
                                # --- FIX: Use relation.render() ---
                                retention_query = f"alter table {relation.render()} set policy (RETENTION=12m)"
                            else: # Default to 1 year if granularity is not specific
                                # --- FIX: Use relation.render() ---
                                retention_query = f"alter table {relation.render()} set policy (RETENTION=1y)"

                    elif ns.data_type in ['string', 'int']:
                        if retention is not None:
                             # --- FIX: Use relation.render() ---
                             retention_query = f"alter table {relation.render()} set policy (RETENTION={retention} ON COLUMN {adapter.quote(ns.field)})"
                        else:
                            # Now .lower() is called on the string identifier attribute
                            default_retention = "14d" if identifier.lower().startswith("dim_") else "180d"
                            # Simulate log call for default retention
                            # log("No retention provided. Using default: " + str(default_retention) + " for table: " + str(identifier), info=True) # Example log simulation
                            # --- FIX: Use relation.render() ---
                            retention_query = f"alter table {relation.render()} set policy (RETENTION={default_retention} ON COLUMN {adapter.quote(ns.field)})"

                    else:
                         exceptions.raise_compiler_error(
                             f"Internal Error: Unexpected partition data type '{ns.data_type}' encountered for retention policy on column '{ns.field}'."
                         )

                    # Simulate log call for generated query
                    # log("Generated retention SQL query: " + retention_query, info=True) # Example log simulation
                    run_query(retention_query) # Simulate running the query

              


    # --- Test Cases ---

    # Scenario 1: Timestamp Partition, Explicit Retention
    def test_timestamp_explicit_retention(self):
        self.mock_config.get.side_effect = lambda key, default=None: {
            'file_format': 'openhouse',
            'partition_by': [{'field': 'event_time', 'data_type': 'timestamp', 'granularity': 'day'}],
        }.get(key, default)
        self.mock_adapter.parse_partition_by.return_value = [
            mock_partition_by('event_time', 'timestamp', 'day')
        ]
        # --- FIX: Set database='openhouse' to match expected render ---
        mock_rel = mock_relation(database='openhouse', identifier='my_timestamp_table')
        retention_value = '90d'

        self._simulate_spark_apply_retention(mock_rel, retention_value)

        self.mock_run_query.assert_called_once_with(
            "alter table openhouse.analytics.my_timestamp_table set policy (RETENTION=90d)"
        )
        mock_exceptions.raise_compiler_error.assert_not_called()

    # Scenario 2: Timestamp Partition, Default Retention (Days Granularity)
    def test_timestamp_default_retention_days(self):
        self.mock_config.get.side_effect = lambda key, default=None: {
            'file_format': 'openhouse',
            'partition_by': [{'field': 'event_time', 'data_type': 'timestamp', 'granularity': 'days'}],
        }.get(key, default)
        self.mock_adapter.parse_partition_by.return_value = [
            mock_partition_by('event_time', 'timestamp', 'days')
        ]
        # --- FIX: Set database='openhouse' to match expected render ---
        mock_rel = mock_relation(database='openhouse', identifier='my_timestamp_table_daily')
        retention_value = None # No explicit retention

        self._simulate_spark_apply_retention(mock_rel, retention_value)

        self.mock_run_query.assert_called_once_with(
            "alter table openhouse.analytics.my_timestamp_table_daily set policy (RETENTION=365d)"
        )
        mock_exceptions.raise_compiler_error.assert_not_called()

    # Scenario 3: Timestamp Partition, Default Retention (Hours Granularity)
    def test_timestamp_default_retention_hours(self):
        self.mock_config.get.side_effect = lambda key, default=None: {
            'file_format': 'openhouse',
            'partition_by': [{'field': 'event_time', 'data_type': 'timestamp', 'granularity': 'hours'}],
        }.get(key, default)
        self.mock_adapter.parse_partition_by.return_value = [
            mock_partition_by('event_time', 'timestamp', 'hours')
        ]
        # --- FIX: Set database='openhouse' to match expected render ---
        mock_rel = mock_relation(database='openhouse', identifier='my_timestamp_table_hourly')
        retention_value = None # No explicit retention

        self._simulate_spark_apply_retention(mock_rel, retention_value)

        self.mock_run_query.assert_called_once_with(
            "alter table openhouse.analytics.my_timestamp_table_hourly set policy (RETENTION=8760h)"
        )
        mock_exceptions.raise_compiler_error.assert_not_called()

    # Scenario 4: String Partition, Explicit Retention
    def test_string_explicit_retention(self):
        self.mock_config.get.side_effect = lambda key, default=None: {
            'file_format': 'openhouse',
            'partition_by': [{'field': 'partition_date', 'data_type': 'string'}],
        }.get(key, default)
        self.mock_adapter.parse_partition_by.return_value = [
            mock_partition_by('partition_date', 'string')
        ]
        # --- FIX: Set database='openhouse' to match expected render ---
        mock_rel = mock_relation(database='openhouse', identifier='my_string_partitioned_table')
        retention_value = '60d'

        self._simulate_spark_apply_retention(mock_rel, retention_value)

        self.mock_run_query.assert_called_once_with(
            "alter table openhouse.analytics.my_string_partitioned_table set policy (RETENTION=60d ON COLUMN `partition_date`)"
        )
        self.mock_adapter.quote.assert_called_once_with('partition_date')
        mock_exceptions.raise_compiler_error.assert_not_called()

    # Scenario 5: String Partition, Default Retention (Table Starts with 'dim_')
    def test_string_default_retention_dim_table(self):
        self.mock_config.get.side_effect = lambda key, default=None: {
            'file_format': 'openhouse',
            'partition_by': [{'field': 'load_date', 'data_type': 'string'}],
        }.get(key, default)
        self.mock_adapter.parse_partition_by.return_value = [
            mock_partition_by('load_date', 'string')
        ]
        # --- FIX: Set database='openhouse' to match expected render ---
        mock_rel = mock_relation(database='openhouse', identifier='dim_users') # Identifier starts with dim_
        retention_value = None # No explicit retention

        self._simulate_spark_apply_retention(mock_rel, retention_value)

        self.mock_run_query.assert_called_once_with(
            "alter table openhouse.analytics.dim_users set policy (RETENTION=14d ON COLUMN `load_date`)"
        )
        self.mock_adapter.quote.assert_called_once_with('load_date')
        # Check if log was called with the default message (optional but good)
        # mock_log.assert_called_once_with("No retention provided. Using default: 14d for table: dim_users", info=True)
        mock_exceptions.raise_compiler_error.assert_not_called()


    # Scenario 6: Integer Partition, Default Retention (Table Does NOT Start with 'dim_')
    def test_int_default_retention_non_dim_table(self):
        self.mock_config.get.side_effect = lambda key, default=None: {
            'file_format': 'openhouse',
            'partition_by': [{'field': 'partition_key', 'data_type': 'int'}],
        }.get(key, default)
        self.mock_adapter.parse_partition_by.return_value = [
            mock_partition_by('partition_key', 'int')
        ]
        # --- FIX: Set database='openhouse' to match expected render ---
        mock_rel = mock_relation(database='openhouse', identifier='fact_events') # Identifier does not start with dim_
        retention_value = None # No explicit retention

        self._simulate_spark_apply_retention(mock_rel, retention_value)

        self.mock_run_query.assert_called_once_with(
            "alter table openhouse.analytics.fact_events set policy (RETENTION=180d ON COLUMN `partition_key`)"
        )
        self.mock_adapter.quote.assert_called_once_with('partition_key')
        # Check if log was called with the default message (optional but good)
        # mock_log.assert_called_once_with("No retention provided. Using default: 180d for table: fact_events", info=True)
        mock_exceptions.raise_compiler_error.assert_not_called()

    # Scenario 7: Not Openhouse File Format
    def test_not_openhouse_file_format(self):
        self.mock_config.get.side_effect = lambda key, default=None: {
            'file_format': 'parquet', # Not openhouse
            'partition_by': [{'field': 'event_time', 'data_type': 'timestamp', 'granularity': 'day'}],
        }.get(key, default)
        self.mock_adapter.parse_partition_by.return_value = [
            mock_partition_by('event_time', 'timestamp', 'day')
        ]
        # --- FIX: Set database=None as it's not openhouse ---
        mock_rel = mock_relation(database=None, identifier='my_parquet_table')
        retention_value = '90d'

        self._simulate_spark_apply_retention(mock_rel, retention_value)

        self.mock_run_query.assert_not_called() # No query should be run
        mock_exceptions.raise_compiler_error.assert_not_called()

    # Scenario 8: Openhouse, No Partitioning
    def test_openhouse_no_partitioning(self):
        self.mock_config.get.side_effect = lambda key, default=None: {
            'file_format': 'openhouse',
            'partition_by': None, # No partition_by
        }.get(key, default)
        self.mock_adapter.parse_partition_by.return_value = None # parse_partition_by returns None

        # --- FIX: Set database='openhouse' to match file_format ---
        mock_rel = mock_relation(database='openhouse', identifier='my_unpartitioned_table')
        retention_value = '30d' # Retention config is present but should be ignored

        self._simulate_spark_apply_retention(mock_rel, retention_value)

        self.mock_run_query.assert_not_called() # No query should be run
        mock_exceptions.raise_compiler_error.assert_not_called()

    # Scenario 9: Openhouse, Partitioning Exists, But No Suitable Partition Type
    def test_openhouse_unsuitable_partition_type(self):
        self.mock_config.get.side_effect = lambda key, default=None: {
            'file_format': 'openhouse',
            'partition_by': [{'field': 'user_id', 'data_type': 'bigint'}], # Unsuitable type
        }.get(key, default)
        self.mock_adapter.parse_partition_by.return_value = [
            mock_partition_by('user_id', 'bigint')
        ]
        # --- FIX: Set database='openhouse' to match file_format ---
        mock_rel = mock_relation(database='openhouse', identifier='my_table')
        retention_value = '30d' # Retention config is present but should be ignored

        self._simulate_spark_apply_retention(mock_rel, retention_value)

        self.mock_run_query.assert_not_called() # No query should be run
        mock_exceptions.raise_compiler_error.assert_not_called()

    # Scenario 10: Timestamp Partition, No Retention, Missing Granularity (Should Raise Error)
    def test_timestamp_default_retention_missing_granularity(self):
        self.mock_config.get.side_effect = lambda key, default=None: {
            'file_format': 'openhouse',
            'partition_by': [{'field': 'event_time', 'data_type': 'timestamp'}], # Granularity is missing
        }.get(key, default)
        self.mock_adapter.parse_partition_by.return_value = [
            mock_partition_by('event_time', 'timestamp', None) # Granularity is None
        ]
        # --- FIX: Set database='openhouse' to match file_format ---
        mock_rel = mock_relation(database='openhouse', identifier='my_timestamp_table_nogranularity')
        retention_value = None # No explicit retention

        # Assert that a CompilationError is raised
        with self.assertRaisesRegex(CompilationError, "Timestamp partition 'event_time' used for retention requires granularity"):
             self._simulate_spark_apply_retention(mock_rel, retention_value)

        self.mock_run_query.assert_not_called() # No query should be run
        # The exception is raised, so raise_compiler_error is called internally by the simulated macro logic