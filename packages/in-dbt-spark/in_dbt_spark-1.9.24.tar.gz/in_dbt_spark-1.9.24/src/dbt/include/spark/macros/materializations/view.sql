{% materialization view, adapter='spark' -%}
    {% do log("Checking for custom Spark view materialization!", info=True) %}
    {%- set file_format = config.get('file_format', 'openhouse') -%}
    {% if file_format == 'openhouse' %}
        {{ return(adapter.dispatch('indbt_view_materialization')()) }}
    {% endif %}
    {{ return(create_or_replace_view()) }}
{%- endmaterialization %}
