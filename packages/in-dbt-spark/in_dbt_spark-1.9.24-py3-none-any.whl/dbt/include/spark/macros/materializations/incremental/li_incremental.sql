{% extends "incremental.sql" %}
{% macro spark__indbt_incremental_materialization() -%}
  {#-- Validate early so we don't run SQL if the file_format + strategy combo is invalid --#}
  {%- set raw_file_format = config.get('file_format', default='openhouse') -%}
  {%- set raw_strategy = config.get('incremental_strategy') or 'append' -%}
  {%- set grant_config = config.get('grants') -%}
  {%- set raw_retention = config.get('retention_period', none) -%}

  {%- set file_format =indbt_dbt_spark_validate_get_file_format(raw_file_format) -%}
  {%- set file_format = dbt_spark_validate_openhouse_configs(file_format) -%}
  {%- set strategy = indbt_dbt_spark_validate_get_incremental_strategy(raw_strategy, file_format) -%}
  {%- set retention = dbt_spark_validate_retention_configs(raw_retention,file_format) -%}

  {%- set catalog -%}
    {%- if not file_format == 'openhouse' -%}
      spark_catalog
    {%- else %}
      openhouse
    {%- endif -%}
  {%- endset -%}

  {#-- Set vars --#}
  {%- set unique_key = config.get('unique_key', none) -%}
  {%- set partition_by = config.get('partition_by', none) -%}
  {%- set language = model['language'] -%}
  {%- set on_schema_change = incremental_validate_on_schema_change(config.get('on_schema_change'), default='ignore') -%}
  {%- set incremental_predicates = config.get('predicates', none) or config.get('incremental_predicates', none) -%}
  {%- set target_relation = this -%}
  {%- set existing_relation = load_relation(this) -%}
  {#-- Only create temp relation for SQL models --#}
  {%- if language == 'sql'-%}
    {%- set tmp_relation = make_temp_relation(this) -%}
    {%- set tmp_relation = tmp_relation.include(database=false, schema=false) -%}
  {%- endif -%}

  {#-- Set Overwrite Mode --#}
  {%- if strategy == 'insert_overwrite' and partition_by -%}
    {%- call statement() -%}
      set spark.sql.sources.partitionOverwriteMode = DYNAMIC
    {%- endcall -%}
  {%- endif -%}

  {# -- TODO: DATAFND-1122 Hard coding the catalog as a workaround for APA-75325. Need to remove this once the spark v2 fix is deployed #}
  {% do adapter.dispatch('use_catalog', 'dbt')('spark_catalog') %}

  {#-- Run pre-hooks --#}
  {{ run_hooks(pre_hooks) }}

  {#-- For Python models, just pass through the compiled code with pyspark marker --#}
  {%- if language == 'python' -%}
    {%- call statement('main', language='python') -%}
{{ indbt_python_prelude() }}
{{ compiled_code }}
    {%- endcall -%}
  {%- else -%}
    {#-- SQL models: Use existing incremental logic --#}
    {#-- Incremental run logic --#}
    {%- if existing_relation is none -%}
      {#-- Relation must be created --#}
      {%- call statement('main', language=language) -%}
        {{ create_table_as(False, target_relation, compiled_code, language) }}
      {%- endcall -%}
      {% do persist_constraints(target_relation, model) %}
    {%- elif existing_relation.is_view or should_full_refresh() -%}
      {#-- Relation must be dropped & recreated --#}
      {% set is_delta = (file_format == 'delta' and existing_relation.is_delta) %}
      {% if not is_delta %} {#-- If Delta, we will `create or replace` below, so no need to drop --#}
        {% do adapter.drop_relation(existing_relation) %}
      {% endif %}
      {%- call statement('main', language=language) -%}
        {{ create_table_as(False, target_relation, compiled_code, language) }}
      {%- endcall -%}
      {% do persist_constraints(target_relation, model) %}
    {%- else -%}
      {#-- Relation must be merged --#}
      {%- call statement('create_tmp_relation', language=language) -%}
        {{ create_table_as(True, tmp_relation, compiled_code, language) }}
      {%- endcall -%}
      {%- do process_schema_changes(on_schema_change, tmp_relation, existing_relation) -%}
      {%- call statement('main') -%}
        {{ indbt_dbt_spark_get_incremental_sql(strategy, tmp_relation, target_relation, existing_relation, unique_key, incremental_predicates) }}
      {%- endcall -%}
    {%- endif -%}
  {%- endif -%}

  {% set should_revoke = should_revoke(existing_relation, full_refresh_mode) %}
  {% do apply_grants(target_relation, grant_config, should_revoke) %}
  {% do apply_retention(target_relation, retention) %}
  {% do persist_docs(target_relation, model) %}
  {% set set_tbl_properties = adapter.dispatch('set_dbt_tblproperties', 'in_dbt_utils') %}
  {% do set_tbl_properties(target_relation, model) %}

  {{ run_hooks(post_hooks) }}

  {{ return({'relations': [target_relation]}) }}

  {%- endmacro %}