{% extends "validate.sql" %}

{% macro indbt_dbt_spark_validate_get_file_format(raw_file_format) %}
  {#-- Validate the file format #}

  {% set accepted_formats = [
    'text', 'csv', 'json', 'jdbc', 'parquet', 'orc', 'hive',
    'delta', 'iceberg', 'libsvm', 'hudi', 'openhouse'
  ] %}

  {% set invalid_file_format_msg -%}
    Invalid file format provided: {{ raw_file_format }}
    Expected one of: {{ accepted_formats | join(', ') }}
  {%- endset %}

  {% if raw_file_format not in accepted_formats %}
    {% do exceptions.raise_compiler_error(invalid_file_format_msg) %}
  {% endif %}

  {% do return(raw_file_format) %}
{% endmacro %}

{% macro indbt_dbt_spark_validate_get_incremental_strategy(raw_strategy, file_format) %}
  {#-- Validate the incremental strategy #}

  {% set invalid_strategy_msg -%}
    Invalid incremental strategy provided: {{ raw_strategy }}
    Expected one of: 'append', 'merge', 'insert_overwrite'
  {%- endset %}

  {% set invalid_merge_msg -%}
    Invalid incremental strategy provided: {{ raw_strategy }}
    You can only choose this strategy when file_format is set to 'delta', 'iceberg', 'hudi', or 'openhouse'
  {%- endset %}

  {% set invalid_insert_overwrite_delta_msg -%}
    Invalid incremental strategy provided: {{ raw_strategy }}
    You cannot use this strategy when file_format is set to 'delta', 'iceberg', or 'openhouse'
    Use the 'append' or 'merge' strategy instead
  {%- endset %}

  {% set invalid_insert_overwrite_endpoint_msg -%}
    Invalid incremental strategy provided: {{ raw_strategy }}
    You cannot use this strategy when connecting via endpoint
    Use the 'append' or 'merge' strategy instead
  {%- endset %}

  {% if raw_strategy not in ['append', 'merge', 'insert_overwrite'] %}
    {% do exceptions.raise_compiler_error(invalid_strategy_msg) %}
  {%- else %}
    {% if raw_strategy == 'merge' and file_format not in ['delta', 'iceberg', 'hudi', 'openhouse'] %}
      {% do exceptions.raise_compiler_error(invalid_merge_msg) %}
    {% endif %}
    {% if raw_strategy == 'insert_overwrite' and file_format == 'delta' %}
      {% do exceptions.raise_compiler_error(invalid_insert_overwrite_delta_msg) %}
    {% endif %}
    {% if raw_strategy == 'insert_overwrite' and target.endpoint %}
      {% do exceptions.raise_compiler_error(invalid_insert_overwrite_endpoint_msg) %}
    {% endif %}
  {% endif %}

  {% do return(raw_strategy) %}
{% endmacro %}

-- Linkedin Internal macros

{% macro dbt_spark_validate_retention_configs(raw_retention, file_format) %}
  {#-- Validate the retention period config --#}

  {% if raw_retention is not none %}
    {% if file_format != 'openhouse' %}
      {% do exceptions.raise_compiler_error(
           "Invalid configs for 'retention_period'. "
           ~ "Retention config is not supported for this file_format: " ~ file_format
         ) %}
    {% endif %}
  {% endif %}

  {% do return(raw_retention) %}
{% endmacro %}


{% macro dbt_spark_validate_openhouse_configs(file_format) %}
  {#-- Validate against configs that OpenHouse does not support ahead of time --#}

  {% if file_format == 'openhouse' %}

    {#-- Disallowed configs --#}
    {% if config.get('clustered_by', none) is not none %}
      {% do exceptions.raise_compiler_error("'clustered_by' is not supported for 'openhouse' file_format") %}
    {% endif %}

    {% if config.get('location_root', none) is not none %}
      {% do exceptions.raise_compiler_error("'location_root' is not supported for 'openhouse' file_format") %}
    {% endif %}

    {#-- Partition-by validation --#}
    {% set raw_pb = config.get('partition_by', none) %}
    {% set partition_by_list = [] %}
    {% set valid_retention_partition_found = namespace(value=false) %} {# Flag to check for suitable retention partition #}
    {% set timestamp_columns = namespace(count=0) %}

    {% if raw_pb is not none %}
      {# Attempt to parse partition_by, raise error if format is invalid (handled by adapter.parse_partition_by) #}
      {% set partition_by_list = adapter.parse_partition_by(raw_pb) %}

      {% if partition_by_list | length > 4 %}
        {% do exceptions.raise_compiler_error(
             "For partitioned tables with file_format = 'openhouse', "
             ~ "the size of 'partition_by' must not be > 4."
           ) %}
      {% endif %}

      {%- for part in partition_by_list -%}
        {%- set dt = part.data_type.lower() -%}
        {#-- Data type check --#}
        {% if dt not in ['timestamp', 'string', 'int'] %}
          {% do exceptions.raise_compiler_error(
               "For partitioned tables with file_format = 'openhouse', "
               ~ "'data_type' must be one of ('timestamp', 'string', 'int')."
             ) %}
        {% endif %}

        {#-- Mark partition types valid for retention --#}
        {% if dt in ['timestamp', 'string', 'int'] %}
          {% set valid_retention_partition_found.value = true %}
        {% endif %}

        {#-- Timestamp-specific rules --#}
        {% if dt == 'timestamp' %}
          {% set timestamp_columns.count = timestamp_columns.count + 1 %}
          {% if timestamp_columns.count > 1 %}
            {% do exceptions.raise_compiler_error(
                 "For timestamp-partitioned tables with file_format = 'openhouse',\n"
                 ~ "   OpenHouse only supports 1 timestamp-based column partitioning"
               ) %}
          {% endif %}

          {% if part.granularity is none %}
            {% do exceptions.raise_compiler_error(
                 "For timestamp-partitioned tables with file_format = 'openhouse' "
                 ~ "and data_type = 'timestamp', granularity must be provided."
               ) %}
          {% endif %}

          {#-- MODIFIED: Use plural forms for valid_gran list --#}
          {% set valid_gran = [
               'hours','days','months','years'
             ] %}
          {% if part.granularity not in valid_gran %}
            {% do exceptions.raise_compiler_error(
                 "For timestamp-partitioned tables with file_format = 'openhouse', "
                 ~ "'granularity' must be one of ('hours', 'days', 'months', or 'years')."
               ) %}
          {% endif %}
        {% endif %}
      {%- endfor %}
    {% endif %}

    {#-- Grants validation --#}
    {% set grant_cfg = config.get('grants', none) %}
    {% if grant_cfg is not none %}
      {% for priv in grant_cfg.keys() %}
        {% if priv.lower() not in ['select', 'manage grants'] %}
          {% do exceptions.raise_compiler_error(
               "For outputs with file_format = 'openhouse', "
               ~ "keys in 'grants' map must be one of ('select', 'manage grants')."
             ) %}
        {% endif %}
      {% endfor %}
    {% endif %}

    {#-- Retention validation --#}
    {% set raw_ret = config.get('retention_period', none) %}
    {% set materialization = config.get('materialized', 'table') %}
    {% if materialization == 'incremental' %}
      {% if raw_ret is not none %}
        {% if raw_pb is none %}
          {% do exceptions.raise_compiler_error(
              "For tables with file_format = 'openhouse' and 'retention_period', "
              ~ "'partition_by' must be supplied."
            ) %}
        {% endif %}

        {#-- Check if any of the partitions were suitable for retention (timestamp, string, or int) --#}
        {% if not valid_retention_partition_found.value %}
          {% do exceptions.raise_compiler_error(
              "For tables with file_format = 'openhouse' and 'retention_period', "
              ~ "'partition_by' must include at least one column partition "
              ~ "with data_type: 'timestamp', 'string', or 'int'."
            ) %}
        {% endif %}

        {#-- (Optional) redundant timestamp-only check removed --#}
      {% endif %}
    {% endif %}

  {% endif %}

  {% do return(file_format) %}
{% endmacro %}