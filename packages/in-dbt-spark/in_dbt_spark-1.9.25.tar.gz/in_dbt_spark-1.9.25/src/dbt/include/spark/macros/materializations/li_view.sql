{% extends "view.sql" %}
{% macro spark__indbt_view_materialization() -%}
    {%- set file_format = config.get('file_format', default='openhouse') -%}

    {%- set identifier = model['alias'] -%}

    {%- set old_relation = adapter.get_relation(database=database, schema=schema, identifier=identifier) -%}
    {%- set exists_as_view = (old_relation is not none and old_relation.is_view) -%}

    {%- set target_relation = api.Relation.create(
        identifier=identifier, schema=schema, database=database,
        type='view') -%}
    {%- set target_relation_str = target_relation.render() -%}
    -- Remove openhouse. from target_relation if it starts with "openhouse."
    {%- if target_relation_str.startswith('openhouse.') -%}
        {%- set target_relation_str = target_relation_str.replace('openhouse.', '') -%}
    {%- endif -%}
    
    {% set grant_config = config.get('grants') %}

    {{ run_hooks(pre_hooks) }}

    -- TODO: Handle, If there's a table with the same name, we need to handle that

    -- build model
    {% call statement('main') -%}
        create view {{ target_relation_str }}
        as (
            {{ sql }}
        );
    {%- endcall %}

    {{ run_hooks(post_hooks) }}

    {{ return({'relations': [target_relation]}) }}
{%- endmacro %}