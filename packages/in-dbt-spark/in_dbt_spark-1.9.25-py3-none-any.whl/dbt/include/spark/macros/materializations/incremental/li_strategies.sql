{% extends "strategies.sql" %}

{% macro indbt_get_insert_overwrite_sql(source_relation, target_relation, existing_relation) %}
  {% do log("[DBT_MACRO] LI_INSERT_OVERWRITE_STRATEGY: source_relation = " ~ source_relation ~ ", target_relation = " ~ target_relation, info=True) %}

    {%- set dest_columns = adapter.get_columns_in_relation(target_relation) -%}
    {%- set dest_cols_csv = dest_columns | map(attribute='quoted') | join(', ') -%}
    
    {#-- Set WAP ID configuration before INSERT OVERWRITE --#}
    {{ set_wap_id_config() }}
    
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
    {%- do log("[DBT_MACRO]  INDBT_STRATEGIES: Executing strategy: " ~ strategy, info=true) -%}
    {%- do log("[DBT_MACRO]  INDBT_STRATEGIES: Source: " ~ source ~ ", Target: " ~ target, info=true) -%}
    {%- if strategy == 'append' -%}
        {%- do log("[DBT_MACRO] INDBT_STRATEGIES: Using append strategy", info=true) -%}
        {#-- insert new records into existing table, without updating or overwriting #}
        {{ get_insert_into_sql(source, target) }}
    {%- elif strategy == 'insert_overwrite' -%}
        {%- do log("[DBT_MACRO] INDBT_STRATEGIES: Using insert_overwrite strategy", info=true) -%}
        {#-- insert statements don't like CTEs, so support them via a temp view #}
        {{ indbt_get_insert_overwrite_sql(source, target, existing) }}
    {%- elif strategy == 'merge' -%}
        {%- do log("[DBT_MACRO] INDBT_STRATEGIES: Using merge strategy", info=true) -%}
        {#-- merge all columns for datasources which implement MERGE INTO (e.g. databricks, iceberg, openhouse) - schema changes are handled for us #}
        {{ get_merge_sql(target, source, unique_key, dest_columns=none, incremental_predicates=incremental_predicates) }}
    {%- else -%}
        {% set no_sql_for_strategy_msg -%}
            No known SQL for the incremental strategy provided: {{ strategy }}
        {%- endset %}
        {%- do exceptions.raise_compiler_error(no_sql_for_strategy_msg) -%}
    {%- endif -%}

{% endmacro %}
