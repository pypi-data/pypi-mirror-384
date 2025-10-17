import unittest
from unittest import mock
import re  

from dbt.exceptions import CompilationError, DbtRuntimeError

# Helper function to raise CompilationError for mock side_effect
def _raise_compilation_error(msg):
    raise CompilationError(msg)

# Mock the exceptions object
mock_exceptions = mock.Mock()
mock_exceptions.raise_compiler_error = mock.Mock(side_effect=_raise_compilation_error)
mock_exceptions.raise_database_error = mock.Mock(side_effect=DbtRuntimeError)

# Helper to create a mock partition object
def mock_partition_by(field, data_type, granularity=None):
    m = mock.Mock()
    m.field = field
    m.data_type = data_type
    m.granularity = granularity
    return m



class TestSparkOpenhouseValidationMacro(unittest.TestCase):

    def setUp(self):
        mock_exceptions.raise_compiler_error.reset_mock()
        mock_exceptions.raise_database_error.reset_mock()

        self.mock_config = mock.Mock()
        self.mock_adapter = mock.Mock()
        self.mock_adapter.parse_partition_by = mock.Mock()

        self.mock_validation = mock.Mock()
        self.mock_validation.any = mock.Mock()
        self.mock_validation.any.__getitem__ = mock.Mock(return_value=mock.Mock())

        self.macro_context = {
            'config': self.mock_config,
            'adapter': self.mock_adapter,
            'exceptions': mock_exceptions,
            'validation': self.mock_validation,
            'namespace': lambda **kwargs: type('NS', (), kwargs)(),
        }

        self._mock_clustered_by = None
        self._mock_location_root = None
        self._mock_partition_by_raw = None
        self._mock_grants = None
        self._mock_retention_period = None

    def _simulate_dbt_spark_validate_openhouse_configs(self, file_format):
        cfg = self.macro_context['config']
        adp = self.macro_context['adapter']
        exc = self.macro_context['exceptions']
        ns  = self.macro_context['namespace']
        val = self.macro_context['validation']

        if file_format == 'openhouse':
            cfg.get.side_effect = lambda key, default=None, validator=None: {
                'clustered_by':     self._mock_clustered_by,
                'location_root':    self._mock_location_root,
                'partition_by':     self._mock_partition_by_raw,
                'grants':           self._mock_grants,
                'retention_period': self._mock_retention_period,
            }.get(key, default)

            if cfg.get('clustered_by', None) is not None:
                exc.raise_compiler_error("'clustered_by' is not supported for 'openhouse' file_format")

            if cfg.get('location_root', None) is not None:
                exc.raise_compiler_error("'location_root' is not supported for 'openhouse' file_format")

            raw = cfg.get('partition_by', None, validator=val.any[list, dict])
            p_list = []
            if raw is not None:
                p_list = adp.parse_partition_by(raw)
                if len(p_list) > 4:
                    exc.raise_compiler_error(
                        "For partitioned tables with file_format = 'openhouse', the size of 'partition_by' must not be > 4."
                    )
                ts_count = ns(count=0)
                for p in p_list:
                    dt = p.data_type.lower()
                    if dt not in ['timestamp', 'string', 'int']:
                        exc.raise_compiler_error(
                            "For partitioned tables with file_format = 'openhouse', "
                            "'data_type' must be one of ('timestamp', 'string', 'int')."
                        )
                    if dt == 'timestamp':
                        ts_count.count += 1
                        if ts_count.count > 1:
                            exc.raise_compiler_error(
                                "For timestamp-partitioned tables with file_format = 'openhouse',\n"
                                "   OpenHouse only supports 1 timestamp-based column partitioning"
                            )
                        valid_gran = [
                            'hour','hours',
                            'day','days',
                            'month','months',
                            'year','years',
                        ]
                        if p.granularity is None:
                            exc.raise_compiler_error(
                                "For timestamp-partitioned tables with file_format = 'openhouse' "
                                "and data_type = 'timestamp', granularity must be provided."
                            )
                        if p.granularity not in valid_gran:
                            exc.raise_compiler_error(
                                "For timestamp-partitioned tables with file_format = 'openhouse', "
                                "'granularity' must be one of ('hours', 'days', 'months', or 'years')."
                            )

            grants = cfg.get('grants', None)
            if grants is not None:
                for priv in grants.keys():
                    if priv.lower() not in ['select', 'manage grants']:
                        exc.raise_compiler_error(
                            "For outputs with file_format = 'openhouse', "
                            "keys in 'grants' map must be one of ('select', 'manage grants')."
                        )

            raw_ret = cfg.get('retention_period', None)
            if raw_ret is not None:
                if cfg.get('partition_by', None) is None:
                    exc.raise_compiler_error(
                        "For tables with file_format = 'openhouse' and 'retention_period', "
                        "'partition_by' must be supplied."
                    )
                found_ts = False
                for p in p_list:
                    if p.data_type.lower() == 'timestamp':
                        found_ts = True
                        break
                if not found_ts:
                    exc.raise_compiler_error(
                        "For tables with file_format = 'openhouse' and 'retention_period', "
                        "partition_by must be supplied with\n"
                        "   1 column partition with data_type: 'timestamp'."
                    )

        return file_format

    # --- Tests ---

    def test_validate_openhouse_configs_valid_timestamp_retention(self):
        self._mock_partition_by_raw = [{'field':'event_time','data_type':'timestamp','granularity':'day'}]
        self.mock_adapter.parse_partition_by.return_value = [
            mock_partition_by('event_time','timestamp','day')
        ]
        self._mock_retention_period = '90d'
        res = self._simulate_dbt_spark_validate_openhouse_configs('openhouse')
        self.assertEqual(res, 'openhouse')
        mock_exceptions.raise_compiler_error.assert_not_called()

    def test_validate_openhouse_configs_valid_timestamp_no_retention(self):
        self._mock_partition_by_raw = [{'field':'event_time','data_type':'timestamp','granularity':'day'}]
        self.mock_adapter.parse_partition_by.return_value = [
            mock_partition_by('event_time','timestamp','day')
        ]
        res = self._simulate_dbt_spark_validate_openhouse_configs('openhouse')
        self.assertEqual(res, 'openhouse')
        mock_exceptions.raise_compiler_error.assert_not_called()

    def test_validate_openhouse_configs_invalid_clustered_by(self):
        self._mock_clustered_by = ['col1']
        with self.assertRaisesRegex(CompilationError,
            r"Compilation Error\s*'clustered_by' is not supported for 'openhouse' file_format"
        ):
            self._simulate_dbt_spark_validate_openhouse_configs('openhouse')

    def test_validate_openhouse_configs_invalid_location_root(self):
        self._mock_location_root = '/foo'
        with self.assertRaisesRegex(CompilationError,
            r"Compilation Error\s*'location_root' is not supported for 'openhouse' file_format"
        ):
            self._simulate_dbt_spark_validate_openhouse_configs('openhouse')

    def test_validate_openhouse_configs_invalid_partition_count(self):
        self._mock_partition_by_raw = [{}, {}, {}, {}, {}]
        self.mock_adapter.parse_partition_by.return_value = [
            mock_partition_by(f'col{i}','string') for i in range(5)
        ]
        with self.assertRaisesRegex(CompilationError,
            r"Compilation Error\s*For partitioned tables with file_format = 'openhouse', the size of 'partition_by' must not be > 4\."
        ):
            self._simulate_dbt_spark_validate_openhouse_configs('openhouse')

    def test_validate_openhouse_configs_invalid_partition_data_type(self):
        self._mock_partition_by_raw = [{'field':'c','data_type':'boolean'}]
        self.mock_adapter.parse_partition_by.return_value = [
            mock_partition_by('c','boolean')
        ]
        with self.assertRaisesRegex(CompilationError,
            r"Compilation Error\s*For partitioned tables with file_format = 'openhouse', 'data_type' must be one of \('timestamp', 'string', 'int'\)\."
        ):
            self._simulate_dbt_spark_validate_openhouse_configs('openhouse')

    def test_validate_openhouse_configs_invalid_multiple_timestamp_partitions(self):
        self._mock_partition_by_raw = [
            {'field':'ts1','data_type':'timestamp','granularity':'day'},
            {'field':'ts2','data_type':'timestamp','granularity':'hour'}
        ]
        self.mock_adapter.parse_partition_by.return_value = [
            mock_partition_by('ts1','timestamp','day'),
            mock_partition_by('ts2','timestamp','hour')
        ]
        with self.assertRaisesRegex(CompilationError,
            r"Compilation Error\s*For timestamp-partitioned tables with file_format = 'openhouse',\s*OpenHouse only supports 1 timestamp-based column partitioning"
        ):
            self._simulate_dbt_spark_validate_openhouse_configs('openhouse')

    def test_validate_openhouse_configs_invalid_timestamp_missing_granularity(self):
        self._mock_partition_by_raw = [{'field':'ts1','data_type':'timestamp'}]
        self.mock_adapter.parse_partition_by.return_value = [mock_partition_by('ts1','timestamp',None)]
        with self.assertRaisesRegex(CompilationError,
            r"Compilation Error\s*For timestamp-partitioned tables with file_format = 'openhouse' and data_type = 'timestamp', granularity must be provided\."
        ):
            self._simulate_dbt_spark_validate_openhouse_configs('openhouse')

    def test_validate_openhouse_configs_invalid_timestamp_invalid_granularity(self):
        self._mock_partition_by_raw = [{'field':'ts1','data_type':'timestamp','granularity':'weeks'}]
        self.mock_adapter.parse_partition_by.return_value = [mock_partition_by('ts1','timestamp','weeks')]
        with self.assertRaisesRegex(CompilationError,
            r"Compilation Error\s*For timestamp-partitioned tables with file_format = 'openhouse', 'granularity' must be one of \('hours', 'days', 'months', or 'years'\)\."
        ):
            self._simulate_dbt_spark_validate_openhouse_configs('openhouse')

    def test_validate_openhouse_configs_invalid_grants_privilege(self):
        self._mock_grants = {'insert':['u']}
        with self.assertRaisesRegex(CompilationError,
            r"Compilation Error\s*For outputs with file_format = 'openhouse', keys in 'grants' map must be one of \('select', 'manage grants'\)\."
        ):
            self._simulate_dbt_spark_validate_openhouse_configs('openhouse')

    def test_validate_openhouse_configs_invalid_retention_no_partition_by(self):
        self._mock_retention_period = '30d'
        self.mock_adapter.parse_partition_by.return_value = []
        with self.assertRaisesRegex(CompilationError,
            r"Compilation Error\s*For tables with file_format = 'openhouse' and 'retention_period', 'partition_by' must be supplied\."
        ):
            self._simulate_dbt_spark_validate_openhouse_configs('openhouse')

    def test_validate_openhouse_configs_invalid_retention_no_timestamp_partition(self):
        self._mock_retention_period = '30d'
        self._mock_partition_by_raw = [{'field':'c','data_type':'string'}]
        self.mock_adapter.parse_partition_by.return_value = [mock_partition_by('c','string')]
        with self.assertRaisesRegex(CompilationError,
            r"Compilation Error\s*For tables with file_format = 'openhouse' and 'retention_period', partition_by must be supplied with\s*1 column partition with data_type: 'timestamp'\."
        ):
            self._simulate_dbt_spark_validate_openhouse_configs('openhouse')
