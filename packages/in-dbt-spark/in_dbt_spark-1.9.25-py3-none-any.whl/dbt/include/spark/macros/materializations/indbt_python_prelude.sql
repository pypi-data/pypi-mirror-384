{#-- 
  Macro to generate the common inDBT Python prelude code
  This eliminates duplication between li_table.sql and li_incremental.sql
--#}

{% macro indbt_python_prelude() %}
$$pyspark$$
# <inDBT Pre-Inserted>
from datetime import datetime as indbt__datetime__mod
from datetime import timedelta as indbt__timedelta
from datetime import timezone as indbt__timezone
from pyspark.sql import SparkSession as indbt__SparkSession

# inDBT Date-Time Variables
# Logical date strings (from macro)
indbt__logical_date_us_pacific_str = '{{ in_dbt_utils.logical_date("US/Pacific") }}'
indbt__logical_date_utc_str = '{{ in_dbt_utils.logical_date("UTC") }}'

indbt__logical_date_mst_str = '{{ in_dbt_utils.logical_date("MST") }}'
indbt__logical_date_cst_str = '{{ in_dbt_utils.logical_date("US/Central") }}'
indbt__logical_date_est_str = '{{ in_dbt_utils.logical_date("US/Eastern") }}'

indbt__logical_date_europe_london_str = '{{ in_dbt_utils.logical_date("Europe/London") }}'
indbt__logical_date_cet_str = '{{ in_dbt_utils.logical_date("CET") }}'

indbt__logical_date_asia_kolkata_str = '{{ in_dbt_utils.logical_date("Asia/Kolkata") }}'
indbt__logical_date_asia_tokyo_str = '{{ in_dbt_utils.logical_date("Asia/Tokyo") }}'
indbt__logical_date_asia_shanghai_str = '{{ in_dbt_utils.logical_date("Asia/Shanghai") }}'
indbt__logical_date_australia_sydney_str = '{{ in_dbt_utils.logical_date("Australia/Sydney") }}'

# Logical date datetime objects
indbt__logical_date_us_pacific_obj = indbt__datetime__mod.fromisoformat(indbt__logical_date_us_pacific_str)
indbt__logical_date_utc_obj = indbt__datetime__mod.fromisoformat(indbt__logical_date_utc_str)

indbt__logical_date_mst_obj = indbt__datetime__mod.fromisoformat(indbt__logical_date_mst_str)
indbt__logical_date_cst_obj = indbt__datetime__mod.fromisoformat(indbt__logical_date_cst_str)
indbt__logical_date_est_obj = indbt__datetime__mod.fromisoformat(indbt__logical_date_est_str)

indbt__logical_date_europe_london_obj = indbt__datetime__mod.fromisoformat(indbt__logical_date_europe_london_str)
indbt__logical_date_cet_obj = indbt__datetime__mod.fromisoformat(indbt__logical_date_cet_str)

indbt__logical_date_asia_kolkata_obj = indbt__datetime__mod.fromisoformat(indbt__logical_date_asia_kolkata_str)
indbt__logical_date_asia_tokyo_obj = indbt__datetime__mod.fromisoformat(indbt__logical_date_asia_tokyo_str)
indbt__logical_date_asia_shanghai_obj = indbt__datetime__mod.fromisoformat(indbt__logical_date_asia_shanghai_str)
indbt__logical_date_australia_sydney_obj = indbt__datetime__mod.fromisoformat(indbt__logical_date_australia_sydney_str)

indbt__execution_date_str = '{{ in_dbt_utils.execution_date() }}'
indbt__execution_date_obj = indbt__datetime__mod.fromisoformat(indbt__execution_date_str)
indbt__is_backfill = '{{ in_dbt_utils.indbt__is_backfill()}}'

# inDBT Source Definitions
indbt__sources = [
  {%- for source_unique_id, source_node in graph.sources.items() -%}
    {
      "source_name": "{{ source_node.source_name }}",
      "table_name": "{{ source_node.name }}",
      "relation_name": "{{ source_node.relation_name }}",
      "meta": {{ source_node.meta | tojson }},
      "read_query_with_filter": "{{ in_dbt_utils.in_source_with_range_filter(source_node.source_name,source_node.name,for_inner=False) }}"
    }{%- if not loop.last -%},{%- endif -%}
  {%- endfor -%}
]

"""
Return the source dict whose source_name and table_name match the inputs.
Raises ValueError if no matching source is found.
"""
indbt__get_source = lambda source_name, table_name: (
    next(
        (s for s in indbt__sources
         if s['source_name'] == source_name and s['table_name'] == table_name),
        None
    )
    or (_ for _ in ()).throw(
        ValueError(f"Source: `{source_name}` Table: `{table_name}` not found")
    )
)

"""Load DataFrame: use filtered query if with_filter else raw table."""
indbt__get_source_dataframe = (
    lambda src, tbl, with_filter=True:
        spark.sql(indbt__get_source(src, tbl)["read_query_with_filter"])
        if with_filter
        else spark.table(indbt__get_source(src, tbl)["relation_name"])
)

# inDBT Logical Date Object (Primary)
indbt__logical_date_obj = indbt__logical_date_us_pacific_obj

# </inDBT Pre-Inserted>
{% endmacro %}
