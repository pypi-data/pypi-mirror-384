{% extends "table.sql" %}
{% macro spark__indbt_table_materialization() %}
  {%- set language = model['language'] -%}
  {%- set identifier = model['alias'] -%}
  {%- set grant_config = config.get('grants') -%}
  {%- set raw_retention = config.get('retention_period', none) -%}

  {%- set raw_file_format = config.get('file_format', default='openhouse') -%}
  {%- set file_format = dbt_spark_validate_openhouse_configs(raw_file_format) -%}
  {%- set retention = dbt_spark_validate_retention_configs(raw_retention,file_format) -%}

  {%- set catalog -%}
    {%- if not file_format == 'openhouse' -%}
      spark_catalog
    {%- else %}
      openhouse
    {%- endif -%}
  {%- endset -%}

  {%- set old_relation = adapter.get_relation(database=database, schema=schema, identifier=identifier) -%}
  {%- set target_relation = api.Relation.create(identifier=identifier,
                                                schema=schema,
                                                database=database,
                                                type='table') -%}

  {# -- TODO: DATAFND-1122 Hard coding the catalog as a workaround for APA-75325. Need to remove this once the spark v2 fix is deployed #}
  {% do adapter.dispatch('use_catalog', 'dbt')('spark_catalog') %}

  {{ run_hooks(pre_hooks) }}

  -- build model
  {% if language == 'python' %}
    {# For Python models, execute the code directly with the $$pyspark$$ marker #}

    {# Execute the Python code directly #}
    {%- call statement('main', language='python') -%}
{{ indbt_python_prelude() }}
{{ compiled_code }}
    {%- endcall -%}
  {% else %}
    {%- if old_relation -%}
      {%- set tmp_relation = make_temp_relation(this) -%}
      {%- set tmp_relation = tmp_relation.include(database=false, schema=false) -%}
      {%- call statement('create_tmp_relation', language=language) -%}
        {{ create_table_as(True, tmp_relation, compiled_code, language) }}
      {%- endcall -%}
      {% call statement('main') -%}
        insert overwrite {{ target_relation.render() }}
        select * from {{ tmp_relation.render() }}
      {%- endcall %}
    {%- else -%}
      {%- call statement('main', language=language) -%}
        {{ create_table_as(False, target_relation, compiled_code, language) }}
      {%- endcall -%}
    {%- endif -%}
  {%- endif -%}

  {% set should_revoke = should_revoke(old_relation, full_refresh_mode=True) %}
  {% do apply_grants(target_relation, grant_config, should_revoke) %}
  {% do apply_retention(target_relation, retention) %}
  {% do persist_docs(target_relation, model) %}
  {% set set_tbl_properties = adapter.dispatch('set_dbt_tblproperties', 'in_dbt_utils') %}
  {% do set_tbl_properties(target_relation, model) %}


  {% do persist_constraints(target_relation, model) %}

  {{ run_hooks(post_hooks) }}

  {{ return({'relations': [target_relation]})}}

{% endmacro %}
