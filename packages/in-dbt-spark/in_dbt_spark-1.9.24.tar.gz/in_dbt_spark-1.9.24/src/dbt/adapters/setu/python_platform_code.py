PYTHON_PLATFORM_CODE = """
from pyspark.sql import DataFrame as indbt__DataFrame
from pyspark.sql import SparkSession as indbt__SparkSession
import sys as indbt__sys
import os as indbt__os
from typing import List as indbt__List, Optional as indbt__Optional, Dict as indbt__Dict, Any as indbt__Any, Union as indbt__Union, Tuple as indbt__Tuple
from datetime import datetime as indbt__datetime, timedelta as indbt__timedelta, timezone as indbt__timezone
from enum import Enum as indbt__Enum
import calendar as indbt__calendar


class indbt__python_incremental_handler:
    \"\"\"
    Handles incremental strategies for python model materialization.

    This class provides methods to generate SQL statements for various incremental
    strategies for python models including append, insert overwrite, and merge operations.
    
    Supports schema change handling through the on_schema_change configuration:
    - 'ignore': Ignore schema changes (default)
    - 'fail': Fail when schema changes are detected
    - 'append_new_columns': Add new columns from source to target
    - 'sync_all_columns': Add new columns, remove missing columns, and update types

    Attributes:
        config (Dict[str, Any]): Configuration dictionary containing strategy-specific
        settings like merge_update_columns, merge_exclude_columns, and on_schema_change.
    \"\"\"

    def __init__(self, config: indbt__Optional[indbt__Dict[str, indbt__Any]] = None):
        \"\"\"
        Initialize the incremental handler with optional configuration.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary for the handler
                populated by dbt.config. Defaults to empty dict if None.
        \"\"\"
        self.config = config or {}

    def _get_update_columns(
        self,
        dest_columns: indbt__List[str],
        merge_update_columns: indbt__Optional[indbt__List[str]] = None,
        merge_exclude_columns: indbt__Optional[indbt__List[str]] = None
    ) -> indbt__Optional[indbt__List[str]]:
        \"\"\"
        Determine which columns should be updated during a merge operation.

        This method resolves the columns to update based on inclusion/exclusion rules.
        Either merge_update_columns or merge_exclude_columns can be specified, but not both.

        Args:
            dest_columns (List[str]): All available columns in the destination table.
            merge_update_columns (Optional[List[str]]): Specific columns to include in updates.
            merge_exclude_columns (Optional[List[str]]): Columns to exclude from updates.

        Returns:
            Optional[List[str]]: List of columns to update, or None if no filtering is applied.
        \"\"\"
        if merge_update_columns and merge_exclude_columns:
            raise ValueError(
                'Cannot specify both merge_update_columns and merge_exclude_columns'
            )

        if merge_update_columns:
            return merge_update_columns

        if merge_exclude_columns:
            exclude_set = {col.lower() for col in merge_exclude_columns}
            return [col for col in dest_columns if col.lower() not in exclude_set]

        return None

    def generate_append_sql(self, source: str, target: str, columns: indbt__List[str]) -> str:
        \"\"\"
        Generate SQL for appending data from source to target table.
        Creates an INSERT INTO statement that adds all rows from the source
        table to the target table without any deduplication or updates.

        Args:
            source (str): Name of the source table/view.
            target (str): Name of the target table.
            columns (List[str]): List of column names to insert.

        Returns:
            str: SQL INSERT statement for appending data.
        \"\"\"
        columns_csv = ', '.join(f'`{col}`' for col in columns)
        return f"INSERT INTO {target}\\nSELECT {columns_csv} FROM {source}"

    def generate_insert_overwrite_sql(
        self,
        source: str,
        target: str,
        columns: indbt__Optional[indbt__List[str]] = None,
    ) -> str:
        \"\"\"
        Generate SQL for insert overwrite operation.

        Creates an INSERT OVERWRITE statement that replaces all data in the target
        table with data from the source table.

        Args:
            source (str): Name of the source table/view.
            target (str): Name of the target table.
            columns (Optional[List[str]]): Specific columns to select. If None, selects all columns.

        Returns:
            str: SQL INSERT OVERWRITE statement.
        \"\"\"
        if columns:
            columns_csv = ', '.join(f'`{col}`' for col in columns)
            sql = f"INSERT OVERWRITE {target}\\nSELECT {columns_csv} FROM {source}"
        else:
            sql = f"INSERT OVERWRITE {target}\\nSELECT * FROM {source}"
        return sql

    def generate_merge_sql(
        self,
        source: str,
        target: str,
        unique_key: indbt__Union[str, indbt__List[str], None],
        columns: indbt__List[str],
        incremental_predicates: indbt__Optional[indbt__List[str]] = None,
        sql_header: indbt__Optional[str] = None
    ) -> str:
        \"\"\"
        Generate SQL for merge (upsert) operation.

        Creates a MERGE statement that updates existing records and inserts new ones
        based on unique key matching. Supports custom predicates and column filtering.

        Args:
            source (str): Name of the source table/view.
            target (str): Name of the target table.
            unique_key (Union[str, List[str], None]): Column(s) used for matching records.
            columns (List[str]): All available columns in the tables.
            incremental_predicates (Optional[List[str]]): Additional WHERE conditions for the merge.
            sql_header (Optional[str]): Optional SQL header to prepend to the statement.

        Returns:
            str: SQL MERGE statement with UPDATE and INSERT clauses.
        \"\"\"
        # Build predicates efficiently
        predicates = incremental_predicates or []

        # Handle unique key predicates
        if unique_key:
            if isinstance(unique_key, str):
                predicates.append(f"src.`{unique_key}` = dest.`{unique_key}`")
            else:
                predicates.extend(f"src.`{key}` = dest.`{key}`" for key in unique_key)
        else:
            raise ValueError("unique_key is required for incremental merge")

        # Get update columns
        merge_update_columns = self.config.get('merge_update_columns')
        merge_exclude_columns = self.config.get('merge_exclude_columns')
        update_columns = self._get_update_columns(columns, merge_update_columns, merge_exclude_columns)

        # Build SQL parts
        sql_parts = []
        if sql_header:
            sql_parts.append(sql_header)

        # MERGE statement
        sql_parts.append(f"MERGE INTO {target} AS dest")
        sql_parts.append(f"USING {source} AS src")
        sql_parts.append(f"ON {' AND '.join(predicates)}")

        # UPDATE clause
        if update_columns:
            update_statements = [f'`{col}` = src.`{col}`' for col in update_columns]
            sql_parts.append("WHEN MATCHED THEN UPDATE SET")
            sql_parts.append("    " + ",\\n    ".join(update_statements))
        else:
            sql_parts.append("WHEN MATCHED THEN UPDATE SET *")

        # INSERT clause
        sql_parts.append("WHEN NOT MATCHED THEN INSERT *")

        return '\\n'.join(sql_parts)

    def generate_sql(self, temp_view: str, target_table: str) -> str:
        \"\"\"
        Generate SQL statement based on the specified incremental strategy.

        This is the main entry point for SQL generation. It handles fetching table columns,
        building predicates, and routing to the strategy-specific SQL generator.

        Args:
            temp_view (str): Name of the source temp view.
            target_table (str): Name of the target table.

        Returns:
            str: Generated SQL statement for the specified strategy.
        \"\"\"
        strategy = self.config.get('incremental_strategy', 'insert_overwrite')
        unique_key = self.config.get('unique_key', None)
        sql_header = self.config.get('sql_header')

        # Try to get target table columns
        columns = get_table_columns_py_model(target_table)
        if not columns:
            # Fallback: try to get from temp_view
            try:
                columns = spark.table(temp_view).columns
                print(f"Using columns from temp view: {columns}")
            except Exception as e:
                print(f"Could not get columns from temp view {temp_view}: {e}")
                raise

        # Build incremental predicates
        incremental_predicates = build_incremental_predicates_py_model(
            self.config, temp_view, target_table
        )

        # Call appropriate strategy function
        if strategy == 'append':
            return self.generate_append_sql(temp_view, target_table, columns)
        elif strategy == 'insert_overwrite':
            return self.generate_insert_overwrite_sql(temp_view, target_table, columns)
        elif strategy == 'merge':
            return self.generate_merge_sql(
                source=temp_view,
                target=target_table,
                unique_key=unique_key,
                columns=columns,
                incremental_predicates=incremental_predicates,
                sql_header=sql_header
            )
        else:
            raise ValueError(f"Unsupported incremental strategy: {strategy}")


def get_source_read_query_with_filter_py_model(source_name: str, table_name: str) -> str:
    \"\"\"
    Retrieve the filtered read query for a specific source and table combination.
    \"\"\"
    for prop in indbt__sources:
        if prop.get("source_name") == source_name and prop.get("table_name") == table_name:
            return prop.get("read_query_with_filter")  # type: ignore
    raise ValueError(
        f"No matching property for source: {source_name}, table: {table_name}"
    )


def get_table_columns_py_model(table_name: str) -> indbt__List[str]:
    \"\"\"
    Retrieve column names from a Spark table.
    \"\"\"
    try:
        df = spark.table(table_name)
        return df.columns
    except Exception as e:
        print(f"Could not get columns for table {table_name}: {e}")
        return []


def build_incremental_predicates_py_model(dbt_config: indbt__Dict[str, indbt__Any], temp_view: str, target_table: str) -> indbt__List[str]:
    \"\"\"
    Build a list of predicates for incremental operations based on configuration.
    \"\"\"
    predicates = []

    # Add time-based filtering if configured
    if dbt_config.get('updated_at'):
        updated_at_col = dbt_config.get('updated_at')
        predicates.append(f"src.`{updated_at_col}` > dest.`{updated_at_col}`")

    # Add custom where clause if specified
    if dbt_config.get('incremental_predicates'):
        predicates.extend(dbt_config.get('incremental_predicates'))

    return predicates


def indbt__generate_input_maps(
        input_map: indbt__Dict[str, indbt__Tuple[str, str]]
) -> indbt__Dict[str, indbt__DataFrame]:
    \"\"\"
    Generate a dictionary of Spark DataFrames based on the given input map.

    For each alias in the input_map, this function:
    - Retrieves the corresponding source and table name.
    - Constructs a read query with filters using `get_source_read_query_with_filter_py_model`.
    - Executes the query using Spark SQL.
    - Registers the resulting DataFrame as a temporary view with the alias name.
    - Stores the DataFrame in a result dictionary keyed by the alias.

    Args:
        input_map (Dict[str, Tuple[str, str]]): A dictionary where each key is an alias
            and the value is a tuple of (source_name, table_name).

    Returns:
        Dict[str, indbt__DataFrame]: A dictionary mapping aliases to their corresponding
            Spark DataFrames.
    \"\"\"
    input_map_py = {}
    for alias, (src, tbl) in input_map.items():
        query = get_source_read_query_with_filter_py_model(src, tbl)
        df = spark.sql(query)
        df.createOrReplaceTempView(alias)
        input_map_py[alias] = df
    return input_map_py


def indbt__scala_executor(
        class_name: str,
        input_map: dict,
        prop_map: dict
) -> indbt__DataFrame:
    \"\"\"
    Executes a Scala-based transformer class from the JVM using Spark and returns a Spark DataFrame.

    This function:
    - Converts the Python `prop_map` to a Java `HashMap`.
    - Generates Spark DataFrames from the provided `input_map` using `indbt__generate_input_maps`.
    - Converts the resulting DataFrames into their JVM representations and builds a Java `HashMap`.
    - Dynamically loads and instantiates the specified Scala class from the JVM classloader.
    - Invokes the `transform` method on the Scala transformer, passing in the input DataFrame map,
      the active Spark session, and the properties map.

    Args:
        class_name (str): Fully qualified name of the Scala class to be executed (e.g. "com.example.MyTransformer").
        input_map (dict): A dictionary mapping alias names to tuples of (source_name, table_name).
        prop_map (dict): A dictionary of properties to pass into the Scala transformer.

    Returns:
        indbt__DataFrame: The transformed result as a Spark DataFrame.
    \"\"\"
    jvm = spark.sparkContext._jvm

    # Convert prop_map to Java map
    prop_map_jvm = jvm.java.util.HashMap()
    for key, value in prop_map.items():
        prop_map_jvm.put(key, value)

    # Prepare Python input map
    input_map_py = indbt__generate_input_maps(input_map)

    # Build Java input map
    input_map_jvm = jvm.java.util.HashMap()
    for alias, df in input_map_py.items():
        input_map_jvm.put(alias, df._jdf)

    # Load and call Java transformer
    cloader = spark.sparkContext._gateway.jvm.Thread.currentThread().getContextClassLoader()
    transformer = cloader.loadClass(class_name).newInstance()

    result_jdf = transformer.transform(input_map_jvm, spark._jsparkSession, prop_map_jvm)
    return indbt__DataFrame(result_jdf, spark._wrapped)




class Macros:
    \"\"\"
    Utility class to retrieve pre-parsed logical date strings or objects
    for various timezones.
    \"\"\"

    LOGICAL_DATE_OBJECTS = {
        # Core
        "US/Pacific": indbt__logical_date_us_pacific_obj,
        "UTC": indbt__logical_date_utc_obj,
    
        # US
        "MST": indbt__logical_date_mst_obj,
        "US/Central": indbt__logical_date_cst_obj,
        "US/Eastern": indbt__logical_date_est_obj,
    
        # Europe
        "Europe/London": indbt__logical_date_europe_london_obj,
        "CET": indbt__logical_date_cet_obj,
    
        # Asia
        "Asia/Kolkata": indbt__logical_date_asia_kolkata_obj,
        "Asia/Tokyo": indbt__logical_date_asia_tokyo_obj,
        "Asia/Shanghai": indbt__logical_date_asia_shanghai_obj,
    
        # Australia
        "Australia/Sydney": indbt__logical_date_australia_sydney_obj,
    }

    LOGICAL_DATE_STRINGS = {
        # Core
        "US/Pacific": indbt__logical_date_us_pacific_str,
        "UTC": indbt__logical_date_utc_str,
    
        # US
        "MST": indbt__logical_date_mst_str,
        "US/Central": indbt__logical_date_cst_str,
        "US/Eastern": indbt__logical_date_est_str,
    
        # Europe
        "Europe/London": indbt__logical_date_europe_london_str,
        "CET": indbt__logical_date_cet_str,
    
        # Asia
        "Asia/Kolkata": indbt__logical_date_asia_kolkata_str,
        "Asia/Tokyo": indbt__logical_date_asia_tokyo_str,
        "Asia/Shanghai": indbt__logical_date_asia_shanghai_str,
    
        # Australia
        "Australia/Sydney": indbt__logical_date_australia_sydney_str,
    }

    @classmethod
    def get_logical_date(cls, tz_name="US/Pacific"):
        \"\"\"
        Return the logical datetime object for the specified timezone.

        Args:
            tz_name (str): The timezone identifier.

        Returns:
            datetime: Logical datetime in that timezone.
        \"\"\"
        if tz_name not in cls.LOGICAL_DATE_OBJECTS:
            raise ValueError(f"Unsupported timezone: {tz_name}")
        return cls.LOGICAL_DATE_OBJECTS[tz_name]

    @classmethod
    def get_logical_date_str(cls, pattern="%Y-%m-%d-%H", tz_name="US/Pacific"):
        \"\"\"
        Return the logical date string formatted from pre-parsed value.

        Args:
            pattern (str): A strftime-compatible format string.
            tz_name (str): The timezone identifier.

        Returns:
            str: Formatted date string.
        \"\"\"
        dt = cls.get_logical_date(tz_name)
        return dt.strftime(pattern)

    @classmethod
    def last_day_of_month(cls, date_obj):
        \"\"\"
        Calculate the last day of the month for a given date.

        Args:
            date_obj (datetime): A datetime object for which to find the last day of the month.

        Returns:
            datetime: A new datetime object representing the last day of the same month
                     and year as the input date, preserving the time and timezone.

        \"\"\"
        if date_obj.month == 12:
            next_month = date_obj.replace(year=date_obj.year + 1, month=1, day=1)
        else:
            next_month = date_obj.replace(month=date_obj.month + 1, day=1)
        last_day = next_month - indbt__timedelta(days=1)
        return date_obj.replace(day=last_day.day)

    @classmethod
    def end_date(cls, frequency, delay, pattern="%Y-%m-%d-%H", tz_name="US/Pacific"):
        \"\"\"
        Calculate the end date for a time period based on frequency and delay.

        This method calculates the end date of a time period by going back a specified
        number of periods (delay) from the current logical date.

        Args:
            frequency (str): The frequency type. Supported values:
                - "hourly": End date is delay hours ago
                - "daily": End date is delay days ago
                - "weekly": End date is the last day of the week from delay weeks ago
                - "monthly": End date is the last day of the month from delay months ago
            delay (int): Number of periods to go back from the current date.
            pattern (str): The strftime pattern to format the returned date string.
            tz_name (str, optional): Timezone name for date calculation.

        Returns:
            str: Formatted end date string according to the specified pattern.
        \"\"\"
        logical_date_env = cls.get_logical_date(tz_name)

        frequency = frequency.lower()

        if frequency == "hourly":
            end_date = logical_date_env - indbt__timedelta(hours=delay)
            return end_date.strftime(pattern)

        elif frequency == "daily":
            end_date = logical_date_env - indbt__timedelta(days=delay)
            return end_date.strftime(pattern)

        elif frequency == "weekly":
            logical_start_week = logical_date_env - indbt__timedelta(days=logical_date_env.weekday())
            start_date_of_end_date = logical_start_week - indbt__timedelta(weeks=delay)
            end_date = start_date_of_end_date + indbt__timedelta(days=6)
            return end_date.strftime(pattern)

        elif frequency == "monthly":
            end_date_year = logical_date_env.year
            end_date_month = logical_date_env.month

            if (end_date_month - delay) > 0:
                end_date_month -= delay
            else:
                end_date_year -= 1 + (delay // 12)
                end_date_month = end_date_month - (delay % 12) + 12
                end_date_month = (end_date_month % 12) or 12

            end_date = cls.last_day_of_month(
                indbt__datetime__mod(
                    day=logical_date_env.day,
                    month=end_date_month,
                    year=end_date_year,
                    tzinfo=logical_date_env.tzinfo
                )
            )
            return end_date.strftime(pattern)

        else:
            raise ValueError(f"frequency = {frequency} is incorrect. only hourly/daily/weekly/monthly are supported")

    @classmethod
    def start_date(cls, frequency, delay, range_val, pattern="%Y-%m-%d-%H", tz_name="US/Pacific"):
        \"\"\"
        Calculate the start date for a time range based on frequency, delay, and range.

        This method calculates the start date of a time period by going back a specified
        number of periods (delay + range_val - 1) from the current logical date.

        Args:
            frequency (str): The frequency type. Supported values:
                - "hourly": Start date is (delay + range_val - 1) hours ago
                - "daily": Start date is (delay + range_val - 1) days ago
                - "weekly": Start date is the first day of the week from (delay + range_val - 1) weeks ago
                - "monthly": Start date is the first day of the month from (delay + range_val - 1) months ago
            delay (int): Number of periods to skip back from current date.
            range_val (int): Number of periods to include in the range.
            pattern (str): The strftime pattern to format the returned date string.
            tz_name (str, optional): Timezone name for date calculation.

        Returns:
            str: Formatted start date string according to the specified pattern.

        \"\"\"
        logical_date_env = cls.get_logical_date(tz_name)

        frequency = frequency.lower()

        if frequency == "hourly":
            start_date = logical_date_env - indbt__timedelta(hours=(delay + range_val - 1))
            return start_date.strftime(pattern)

        elif frequency == "daily":
            start_date = logical_date_env - indbt__timedelta(days=(delay + range_val - 1))
            return start_date.strftime(pattern)

        elif frequency == "weekly":
            logical_start_week = logical_date_env - indbt__timedelta(days=logical_date_env.weekday())
            start_date = logical_start_week - indbt__timedelta(weeks=(delay + range_val - 1))
            return start_date.strftime(pattern)

        elif frequency == "monthly":
            start_date_year = logical_date_env.year
            start_date_month = logical_date_env.month

            if (start_date_month - delay - range_val + 1) > 0:
                start_date_month -= (delay + range_val - 1)
            else:
                total_shift = delay + range_val - 1
                start_date_year -= 1 + (total_shift // 12)
                start_date_month = start_date_month - (total_shift % 12) + 12
                start_date_month = (start_date_month % 12) or 12

            start_date = indbt__datetime__mod(
                year=start_date_year,
                month=start_date_month,
                day=1,
                tzinfo=logical_date_env.tzinfo
            )
            return start_date.strftime(pattern)

        else:
            raise ValueError(f"frequency = {frequency} is incorrect. only hourly/daily/weekly/monthly are supported")


# ==========================================================================
# Utilities to replace dateutil.relativedelta
# ==========================================================================
def subtract_months(dt: indbt__datetime, months: int) -> indbt__datetime:
    \"\"\"Subtract `months` from `dt`, adjusting day if needed.\"\"\"
    year = dt.year
    month = dt.month - months
    while month <= 0:
        month += 12
        year -= 1
    day = min(dt.day, indbt__calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)

def add_months(dt: indbt__datetime, months: int) -> indbt__datetime:
    \"\"\"Add `months` to `dt`, adjusting day if needed.\"\"\"
    year = dt.year
    month = dt.month + months
    while month > 12:
        month -= 12
        year += 1
    day = min(dt.day, indbt__calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)

# ==========================================================================
# Core logic
# ==========================================================================
def indbt__get_max_partition_delay():
    \"\"\"
    Returns the maximum partition_delay found across all sources in the global indbt__sources list.

    Each source in `indbt__sources` may define partitioning metadata under:
        source["meta"]["sensor"]["partition_by"]

    The function:
    - Defaults delay to 0 if not specified.
    - Safely handles sources with missing or malformed metadata.
    - Iterates over all defined partitions and finds the highest `partition_delay` value.

    Returns:
        int: The maximum partition delay across all sources. Defaults to 0 if no delays are defined.
    \"\"\"
    max_delay = 0
    for source in indbt__sources:
        try:
            partitions = source.get("meta", {}).get("sensor", {}).get("partition_by", [])
            for partition in partitions:
                delay = partition.get("partition_delay", 0)
                if isinstance(delay, int):  # ensure it's a number
                    max_delay = max(max_delay, delay)
        except Exception:
            continue  # skip sources with malformed metadata
    return max_delay

class UxpExecutionMode(indbt__Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

class UxpDatePropCalculator:
    \"\"\"
    Complete backfill calculator with date properties generation
    \"\"\"

    def __init__(self, frequency_weekly_day: int = 1, window: int = 1, delay: int = 1):
        \"\"\"
        Initialize the calculator

        Args:
            frequency_weekly_day: Day of week for weekly schedule (1=Monday, 7=Sunday)
            window: Window size for the dataset
            delay: Delay in days/hours/months
        \"\"\"
        self.frequency_weekly_day = frequency_weekly_day
        self.window = window
        self.delay = delay

    def get_last_weekly_data_date(self, date: indbt__datetime) -> indbt__datetime:
        \"\"\"
        Calculate the last weekly data date for a given flow date.
        \"\"\"
        data_day = self.frequency_weekly_day - 1
        if data_day == 0:
            data_day = 7

        data_day_0based = data_day - 1
        current_day = date.weekday()

        if current_day <= data_day_0based:
            date = date - indbt__timedelta(weeks=1)

        days_diff = (current_day - data_day_0based) % 7
        if days_diff == 0:
            days_diff = 7

        result = date - indbt__timedelta(days=days_diff)
        return result

    def get_last_monthly_data_date(self, date: indbt__datetime) -> indbt__datetime:
        \"\"\"
        Calculate the last monthly data date for a given flow date.
        \"\"\"
        date = subtract_months(date, 1)
        last_day = indbt__calendar.monthrange(date.year, date.month)[1]
        date = date.replace(day=last_day)
        return date

    def calculate_flow_dates(self, start_date: indbt__datetime, end_date: indbt__datetime, mode: UxpExecutionMode) -> indbt__List[indbt__datetime]:
        \"\"\"
        Calculate flow dates for backfill.
        \"\"\"
        flow_dates = []

        if mode in [UxpExecutionMode.WEEKLY, UxpExecutionMode.MONTHLY]:
            if mode == UxpExecutionMode.WEEKLY:
                time_increment = indbt__timedelta(weeks=1)
                flow_start = start_date + time_increment
                flow_end = end_date + time_increment

                current_date = flow_start
                while current_date <= flow_end:
                    flow_dates.append(current_date)
                    current_date += time_increment
            else:
                flow_start = add_months(start_date, 1)
                flow_end = add_months(end_date, 1)
                current_date = flow_start
                while current_date <= flow_end:
                    flow_dates.append(current_date)
                    current_date = add_months(current_date, 1)

        else:  # DAILY
            flow_start = start_date + indbt__timedelta(days=self.delay + self.window - 1)
            flow_end = end_date + indbt__timedelta(days=self.delay + self.window - 1)

            current_date = flow_start
            while current_date <= flow_end:
                flow_dates.append(current_date)
                current_date += indbt__timedelta(days=1)

        return flow_dates

    def calculate_start_end_dates_for_data_date(self, data_date: indbt__datetime, mode: UxpExecutionMode) -> indbt__Tuple[indbt__datetime, indbt__datetime]:
        \"\"\"
        Calculate start and end dates for processing a specific data date.
        \"\"\"
        if mode == UxpExecutionMode.WEEKLY:
            end_date = data_date
            start_date = end_date - indbt__timedelta(weeks=self.window) + indbt__timedelta(days=1)

        elif mode == UxpExecutionMode.MONTHLY:
            end_date = data_date.replace(day=indbt__calendar.monthrange(data_date.year, data_date.month)[1])
            start_date = subtract_months(end_date.replace(day=1), self.window - 1)

        else:
            start_date = data_date
            end_date = data_date

        return start_date, end_date

    def calculate_missing_date(self, missing_flow_date: str, mode: UxpExecutionMode) -> indbt__datetime:
        \"\"\"
        Calculate missing date from missing flow date.
        \"\"\"
        missing_date = indbt__datetime.strptime(missing_flow_date, "%Y-%m-%d")

        if mode == UxpExecutionMode.MONTHLY:
            if self.window > 1:
                missing_date = subtract_months(missing_date, self.delay)
                missing_date = missing_date.replace(day=1)
                missing_date = add_months(missing_date, 1)
                missing_date = missing_date - indbt__timedelta(days=1)
            else:
                missing_date = self.get_last_monthly_data_date(missing_date)

        elif mode == UxpExecutionMode.WEEKLY:
            missing_date = self.get_last_weekly_data_date(missing_date)

        else:
            missing_date = missing_date - indbt__timedelta(days=self.delay)

        return missing_date

    def generate_date_properties(self, start_date: indbt__datetime, end_date: indbt__datetime) -> indbt__Dict[str, indbt__Any]:
        \"\"\"
        Generate all required date properties in various formats.
        \"\"\"
        start_date_utc = start_date.replace(tzinfo=indbt__timezone.utc)
        end_date_utc = end_date.replace(tzinfo=indbt__timezone.utc)

        start_epoch = int(start_date_utc.timestamp() * 1000)
        end_epoch = int((end_date_utc.replace(hour=23, minute=59, second=59, microsecond=999000).timestamp()) * 1000)

        properties = {
            "start_date": start_date.strftime("%Y%m%d"),
            "end_date": end_date.strftime("%Y%m%d"),
            "start_date_epoch": start_epoch,
            "end_date_epoch": end_epoch,
            "start_date_partition": start_date.strftime("%Y-%m-%d"),
            "end_date_partition": end_date.strftime("%Y-%m-%d"),
            "start_date_hive_partition": start_date.strftime("%Y-%m-%d-00"),
            "end_date_hive_partition": end_date.strftime("%Y-%m-%d-23")
        }

        return properties


def get_uxp_scala_properties(frequency: str = "daily", is_udp: bool = False) -> indbt__Dict[str, indbt__Any]:
    \"\"\"
    Generate all date properties based on configuration and logical date.

    Args:
        config: Configuration dictionary containing mode, window, delay, backfill_date, etc.
        is_udp: Boolean indicating if the flow is UDP .
    Returns:
        Dictionary containing all date properties
    \"\"\"
    is_backfill = indbt__is_backfill.lower() == "true"

    # Parse execution mode
    mode = UxpExecutionMode[frequency.upper()]

    # Get delay
    delay = indbt__get_max_partition_delay() + 1

    # Fixed values
    frequency_weekly_day = 7
    window = 1

    # Initialize calculator
    calculator = UxpDatePropCalculator(
        frequency_weekly_day=frequency_weekly_day,
        window=window,
        delay=delay
    )

    if is_udp:
        # UDP mode: start_date = end_date = logical_date
        udp_date = indbt__logical_date_obj
        start_date = udp_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = udp_date.replace(hour=0, minute=0, second=0, microsecond=0)
        data_date = udp_date

    elif is_backfill:
        # Airflow-style backfill logic
        reference_date = indbt__logical_date_obj
        data_date = reference_date
        start_date, end_date = calculator.calculate_start_end_dates_for_data_date(
            data_date=data_date,
            mode=mode
        )
    else:
        # Normal flow: execution-based calculation
        flow_date_str = (indbt__logical_date_obj + indbt__timedelta(days=1)).strftime("%Y-%m-%d")
        data_date = calculator.calculate_missing_date(
            missing_flow_date=flow_date_str,
            mode=mode
        )
        start_date, end_date = calculator.calculate_start_end_dates_for_data_date(
            data_date=data_date,
            mode=mode
        )
    # Generate all date properties
    properties = calculator.generate_date_properties(start_date, end_date)

    # Add metadata
    properties.update({
        "data_date": data_date.strftime("%Y-%m-%d"),
        "mode": mode.value,
        "window": window,
        "delay": delay,
        "is_backfill": is_backfill,
        "is_udp": is_udp
    })

    return properties

class indbt__table_creator:
    \"\"\"Handles comprehensive table creation for Python models with full parity to spark__create_table_as.\"\"\"

    def __init__(self, dbt_config):
        self.config = dbt_config

    def _get_file_format_clause(self):
        \"\"\"Generate USING clause for file format.\"\"\"
        file_format = self.config.get('file_format')
        if file_format:
            return f"USING {file_format}"
        return ""

    def _get_location_clause(self, identifier):
        \"\"\"Generate LOCATION clause.\"\"\"
        location_root = self.config.get('location_root')
        if location_root:
            return f"LOCATION '{location_root}/{identifier}'"
        return ""

    def _get_comment_clause(self):
        \"\"\"Generate COMMENT clause.\"\"\"
        comment = self.config.get('description')
        if comment:
            escaped_comment = comment.replace("'", "''")
            return f"COMMENT '{escaped_comment}'"
        return ""

    def _get_tblproperties_clause(self):
        \"\"\"Generate TBLPROPERTIES clause.\"\"\"
        tblproperties = self.config.get('tblproperties', {})
        if tblproperties:
            props = []
            for key, value in tblproperties.items():
                props.append(f"'{key}' = '{value}'")
            return f"TBLPROPERTIES ({', '.join(props)})"
        return ""

    def _get_options_clause(self):
        \"\"\"Generate OPTIONS clause.\"\"\"
        options = self.config.get('options', {})
        if options:
            opts = []
            for key, value in options.items():
                opts.append(f"'{key}' = '{value}'")
            return f"OPTIONS ({', '.join(opts)})"
        return ""

    def _get_partition_clause(self):
        \"\"\"Generate PARTITIONED BY clause.\"\"\"
        partition_by = self.config.get('partition_by')
        if partition_by:
            if isinstance(partition_by, list):
                partition_by_fields = [pb['field'] for pb in partition_by]
                return f"PARTITIONED BY ({', '.join(partition_by_fields)})"
            else:
                raise ValueError("partition_by must be a list of dict[field, data_type]")
        return ""

    def _get_clustered_clause(self):
        \"\"\"Generate CLUSTERED BY clause.\"\"\"
        clustered_by = self.config.get('clustered_by')
        if clustered_by:
            if isinstance(clustered_by, str):
                return f"CLUSTERED BY ({clustered_by})"
            elif isinstance(clustered_by, list):
                return f"CLUSTERED BY ({', '.join(clustered_by)})"
        return ""

    def _should_use_create_or_replace(self):
        \"\"\"Determine if we should use CREATE OR REPLACE TABLE.\"\"\"
        file_format = self.config.get('file_format', '').lower()
        return file_format in ['delta', 'iceberg']

    def _build_create_table_sql(self, table_name, temp_view, identifier):
        \"\"\"Build comprehensive CREATE TABLE statement.\"\"\"
        clauses = []

        if self._should_use_create_or_replace():
            clauses.append(f"CREATE OR REPLACE TABLE {table_name}")
        else:
            clauses.append(f"CREATE TABLE {table_name}")

        file_format = self._get_file_format_clause()
        if file_format:
            clauses.append(file_format)

        options = self._get_options_clause()
        if options:
            clauses.append(options)

        tblproperties = self._get_tblproperties_clause()
        if tblproperties:
            clauses.append(tblproperties)

        partition = self._get_partition_clause()
        if partition:
            clauses.append(partition)

        clustered = self._get_clustered_clause()
        if clustered:
            clauses.append(clustered)

        location = self._get_location_clause(identifier)
        if location:
            clauses.append(location)

        comment = self._get_comment_clause()
        if comment:
            clauses.append(comment)

        clauses.append(f"AS SELECT * FROM {temp_view}")
        return '\\n'.join(clauses)

    def create_table(self, table_name, temp_view, identifier):
        \"\"\"Create table with comprehensive configuration support.\"\"\"
        sql = self._build_create_table_sql(table_name, temp_view, identifier)
        print(f"Creating table with SQL:\\n{sql}")
        spark.sql(sql)

    def overwrite_table(self, table_name, temp_view):
        \"\"\"Overwrite existing table.\"\"\"
        print(f"Overwriting {table_name}")
        spark.sql(f"INSERT OVERWRITE {table_name} SELECT * FROM {temp_view}")


def indbt__create_table_as(table_name, temp_view, dbt_config):
    \"\"\"Create table with comprehensive configuration support - CREATE TABLE AS SELECT only.\"\"\"
    creator = indbt__table_creator(dbt_config)
    identifier = table_name.split('.')[-1]
    creator.create_table(table_name, temp_view, identifier)


def indbt__overwrite_table(table_name, temp_view):
    \"\"\"Overwrite existing table using INSERT OVERWRITE.\"\"\"
    print(f"Overwriting {table_name}")
    spark.sql(f"INSERT OVERWRITE {table_name} SELECT * FROM {temp_view}")


def indbt__handle_incremental(table_name, temp_view, dbt_config):
    \"\"\"Handle incremental materialization logic with schema change support.\"\"\"
    print(f"Incremental refresh for {table_name}")
    
    # Get and validate on_schema_change configuration
    on_schema_change = dbt_config.get('on_schema_change', 'ignore')
    on_schema_change = indbt__validate_on_schema_change(on_schema_change, default='ignore')
    
    # Process schema changes if needed
    indbt__process_schema_changes(on_schema_change, temp_view, table_name)
    
    # Generate and execute incremental SQL
    handler = indbt__python_incremental_handler(config=dbt_config)
    sql = handler.generate_sql(temp_view=temp_view, target_table=table_name)
    spark.sql(sql)


def indbt__validate_on_schema_change(on_schema_change: indbt__Optional[str], default: str = 'ignore') -> str:
    \"\"\"
    Validate on_schema_change configuration value.
    
    Args:
        on_schema_change: The on_schema_change config value
        default: Default value to use if invalid
        
    Returns:
        str: Valid on_schema_change value
    \"\"\"
    valid_values = ['sync_all_columns', 'append_new_columns', 'fail', 'ignore']
    
    if on_schema_change not in valid_values:
        print(f"Invalid value for on_schema_change ({on_schema_change}) specified. Setting default value of {default}.")
        return default
    
    return on_schema_change


def indbt__spark_type_to_sql_type(spark_type_str: str) -> str:
    \"\"\"
    Convert Spark data type string (simpleString or Type form) to a SQL-friendly type string.
    
    Args:
        spark_type_str: String representation of Spark data type (e.g., 'StringType', 'array<string>')
        
    Returns:
        SQL data type string (e.g., 'STRING', 'ARRAY<STRING>')
    \"\"\"
    s = (spark_type_str or '').strip()
    if not s:
        return s

    # Mapping for Type-suffixed forms
    type_mapping = {
        'StringType': 'STRING',
        'IntegerType': 'INT',
        'LongType': 'BIGINT',
        'DoubleType': 'DOUBLE',
        'FloatType': 'FLOAT',
        'BooleanType': 'BOOLEAN',
        'DateType': 'DATE',
        'TimestampType': 'TIMESTAMP',
        'BinaryType': 'BINARY',
        'ByteType': 'TINYINT',
        'ShortType': 'SMALLINT',
        'NullType': 'NULL'
    }

    # Mapping for simpleString primitives (lowercase)
    simple_mapping = {
        'string': 'STRING',
        'int': 'INT',
        'integer': 'INT',
        'bigint': 'BIGINT',
        'double': 'DOUBLE',
        'float': 'FLOAT',
        'boolean': 'BOOLEAN',
        'date': 'DATE',
        'timestamp': 'TIMESTAMP',
        'timestamp_ntz': 'TIMESTAMP_NTZ',
        'binary': 'BINARY',
        'tinyint': 'TINYINT',
        'smallint': 'SMALLINT',
        'byte': 'TINYINT',
        'long': 'BIGINT',
        'null': 'NULL'
    }

    def _split_top_level(text: str, sep: str = ','):
        parts = []
        current = []
        depth_paren, depth_angle = 0, 0
        for ch in text:
            if ch == '(':
                depth_paren += 1
            elif ch == ')':
                depth_paren -= 1
            elif ch == '<':
                depth_angle += 1
            elif ch == '>':
                depth_angle -= 1
            if ch == sep and depth_paren == 0 and depth_angle == 0:
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(ch)
        if current:
            parts.append(''.join(current).strip())
        return parts

    def _handle_simple_string(text: str) -> str:
        t = text.strip()
        tl = t.lower()

        # Structs: return as-is to avoid altering field names
        if tl.startswith('struct<') and t.endswith('>'):
            return t

        # DECIMAL(p,s)
        if tl.startswith('decimal(') and t.endswith(')'):
            return 'DECIMAL' + t[t.find('('):]

        # CHAR/VARCHAR with length
        if tl.startswith('char(') and t.endswith(')'):
            return 'CHAR' + t[t.find('('):]
        if tl.startswith('varchar(') and t.endswith(')'):
            return 'VARCHAR' + t[t.find('('):]

        # ARRAY<inner>
        if tl.startswith('array<') and t.endswith('>'):
            inner = t[t.find('<') + 1:-1]
            sql_inner = indbt__spark_type_to_sql_type(inner)
            return f'ARRAY<{sql_inner}>'

        # MAP<key,value>
        if tl.startswith('map<') and t.endswith('>'):
            inner = t[t.find('<') + 1:-1]
            parts = _split_top_level(inner, ',')
            if len(parts) >= 2:
                key_sql = indbt__spark_type_to_sql_type(parts[0])
                val_sql = indbt__spark_type_to_sql_type(parts[1])
                return f'MAP<{key_sql},{val_sql}>'
            return 'MAP<' + inner + '>'

        # Primitives
        if tl in simple_mapping:
            return simple_mapping[tl]

        return t

    def _handle_type_form(text: str) -> str:
        if text in type_mapping:
            return type_mapping[text]

        # DecimalType(precision,scale)
        if text.startswith('DecimalType(') and text.endswith(')'):
            return 'DECIMAL' + text[len('DecimalType'):]

        # ArrayType(elementType, containsNull)
        if text.startswith('ArrayType(') and text.endswith(')'):
            inner = text[len('ArrayType('):-1]
            args = _split_top_level(inner, ',')
            element = args[0] if args else inner
            element_sql = indbt__spark_type_to_sql_type(element)
            return f'ARRAY<{element_sql}>'

        # MapType(keyType, valueType, valueContainsNull)
        if text.startswith('MapType(') and text.endswith(')'):
            inner = text[len('MapType('):-1]
            args = _split_top_level(inner, ',')
            if len(args) >= 2:
                key_sql = indbt__spark_type_to_sql_type(args[0])
                val_sql = indbt__spark_type_to_sql_type(args[1])
                return f'MAP<{key_sql},{val_sql}>'
            return 'MAP<' + inner + '>'

        # StructType: leave unchanged to preserve detailed schema
        if text.startswith('StructType('):
            return text

        return text

    sl = s.lower()
    if ('<' in s and '>' in s) or sl.startswith(('array<', 'map<', 'struct<', 'decimal(', 'char(', 'varchar(')) or sl in simple_mapping:
        return _handle_simple_string(s)

    return _handle_type_form(s)


def indbt__get_table_columns_info(table_name: str) -> indbt__List[indbt__Dict[str, str]]:
    \"\"\"
    Get detailed column information for a table including name and data type.
    
    Args:
        table_name: Name of the table
        
    Returns:
        List of dictionaries with 'name' and 'data_type' keys
    \"\"\"
    try:
        df = spark.table(table_name)
        columns_info = []
        for field in df.schema.fields:
            # Prefer Spark's simpleString for SQL-friendly type names
            try:
                spark_type_str = field.dataType.simpleString()
            # We only catch AttributeError here because a broader catch could mask real
            # runtime errors. The function itself has an outer broad try/except that will
            # safely handle unexpected failures and log a helpful message.
            except AttributeError:
                spark_type_str = str(field.dataType)

            sql_type_str = indbt__spark_type_to_sql_type(spark_type_str)
            columns_info.append({
                'name': str(field.name).lower(),
                'data_type': sql_type_str
            })
        return columns_info
    except Exception as e:
        print(f"Could not get column info for table {table_name}: {e}")
        return []


def indbt__check_for_schema_changes(source_table: str, target_table: str) -> indbt__Dict[str, indbt__Any]:
    \"\"\"
    Check for schema changes between source and target tables.
    
    Args:
        source_table: Name of the source table
        target_table: Name of the target table
        
    Returns:
        Dictionary containing schema change information
    \"\"\"
    source_columns = indbt__get_table_columns_info(source_table)
    target_columns = indbt__get_table_columns_info(target_table)
    
    # Create maps for easier lookup (case-sensitive to match SQL behavior)
    source_map = {col['name']: col for col in source_columns}
    target_map = {col['name']: col for col in target_columns}
    
    # Find columns in source but not in target
    source_not_in_target = []
    for col in source_columns:
        if col['name'] not in target_map:
            source_not_in_target.append(col)
    
    # Find columns in target but not in source
    target_not_in_source = []
    for col in target_columns:
        if col['name'] not in source_map:
            target_not_in_source.append(col)
    
    # Find columns with type changes
    new_target_types = []
    for col in source_columns:
        if col['name'] in target_map:
            target_col = target_map[col['name']]
            if col['data_type'] != target_col['data_type']:
                new_target_types.append({
                    'column_name': col['name'],
                    'new_type': col['data_type'],
                    'old_type': target_col['data_type']
                })
    
    schema_changed = bool(source_not_in_target or target_not_in_source or new_target_types)
    
    changes_dict = {
        'schema_changed': schema_changed,
        'source_not_in_target': source_not_in_target,
        'target_not_in_source': target_not_in_source,
        'source_columns': source_columns,
        'target_columns': target_columns,
        'new_target_types': new_target_types
    }
    
    if schema_changed:
        msg = f\"\"\"
In {target_table}:
    Schema changed: {schema_changed}
    Source columns not in target: {[col['name'] for col in source_not_in_target]}
    Target columns not in source: {[col['name'] for col in target_not_in_source]}
    New column types: {[(ntt['column_name'], ntt['old_type'], ntt['new_type']) for ntt in new_target_types]}
        \"\"\"
        print(msg)
    
    return changes_dict


def indbt__sync_column_schemas(on_schema_change: str, target_table: str, schema_changes_dict: indbt__Dict[str, indbt__Any]) -> None:
    \"\"\"
    Synchronize column schemas based on on_schema_change strategy.
    
    Args:
        on_schema_change: The schema change strategy
        target_table: Name of the target table
        schema_changes_dict: Dictionary containing schema change information
    \"\"\"
    add_to_target_arr = schema_changes_dict['source_not_in_target']
    
    if on_schema_change == 'append_new_columns':
        if len(add_to_target_arr) > 0:
            # Add columns only (equivalent to alter_relation_add_remove_columns with none for remove)
            for col in add_to_target_arr:
                sql_type = indbt__spark_type_to_sql_type(col.get('data_type', ''))
                sql = f"ALTER TABLE {target_table} ADD COLUMN `{col['name']}` {sql_type}"
                spark.sql(sql)
                    
    elif on_schema_change == 'sync_all_columns':
        remove_from_target_arr = schema_changes_dict['target_not_in_source']
        new_target_types = schema_changes_dict['new_target_types']
        
        # Add and remove columns together (matching SQL alter_relation_add_remove_columns behavior)
        if len(add_to_target_arr) > 0 or len(remove_from_target_arr) > 0:
            # Add columns first
            for col in add_to_target_arr:
                sql_type = indbt__spark_type_to_sql_type(col.get('data_type', ''))
                sql = f"ALTER TABLE {target_table} ADD COLUMN `{col['name']}` {sql_type}"
                spark.sql(sql)
            
            # Remove columns
            for col in remove_from_target_arr:
                sql = f"ALTER TABLE {target_table} DROP COLUMN `{col['name']}`"
                spark.sql(sql)
        
        # Handle type changes separately (matching SQL behavior)
        if new_target_types != []:
            for ntt in new_target_types:
                column_name = ntt['column_name']
                new_type = ntt['new_type']
                new_type_sql = indbt__spark_type_to_sql_type(new_type)
                sql = f"ALTER TABLE {target_table} ALTER COLUMN `{column_name}` TYPE {new_type_sql}"
                spark.sql(sql)
    
    # Log message matching SQL format exactly
    schema_change_message = f\"\"\"
    In {target_table}:
        Schema change approach: {on_schema_change}
        Columns added: {add_to_target_arr}
        Columns removed: {schema_changes_dict.get('target_not_in_source', [])}
        Data types changed: {schema_changes_dict.get('new_target_types', [])}
    \"\"\"
    print(schema_change_message)


def indbt__process_schema_changes(on_schema_change: str, source_table: str, target_table: str) -> indbt__List[indbt__Dict[str, str]]:
    \"\"\"
    Process schema changes between source and target tables.
    
    Args:
        on_schema_change: The schema change strategy
        source_table: Name of the source table
        target_table: Name of the target table
        
    Returns:
        List of source column information
    \"\"\"
    if on_schema_change == 'ignore':
        return []
    
    schema_changes_dict = indbt__check_for_schema_changes(source_table, target_table)
    
    if schema_changes_dict['schema_changed']:
        if on_schema_change == 'fail':
            fail_msg = f\"\"\"
The source and target schemas on this incremental model are out of sync!
They can be reconciled in several ways:
  - set the `on_schema_change` config to either append_new_columns or sync_all_columns, depending on your situation.
  - Re-run the incremental model with `--full-refresh` to update the target schema.
  - update the schema manually and re-run the process.

Additional troubleshooting context:
   Source columns not in target: {[col['name'] for col in schema_changes_dict['source_not_in_target']]}
   Target columns not in source: {[col['name'] for col in schema_changes_dict['target_not_in_source']]}
   New column types: {[(ntt['column_name'], ntt['old_type'], ntt['new_type']) for ntt in schema_changes_dict['new_target_types']]}
            \"\"\"
            raise ValueError(fail_msg)
        else:
            indbt__sync_column_schemas(on_schema_change, target_table, schema_changes_dict)
    
    return schema_changes_dict['source_columns']


def indbt__table_exists(table_name):
    \"\"\"Check if table exists in Spark catalog.\"\"\"
    try:
        spark.table(table_name)
        return True
    except Exception:
        return False


def indbt__should_full_refresh(dbt_config):
    \"\"\"Check if full refresh should be performed, checking multiple sources.\"\"\"
    
    def _is_truthy(value):
        \"\"\"Check if a value represents True, handling strings and booleans.\"\"\"
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() == 'true'
        raise ValueError(f"Invalid value for full_refresh: {value}. Expected boolean or string 'true'/'false'.")
    
    # Check model config first
    full_refresh_config = dbt_config.get('full_refresh', False)
    if _is_truthy(full_refresh_config):
        return True
    
    # Check for global flags (various ways dbt might pass this)
    try:
        # Try to access global variables that dbt might set
        if 'indbt__full_refresh' in globals() and _is_truthy(indbt__full_refresh):
            return True
        if 'indbt__flags' in globals() and hasattr(indbt__flags, 'FULL_REFRESH') and _is_truthy(indbt__flags.FULL_REFRESH):
            return True
    except:
        pass
    
    return False


def indbt__orchestrate_materialization(table_name, temp_view, dbt_config):
    \"\"\"Main orchestration function for Python model materialization.\"\"\"
    exists = indbt__table_exists(table_name)
    materialized = dbt_config.get('materialized', 'table')
    is_incremental = (materialized.lower() == 'incremental')
    should_full_refresh = indbt__should_full_refresh(dbt_config)

    if not exists:
        # Relation must be created
        print(f"Creating new table: {table_name}")
        indbt__create_table_as(table_name, temp_view, dbt_config)
    elif should_full_refresh or not is_incremental:
        # Relation must be dropped & recreated (full_refresh overrides incremental)
        if should_full_refresh and is_incremental:
            print(f"Full refresh requested for incremental model: {table_name}")
        indbt__overwrite_table(table_name, temp_view)
    else:
        # Incremental merge logic
        indbt__handle_incremental(table_name, temp_view, dbt_config)


dbt = dbtObj(spark.table)
df = model(dbt, spark)

if df is not None:
    table_name = str(dbt.this)
    temp_view = f"temp_view_{table_name.replace('.', '_')}"
    df.createOrReplaceTempView(temp_view)

    indbt__orchestrate_materialization(table_name, temp_view, dbt.config)

"""
