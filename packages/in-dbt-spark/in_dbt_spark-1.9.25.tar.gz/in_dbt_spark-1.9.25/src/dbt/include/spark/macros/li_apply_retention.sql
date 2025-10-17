{% macro apply_retention(target_relation, retention) %}
  {{ return(adapter.dispatch('apply_retention', 'dbt')(target_relation, retention)) }}
{%- endmacro -%}

{% macro spark__apply_retention(relation, retention) %}
  {#
    Applies a retention policy to an Openhouse table in Spark.
    Supports retention on timestamp (table-level) and string/int (column-level) partitioned tables.
  #}
  {%- set file_format = config.get('file_format', 'openhouse') -%}
  {%- set raw_partition_by = config.get('partition_by', none) -%}
  {%- set partition_by_list = adapter.parse_partition_by(raw_partition_by) -%}
  {%- set ns = namespace(field=none, data_type=none, granularity=none) -%}
  {%- set identifier = relation.identifier -%}

  {% if file_format == 'openhouse' and partition_by_list is not none %}
    
    {#-- Pick the first valid partition (timestamp/string/int) --#}
    {% for partition_by in partition_by_list 
         if partition_by.data_type.lower() in ['timestamp', 'string', 'int'] and ns.field is none %}
      {% set ns.field = partition_by.field %}
      {% set ns.data_type = partition_by.data_type.lower() %}
      {% if ns.data_type == 'timestamp' %}
        {% set ns.granularity = partition_by.granularity %}
      {% endif %}
    {% endfor %}

    {% if ns.field is not none %}
      {% set retention_query %}
        
        {# === TIMESTAMP Partition === #}
        {% if ns.data_type == 'timestamp' %}
          {% if retention is not none %}
            alter table {{ relation }} set policy (RETENTION={{ retention }})
          {% else %}
            {% if ns.granularity is none %}
              {% do exceptions.raise_compiler_error(
                "Timestamp partition '" ~ ns.field ~ "' requires a granularity ('hours', 'days', 'months', 'years') to apply default retention policy."
              ) %}
            {% elif ns.granularity == 'hours' %}
              alter table {{ relation }} set policy (RETENTION=8760h)
            {% elif ns.granularity == 'days' %}
              alter table {{ relation }} set policy (RETENTION=365d)
            {% elif ns.granularity == 'months' %}
              alter table {{ relation }} set policy (RETENTION=12m)
            {% else %}
              {# Default fallback for unknown timestamp granularity #}
                {% do log(
                    "Unknown timestamp granularity '" ~ ns.granularity ~ 
                    "' for table: " ~ identifier ~ 
                    ". Using default retention of 1 year.", info=True
                ) %}
                {# Set default retention to 1 year #}
                {# This is a fallback and should be avoided with proper granularity #}  
              alter table {{ relation }} set policy (RETENTION=1y)
            {% endif %}
          {% endif %}

        {# === STRING / INT Partition === #}
        {% elif ns.data_type in ['string', 'int'] %}
          {% if retention is not none %}
            alter table {{ relation }} set policy (RETENTION={{ retention }} ON COLUMN {{ adapter.quote(ns.field) }})
          {% else %}
            {% set default_retention = "14d" %}
            {% do log(
              "No retention provided. Using default: " ~ default_retention ~ 
              " for table: " ~ identifier, info=True
            ) %}
            alter table {{ relation }} set policy (RETENTION={{ default_retention }} ON COLUMN {{ adapter.quote(ns.field) }})
          {% endif %}

        {# === Unexpected Type === #}
        {% else %}
          {% do exceptions.raise_compiler_error(
            "Unexpected partition data type '" ~ ns.data_type ~ 
            "' encountered for retention policy on column '" ~ ns.field ~ "'."
          ) %}
        {% endif %}

      {% endset %}

      {% do run_query(retention_query) %}
    {% endif %}
  {% endif %}
{% endmacro %}

