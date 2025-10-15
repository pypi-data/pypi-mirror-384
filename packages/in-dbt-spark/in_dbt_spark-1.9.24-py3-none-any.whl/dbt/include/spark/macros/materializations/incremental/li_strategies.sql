{% extends "strategies.sql" %}

{% macro indbt_get_insert_overwrite_sql(source_relation, target_relation, existing_relation) %}

    {%- set dest_columns = adapter.get_columns_in_relation(target_relation) -%}
    {%- set dest_cols_csv = dest_columns | map(attribute='quoted') | join(', ') -%}
    {% if existing_relation.is_iceberg or existing_relation.is_openhouse %}
      {# removed table from statement for iceberg #}
      insert overwrite {{ target_relation }}
      {# removed partition_cols for iceberg as well #}
    {% else %}
      insert overwrite table {{ target_relation }}
      {{ partition_cols(label="partition") }}
    {% endif %}
    select {{dest_cols_csv}} from {{ source_relation }}

{% endmacro %}

{% macro indbt_dbt_spark_get_incremental_sql(strategy, source, target, existing, unique_key, incremental_predicates) %}
    {%- if strategy == 'append' -%}
        {#-- insert new records into existing table, without updating or overwriting #}
        {{ get_insert_into_sql(source, target) }}
    {%- elif strategy == 'insert_overwrite' -%}
        {#-- insert statements don't like CTEs, so support them via a temp view #}
        {{ indbt_get_insert_overwrite_sql(source, target, existing) }}
    {%- elif strategy == 'merge' -%}
        {#-- merge all columns for datasources which implement MERGE INTO (e.g. databricks, iceberg, openhouse) - schema changes are handled for us #}
        {{ get_merge_sql(target, source, unique_key, dest_columns=none, incremental_predicates=incremental_predicates) }}
    {%- else -%}
        {% set no_sql_for_strategy_msg -%}
            No known SQL for the incremental strategy provided: {{ strategy }}
        {%- endset %}
        {%- do exceptions.raise_compiler_error(no_sql_for_strategy_msg) -%}
    {%- endif -%}

{% endmacro %}
