{% extends "python.sql" %}

{% macro indbt__py_script_postfix(model) %}
# This part is user provided model code
# you will need to copy the next section to run the code
# COMMAND ----------
# this part is dbt logic for get ref work, do not modify

{{ build_ref_function(model ) }}
{{ build_source_function(model ) }}
{{ build_config_dict(model) }}

class config:
    def __init__(self, *args, **kwargs):
        global config_dict
        config_dict.update(kwargs)

    def get(self, key, default=None):
        return config_dict.get(key, default)

    def __contains__(self, key):
        return key in config_dict

    def __call__(self, *args, **kwargs):
        global config_dict
        config_dict.update(kwargs)


class this:
    """dbt.this() or dbt.this.identifier"""
    database = "{{ this.database }}"
    schema = "{{ this.schema }}"
    identifier = "{{ this.identifier }}"
    {% set this_relation_name = resolve_model_name(this) %}
    def __repr__(self):
        return '{{ this_relation_name  }}'


class dbtObj:
    def __init__(self, load_df_function) -> None:
        self.source = lambda *args: source(*args, dbt_load_df_function=load_df_function)
        self.ref = lambda *args, **kwargs: ref(*args, **kwargs, dbt_load_df_function=load_df_function)
        self.config = config()
        self.this = this()
        self.is_incremental = {{ is_incremental() }}

# COMMAND ----------
{{py_script_comment()}}
{% endmacro %}
