{% extends "snapshot.sql" %}
{% macro spark__indbt_snapshot_materialization() %}
     {%- set config = model['config'] -%}

     {%- set target_table = model.get('alias', model.get('name')) -%}

     {%- set strategy_name = config.get('strategy') -%}
     {%- set unique_key = config.get('unique_key') %}
     {%- set file_format = config.get('file_format', 'openhouse') -%}
     {%- set grant_config = config.get('grants') -%}

     {% set target_relation_exists, target_relation = get_or_create_relation(
         database=model.database,
         schema=model.schema,
         identifier=target_table,
         type='table') -%}

     {%- if file_format not in ['delta', 'iceberg', 'hudi', 'openhouse'] -%}
         {% set invalid_format_msg -%}
         Invalid file format: {{ file_format }}
         Snapshot functionality requires file_format be set to 'delta' or 'iceberg' or 'hudi' or 'openhouse'
         {%- endset %}
         {% do exceptions.raise_compiler_error(invalid_format_msg) %}
     {% endif %}

     {%- if target_relation_exists -%}
        {%- if not target_relation.is_delta and not target_relation.is_iceberg and not target_relation.is_hudi and not target_relation.is_openhouse -%}
            {% set invalid_format_msg -%}
                 The existing table {{ model.schema }}.{{ target_table }} is in another format than 'delta' or 'iceberg' or 'hudi' or 'openhouse'
            {%- endset %}
            {% do exceptions.raise_compiler_error(invalid_format_msg) %}
        {% endif %}
     {% endif %}

     {% if not adapter.check_schema_exists(model.database, model.schema) %}
        {% do exceptions.raise_compiler_error("Self-serve schema creation is not currently supported in OpenHouse. Please reach out in #ask_openhouse to manually provision your database.") %}
     {% endif %}

     {%- if not target_relation.is_table -%}
        {% do exceptions.relation_wrong_type(target_relation, 'table') %}
     {%- endif -%}

     {# -- TODO: DATAFND-1122 Hard coding the catalog as a workaround for APA-75325. Need to remove this once the spark v2 fix is deployed #}
     {% do adapter.dispatch('use_catalog', 'dbt')('spark_catalog') %}

     {{ run_hooks(pre_hooks, inside_transaction=False) }}

     {{ run_hooks(pre_hooks, inside_transaction=True) }}

     {% set strategy_macro = strategy_dispatch(strategy_name) %}
     {% set strategy = strategy_macro(model, "snapshotted_data", "source_data", config, target_relation_exists) %}

     {% if not target_relation_exists %}

         {% set build_sql = build_snapshot_table(strategy, model['compiled_code']) %}
         {% set final_sql = create_table_as(False, target_relation, build_sql) %}

     {% else %}

         {{ adapter.valid_snapshot_target(target_relation) }}

                -- create temp delta table (table_name__dbt_tmp) with changetype as update/insert/delete
         {% set staging_table = spark_build_snapshot_staging_table(strategy, sql, target_relation, file_format) %}

                    -- this may no-op if the database does not require column expansion
             {% do adapter.expand_target_column_types(from_relation=staging_table,
             to_relation=target_relation) %}

         {% set missing_columns = adapter.get_missing_columns(staging_table, target_relation)
         | rejectattr('name', 'equalto', 'dbt_change_type')
         | rejectattr('name', 'equalto', 'DBT_CHANGE_TYPE')
         | rejectattr('name', 'equalto', 'dbt_unique_key')
         | rejectattr('name', 'equalto', 'DBT_UNIQUE_KEY')
         | list %}

         {% do create_columns(target_relation, missing_columns) %}

         {% set staging_columns = adapter.get_columns_in_relation(staging_table)
         | rejectattr('name', 'equalto', 'dbt_change_type')
         | rejectattr('name', 'equalto', 'DBT_CHANGE_TYPE')
         | rejectattr('name', 'equalto', 'dbt_unique_key')
         | rejectattr('name', 'equalto', 'DBT_UNIQUE_KEY')
         | list %}

                -- only some file_formats support merge_into, others use full outer join to merge snapshot and source table
                -- TODO DATAFND-1019: use MERGE INTO for OpenHouse when `merge into` starts using column id ordering rather than ordinal
         {% if file_format in ['delta', 'iceberg', 'hudi'] %}
             {% set quoted_source_columns = [] %}
             {% for column in staging_columns %}
             {% do quoted_source_columns.append(adapter.quote(column.name)) %}
             {% endfor %}

             {% set final_sql = snapshot_merge_sql(
                 target = target_relation,
                 source = staging_table,
                 insert_cols = quoted_source_columns)
             %}
        {% else %}
             {% set source_columns_updated = staging_columns
             | rejectattr('name', 'equalto', 'dbt_updated_at')
             | rejectattr('name', 'equalto', 'dbt_valid_from')
             | rejectattr('name', 'equalto', 'dbt_valid_to')
             | rejectattr('name', 'equalto', 'dbt_scd_id')
             | list %}

                    -- merge old snapshot and table (table_name__dbt_tmp) to create  another temp table (table_name__dbt_merge)
             {% set merge_table = merge_sql_hive(
             target = target_relation,
             source = staging_table,
             insert_cols = source_columns_updated)
             %}
                    -- overwrite snapshot table with merge table creates above (table_name__dbt_merge)
             {% set final_sql = insert_overwrite(
             target = target_relation,
             source = merge_table)
             %}
        {% endif %}
     {% endif %}

     {% call statement('main') %}
     {{ final_sql }}
     {% endcall %}

     {% set should_revoke = should_revoke(target_relation_exists, full_refresh_mode) %}
     {% do apply_grants(target_relation, grant_config, should_revoke) %}

     {% do persist_docs(target_relation, model) %}
     {% set set_tbl_properties = adapter.dispatch('set_dbt_tblproperties', 'in_dbt_utils') %}
     {% do set_tbl_properties(target_relation, model) %}


     {{ run_hooks(post_hooks, inside_transaction=True) }}

     {{ adapter.commit() }}

     {% if staging_table is defined %}
        {% do post_snapshot(staging_table) %}
     {% endif %}
     {% if merge_table is defined %}
        {% do post_snapshot(merge_table) %}
     {% endif %}

     {{ run_hooks(post_hooks, inside_transaction=False) }}

     {{ return({'relations': [target_relation]}) }}

{% endmacro %}
